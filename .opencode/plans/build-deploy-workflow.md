# Plan : Workflow CI/CD Build & Deploy automatisé

## Résumé du comportement

| Événement | Build | Push tag | Tofu apply |
|-----------|-------|----------|------------|
| **PR** (ouverte/synchronisée) | ✅ Build validation only | ❌ Non | ❌ Non |
| **Push** merge integration | ✅ Build | `:dev` | ✅ Dev |
| **Push** merge main | ✅ Build | `:prod` + version + `:latest` si release | ✅ Prod |
| **workflow_dispatch** (manuel) | ❌ (retag existant) | Retag `:dev` → `:prod` | ✅ Prod |

## Modifications Terraform

### 1. `00_infra/opentofu/environments/dev/main.tf`

4 occurrences (lignes 256, 280, 303, 405) :
```hcl
# AVANT
image = "${module.artifact_registry.repository_url}/extract-ft:latest"

# APRÈS
image = "${module.artifact_registry.repository_url}/extract-ft:${var.environment}"
```

### 2. `00_infra/opentofu/environments/prod/main.tf`

2 occurrences (lignes 70, 94) — idem, remplacer `:latest` par `:${var.environment}`

## Workflow fusionné : `.github/workflows/release.yml`

### Trigger
```yaml
on:
  pull_request:
    branches: [main, integration]
    paths-ignore: ["_*/**", "**/_*/**"]
  push:
    branches: [main, integration]
    paths-ignore: ["_*/**", "**/_*/**"]
  workflow_dispatch:
```

### Jobs

#### job: `filter` (tous events)
- `dorny/paths-filter` → outputs: `shared`, `ft`, `geo`, `adzuna`, `dbt`

#### job: `release` (push only — toujours tourne pour éviter skip)
```yaml
if: github.event_name == 'push'
```
- L'étape semantic-release a `if: github.ref_name == 'main'` — skip sur integration
- outputs: `released`, `version` (vides si skip sur integration)

#### job: `build-check` (PR only)
```yaml
if: github.event_name == 'pull_request'
needs: filter
strategy:
  matrix:
    include:
      - name: extract-ft, filter_key: ft, dockerfile: ...
      - name: extract-geo, filter_key: geo, dockerfile: ...
      - name: extract-adzuna, filter_key: adzuna, dockerfile: ...
      - name: dbt_transform, filter_key: dbt, dockerfile: ...
```
- Chaque job ne tourne que si le path filter correspond OU si `shared == 'true'`
- `docker build` uniquement (pas de push, pas de `docker/setup-buildx-action` requis — simple `docker build` pour valider)

#### job: `build-and-push` (push only)
```yaml
if: github.event_name == 'push'
needs: [filter, release]
# release ne bloque pas: le job tourne sur tout push, seule l'étape semantic-release skip sur integration
```
- Matrix identique à build-check
- Auth GCP + Docker
- `docker/build-push-action` avec tags :
  - Toujours : `:dev` (si branche integration) ou `:prod` (si branche main)
  - Si semantic release a fired (`needs.release.outputs.released == 'true'`) : aussi `:vX.Y.Z` et `:latest`
- Condition de build par image : `needs.filter.outputs.shared == 'true' || needs.filter.outputs.<key> == 'true'`

#### job: `deploy` (push only)
```yaml
if: github.event_name == 'push'
needs: build-and-push
```
- `tofu init` + `tofu apply` dans `00_infra/opentofu/environments/${{ github.ref_name == 'main' && 'prod' || 'dev' }}`
- Auth GCP via WIF

#### job: `promote` (workflow_dispatch only)
```yaml
if: github.event_name == 'workflow_dispatch'
```
- `gcloud container images add-tag` pour chaque image : `:dev` → `:prod`

#### job: `deploy-prod-after-promote` (workflow_dispatch only)
```yaml
needs: promote
```
- `tofu apply` pour environement prod

## Ce qui reste inchangé
- `ci.yml` (ruff, pytest, dbt parse, sqlfluff) — continue sur PR
- `dbt-ci.yml` (dbt compile + run + test BQ) — continue sur PR
- `AGENTS.md` — non modifié

## Points d'attention
1. **needs: [filter, release]** sur build-and-push — `release` tourne sur tout push (pas de skip), l'étape semantic-release est skip sur integration via `if: github.ref_name == 'main'`
2. **Condition de build par image** : `shared == 'true' || ft == 'true'` car shared est une dépendance commune
3. **Auth GCP** : utiliser WIF (déjà configuré dans les vars GitHub)
4. **`github.ref_name`** pour déterminer environnement (main → prod, integration → dev)
5. **Tag image** : `${var.environment}` dans terraform → `:dev` ou `:prod` automatiquement
