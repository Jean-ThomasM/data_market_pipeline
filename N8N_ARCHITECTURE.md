# Architecture n8n — Data Market Pipeline

## 1. Vue d'ensemble

n8n est déployé comme **Cloud Run service** dans GCP (projet `data-market-386959`, région `europe-west1`). Il sert de **proxy HTTP** pour le scraping de societe.com : il récupère le HTML des pages société et le transmet à un job Python (`n8n_trigger`) qui parse les données.

### Architecture

```
BigQuery (int_adzuna_offres + staging_api_entreprise)
  │  n8n_trigger (Cloud Run Job) interroge les offres non traitées
  ▼
n8n_trigger/main.py
  │  Si N8N_WEBHOOK_URL défini → appelle via N8nClient
  │  Si N8N_WEBHOOK_URL absent ou erreur → fallback HTTP direct
  │
  ├─(priorité)──> n8n (Cloud Run service) ──> societe.com
  │                    webhook GET HTML
  │                    /webhook/societe-scraper
  │
  └─(fallback)──> scraper.scrape_societe() (direct HTTP)
  │
  ▼
scraper.parse_societe_html(html, siren)
  │  Extrait JSON-LD + dt/dd + ADSTACK.data
  ▼
save_ndjson_records()
  │  GCS : raw/n8n_societe/{timestamp}.ndjson
  ▼
insert_rows(staging_societe_tracking)
  │  BQ : marque les offres comme traitées
  ▼
[Via le pipeline global Workflows]
load-staging-n8n-societe (Workflow)
  │  Charge NDJSON → staging_n8n_societe
  │  Déplace fichiers traités → raw/n8n_societe/done/
```

---

## 2. Ressources GCP provisionnées

### 2.1 Service Account

| Ressource | Valeur |
|-----------|--------|
| **Nom** | `n8n-runner-dev` |
| **Display name** | `n8n Runner dev` |
| **Provisionné par** | `module.n8n_service_account` |

Le service account `pipeline-runner-dev` exécute le `n8n_trigger` Cloud Run Job.

### 2.2 Cloud Run Service (n8n)

| Attribut | Valeur |
|----------|--------|
| **Nom** | `n8n-dev` |
| **Image** | `europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/n8n:latest` |
| **Service account** | `n8n-runner-dev` |
| **Port** | `5678` |
| **CPU** | `1` |
| **Memory** | `2Gi` |
| **Scaling** | `MANUAL` — 1 instance (toujours actif) |
| **URL** | Variable (déterminée par Cloud Run) — actuellement `https://n8n-dev-822083335202.europe-west1.run.app` |
| **Provisionné par** | `module.n8n_service` |

### 2.3 Cloud Run Job (n8n_trigger)

| Attribut | Valeur |
|----------|--------|
| **Nom** | `n8n-trigger-dev` |
| **Image** | `.../n8n-trigger:latest` |
| **Service account** | `pipeline-runner-dev` |
| **Provisionné par** | `module.n8n_trigger_job` |

### 2.4 Secret Manager

| Secret | ID | Utilisé par |
|--------|----|-------------|
| **n8n encryption key** | `n8n-encryption-key-dev` | n8n service (via `secret_env_vars`) |

### 2.5 BigQuery

| Table | Dataset | Description |
|-------|---------|-------------|
| `staging_n8n_societe` | `staging_dev` | Données scrapées (33 colonnes) |
| `staging_societe_tracking` | `staging_dev` | Traçage des offres traitées (3 colonnes) |

#### Schéma `staging_n8n_societe`

| Colonne | Type | Mode |
|---------|------|------|
| `employer_name` | STRING | NULLABLE |
| `nom_commune` | STRING | NULLABLE |
| `siren` | STRING | NULLABLE |
| `scraped_at` | TIMESTAMP | NULLABLE |
| `siret_siege` | STRING | NULLABLE |
| `tva_intra` | STRING | NULLABLE |
| `legal_name` | STRING | NULLABLE |
| `naf_code` | STRING | NULLABLE |
| `naf_label` | STRING | NULLABLE |
| `date_creation` | STRING | NULLABLE |
| `adresse_rue` | STRING | NULLABLE |
| `adresse_complement` | STRING | NULLABLE |
| `adresse_code_postal` | STRING | NULLABLE |
| `adresse_ville` | STRING | NULLABLE |
| `forme_juridique_code` | STRING | NULLABLE |
| `statut` | STRING | NULLABLE |
| `dirigeants` | RECORD (REPEATED) | — |
| ├─ `nom` | STRING | NULLABLE |
| ├─ `prenom` | STRING | NULLABLE |
| ├─ `nom_famille` | STRING | NULLABLE |
| ├─ `fonction` | STRING | NULLABLE |
| └─ `siren` | STRING | NULLABLE |
| `capital_social` | STRING | NULLABLE |
| `convention_collective` | STRING | NULLABLE |
| `noms_commerciaux` | STRING | NULLABLE |
| `statut_rcs` | STRING | NULLABLE |
| `statut_insee` | STRING | NULLABLE |
| `statut_rne` | STRING | NULLABLE |
| `chiffre_affaires` | STRING | NULLABLE |
| `effectif` | STRING | NULLABLE |

#### Schéma `staging_societe_tracking`

| Colonne | Type | Mode |
|---------|------|------|
| `employer_name` | STRING | REQUIRED |
| `nom_commune` | STRING | NULLABLE |
| `processed_at` | TIMESTAMP | REQUIRED |

### 2.6 Cloud Workflows

| Nom | Description |
|-----|-------------|
| `load-staging-n8n-societe-dev` | Charge les fichiers NDJSON de `raw/n8n_societe/*.ndjson` vers `staging_n8n_societe`, puis déplace les fichiers dans `done/` |
| `pipeline-global-dev` | Orchestre tout le pipeline : les étapes n8n sont exécutées APRÈS dbt (run_n8n_extract → run_n8n_load) |

### 2.7 Monitoring

#### Uptime check
- **Nom** : `n8n Health Check dev`
- **Chemin** : `/health`
- **Fréquence** : toutes les 60s
- **Timeout** : 10s
- **SSL** : activé

#### Log metric
- **Nom** : `n8n_errors_dev`
- **Filtre** : `resource.type = "cloud_run_revision" resource.labels.service_name = "n8n-dev" severity = ERROR`

#### Alert policy
- **Nom** : `Erreurs n8n - dev`
- **Condition** : `n8n_errors > 0` sur une fenêtre de 300s
- **Notification** : email (configuré dans `var.monitoring_email`)
- **Délai post-création** : 30s (time_sleep pour propagation des métriques)

#### Dashboard
- **Widget** : `Statut n8n` — affiche la disponibilité via `uptime_check/health_passed`
- **Aggregation** : moyenne sur 3600s

---

## 3. Permissions IAM

### 3.1 n8n service account (`n8n-runner-dev`)

| Ressource | Rôle | Cible |
|-----------|------|-------|
| `n8n_encryption_key_accessor` | `roles/secretmanager.secretAccessor` | Secret `n8n-encryption-key-dev` |
| `n8n_data_lake_viewer` | `roles/storage.objectViewer` | Bucket `data-market-386959-data-lake-dev` |
| `n8n_staging_data_editor` | `roles/bigquery.dataEditor` | Dataset `staging_dev` |
| `n8n_bigquery_job_user` | `roles/bigquery.jobUser` | Project level |
| `n8n_secret_accessor` | `roles/secretmanager.secretAccessor` | Project level |

### 3.2 Pipeline service account (`pipeline-runner-dev`)

Ce SA exécute le Cloud Run Job `n8n-trigger-dev`. Les permissions viennent de 3 sources :

#### Via `module.pipeline_iam`

| Ressource | Rôle | Cible |
|-----------|------|-------|
| `pipeline_storage_object_admin` | `roles/storage.objectAdmin` | Bucket `data-market-386959-data-lake-dev` |
| `pipeline_bigquery_data_editor` | `roles/bigquery.dataEditor` | Project level |
| `pipeline_bigquery_job_user` | `roles/bigquery.jobUser` | Project level |
| `pipeline_secret_accessor` | `roles/secretmanager.secretAccessor` | Project level |
| `pipeline_run_jobs_executor` | `roles/run.jobsExecutor` | Project level |
| `pipeline_run_viewer` | `roles/run.viewer` | Project level |

#### Via `module.scheduler_iam`

| Ressource | Rôle | Cible |
|-----------|------|-------|
| `scheduler_run_invoker` | `roles/run.invoker` | Project level |
| `scheduler_run_developer` | `roles/run.developer` | Project level |

#### Via main.tf (dédié n8n)

| Ressource | Rôle | Cible |
|-----------|------|-------|
| `pipeline_n8n_updater` | `roles/run.developer` | Service `n8n-dev` |

**Via le pipeline global (Workflows) :**

| Ressource | Rôle | Cible |
|-----------|------|-------|
| `pipeline_workflows_invoker` | `roles/workflows.invoker` | Project level (pipeline SA) |
| `workflows_service_account_token_creator` | `roles/iam.serviceAccountTokenCreator` | pipeline SA (allow workflows SA to impersonate) |

Ces permissions permettent au workflow `pipeline-global-dev` d'exécuter le job `n8n-trigger-dev` et le workflow `load-staging-n8n-societe-dev`.

**Synthèse des droits effectifs du `pipeline-runner-dev` :**
- `storage.objectAdmin` — lire/écrire/supprimer des objets GCS
- `bigquery.dataEditor` — lire/écrire dans toutes les tables BQ
- `bigquery.jobUser` — exécuter des jobs BQ (requêtes, loads)
- `secretmanager.secretAccessor` — lire tous les secrets
- `run.jobsExecutor` + `run.developer` — exécuter des Cloud Run Jobs et services
- `run.viewer` — lister l'état des ressources Cloud Run

Ces droits permettent au `n8n_trigger` de : requêter BQ, écrire dans GCS, appeler le webhook n8n (via HTTP public), et marquer les offres traitées dans `staging_societe_tracking`.

### 3.3 Public access

| Ressource | Rôle | Cible |
|-----------|------|-------|
| `n8n_public_access` | `roles/run.invoker` | Service `n8n-dev` — `allUsers` |

---

## 4. Variables d'environnement

### 4.1 n8n service (Cloud Run)

| Variable | Valeur | Source |
|----------|--------|--------|
| `N8N_PORT` | `5678` | main.tf |
| `N8N_PROTOCOL` | `https` | main.tf |
| `N8N_SECURE_COOKIE` | `true` | main.tf |
| `N8N_ENDPOINT_HEALTH` | `health` | main.tf |
| `N8N_RUNNERS_ENABLED` | `false` | main.tf |
| `N8N_RESTRICT_FILE_ACCESS_TO` | `/tmp` | main.tf |
| `GENERIC_TIMEZONE` | `Europe/Paris` | Dockerfile + main.tf |
| `N8N_HOST` | *(non défini — auto-détecté par n8n)* | main.tf |
| `N8N_EDITOR_BASE_URL` | *(non défini — auto-détecté par n8n)* | main.tf |
| `WEBHOOK_URL` | *(non défini — auto-détecté par n8n)* | main.tf |
| `N8N_ENCRYPTION_KEY` | (secret) | Secret Manager |

### 4.2 n8n_trigger job (Cloud Run Job)

| Variable | Valeur | Source |
|----------|--------|--------|
| `ENVIRONMENT` | `dev` | main.tf |
| `GCS_BUCKET_NAME` | `data-market-386959-data-lake-dev` | main.tf |
| `GCP_PROJECT_ID` | `data-market-386959` | main.tf |
| `STORAGE` | `gcs` | main.tf |
| `INTERMEDIATE_DATASET_ID` | `intermediate_dev` | main.tf |
| `STAGING_DATASET_ID` | `staging_dev` | main.tf |
| `N8N_WEBHOOK_URL` | `https://n8n-dev-.../webhook/societe-scraper` | main.tf (généré automatiquement) |

---

## 5. Workflow n8n : societe.com scraper

### 5.1 Fichier

`n8n/societe.com-scraper.json`

### 5.2 Nœuds

| Nœud | Type | Rôle |
|------|------|------|
| **Webhook** | `n8n-nodes-base.webhook` | Reçoit POST sur `/webhook/societe-scraper` avec `{siren, employer_name, nom_commune}`. Méthode HTTP spécifiée via `"httpMethod": "POST"` dans le JSON (par défaut GET). Le contenu du body est accessible via `$json.body.*` (pas `$json.*`) |
| **HTTP Request** | `n8n-nodes-base.httpRequest` | GET `https://www.societe.com/societe/{slug}-{siren}.html` où `slug = $json.body.employer_name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')` |
| **Set Output** | `n8n-nodes-base.set` | Passe les champs : `siren`, `employer_name`, `nom_commune`, `html` (contenu de la page) |
| **Respond to Webhook** | `n8n-nodes-base.respondToWebhook` | Renvoie le résultat au caller |

### 5.3 Import automatique

Au démarrage du conteneur, `entrypoint.sh` exécute :

```bash
n8n import:workflow --input=/app/workflows/societe.com-scraper.json
```

L'import **désactive** le workflow (même si le JSON a `"active": true`, cf. l'option `--activeState=fromJson` qui ne fonctionne pas en mode non-queue). Le workflow doit être activé **après déploiement** (cf. §5.4).

### 5.4 Activation post-déploiement

L'activation passe par l'API REST de n8n, accessible **uniquement depuis l'URL Cloud Run externe** (les routes `/rest/*` retournent 404 en localhost dans le conteneur).

Le script `n8n/n8n_activate.sh` automatise les 4 étapes :

1. `POST /rest/owner/setup` — créer l'owner (ignoré si déjà existant)
2. `POST /rest/login` — récupérer le cookie `n8n-auth`
3. `GET /rest/workflows/:id` — récupérer le `versionId` courant
4. `POST /rest/workflows/:id/activate` — activer avec `{"versionId":"..."}`

Déploiement complet :

```bash
docker build -f n8n/Dockerfile -t n8n:local ./n8n
docker tag n8n:local europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/n8n:dev
docker push europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/n8n:dev
gcloud run deploy n8n-dev --image=europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/n8n:dev --region=europe-west1 --project=data-market-386959 --port=5678 --no-use-http2
bash n8n/n8n_activate.sh
```

---

## 6. Code source

### 6.1 `01_shared/shared/n8n.py` — N8nClient

```python
class N8nClient:
    def __init__(self, webhook_url: str)
    def trigger_workflow(self, payload: dict) -> list[dict]
```

Simple client HTTP POST avec timeout 120s. Utilisé par `n8n_trigger/main.py`.

### 6.2 `02_extract/n8n_trigger/main.py` — Point d'entrée

Fonctionnement :
1. `get_untracked_offers()` : requête BQ qui joint `int_adzuna_offres` × `staging_api_entreprise` × `staging_societe_tracking` pour trouver les offres avec SIREN non encore scrapées
2. Pour chaque offre :
   - Si `N8N_WEBHOOK_URL` défini : `scrape_via_n8n(n8n_client, siren, employer_name, nom_commune)`
   - Si n8n échoue ou n'est pas configuré : `scraper.scrape_societe(siren, company_name)` (fallback direct HTTP)
3. Résultats sauvegardés dans GCS : `raw/n8n_societe/{timestamp}.ndjson`
4. Traçage inséré dans `staging_societe_tracking`

### 6.3 `02_extract/n8n_trigger/scraper.py` — Parsing HTML

Fonctions exportées :

| Fonction | Rôle |
|----------|------|
| `parse_societe_html(html, siren)` | Parse le HTML déjà récupéré (utilisé après n8n) |
| `scrape_societe(siren, company_name)` | Fait la requête HTTP + parse (fallback direct) |

Extraction depuis le HTML :
- **JSON-LD** : `<script type="application/ld+json">` → `legalName`, `identifier` (SIREN/SIRET/TVA), `naics`, `description`, `foundingDate`, `address`, `additionalProperty`, `member` (dirigeants)
- **dt/dd** : `Capital social`, `Convention collective`, `Noms commerciaux`, `Statut RCS`, `Statut INSEE`, `Statut RNE`
- **ADSTACK.data** : `chiffre` (chiffre d'affaires), `effectif`

### 6.4 `02_extract/n8n_trigger/Dockerfile` — Image du trigger

Multi-stage build : `uv sync --frozen --no-dev --package n8n-trigger` → `python:3.13-slim`. Le trigger n'a pas besoin du workflow n8n embarqué ; il appelle l'instance n8n distante via HTTP.

---

## 7. Intégration CI/CD

### 7.1 Images Docker

| Image | Dockerfile | Tags |
|-------|------------|------|
| `n8n` | `n8n/Dockerfile` | `n8n:{tag}`, `n8n:{version}`, `n8n:latest` |
| `n8n-trigger` | `02_extract/n8n_trigger/Dockerfile` | `n8n-trigger:{tag}`, `n8n-trigger:{version}`, `n8n-trigger:latest` |

### 7.2 Pipeline GitHub Actions (`release.yml`)

- **Path filter** : `n8n/**` → build de l'image n8n ; `02_extract/n8n_trigger/**` → build de n8n-trigger
- **Manual override** : `n8n=true`, `n8n_trigger=true`
- **Promote** : les images `n8n` et `n8n-trigger` sont retaggées `dev` → `prod`

### 7.3 Déploiement manuel

```bash
# Build
docker build -f n8n/Dockerfile -t n8n:local ./n8n

# Tag & push vers Artifact Registry
docker tag n8n:local europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/n8n:dev
docker push europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/n8n:dev
```

---

## 8. Orchestration dans le pipeline global

Le workflow `pipeline-global-dev` exécute les étapes n8n **après** toutes les autres étapes post-traitement :

```
[Parallel branches: FT, GEO, Adzuna, Sirene, API Entreprise]
    │
    ▼
run_dbt (dbt-run-dev)
    │
    ▼
run_n8n_extract (n8n-trigger-dev)     ← Cloud Run Job Java
    │
    ▼
run_n8n_load (load-staging-n8n-societe-dev)  ← Cloud Workflow
    │
    ▼
done
```

Le load workflow :
1. BigQuery load job depuis `gs://{bucket}/raw/n8n_societe/*.ndjson` vers `staging_n8n_societe`
2. Liste les fichiers dans `raw/n8n_societe/`
3. Copie chaque fichier vers `raw/n8n_societe/done/`
4. Supprime le fichier original

---

## 9. Limitations et notes

- **1 instance toujours active** : `manual_instance_count = 1`. Pas de cold start. Coût ~30-40€/mois en dev. Pour passer en scale-to-zero, remplacer par `manual_instance_count = 0` et ajouter `N8N_HOST`/`N8N_EDITOR_BASE_URL`/`WEBHOOK_URL` auto-détectés.
- **URL auto-détectée** : n8n détermine son URL depuis l'en-tête `Host` des requêtes Cloud Run. Pas de hardcodage nécessaire.
- **Dépendances BQ** : le `n8n_trigger` nécessite que les tables `int_adzuna_offres` et `staging_api_entreprise` soient déjà peuplées (produites par les jobs d'extraction + dbt en amont).
- **Fallback direct** : si n8n n'est pas disponible, le trigger utilise le scraping HTTP direct via `scraper.scrape_societe()`, assurant la résilience.
- **Prod** : l'environnement `prod` ne déploie PAS n8n. Le promote CI/CD tag les images mais le Terraform prod n'inclut pas les ressources n8n.

---

## 10. Références Terraform

Toutes les ressources n8n sont définies dans `00_infra/opentofu/environments/dev/main.tf` (lignes 475-577 pour le service, 619-747 pour les tables et workflows). Modules utilisés :

| Module | Emplacement |
|--------|-------------|
| `cloud_run_service` | `00_infra/opentofu/modules/cloud_run_service/` |
| `cloud_run_job` | `00_infra/opentofu/modules/cloud_run_job/` |
| `bigquery_table` | `00_infra/opentofu/modules/bigquery_table/` |
| `secret_manager_secret` | `00_infra/opentofu/modules/secret_manager_secret/` |
| `service_account` | `00_infra/opentofu/modules/service_account/` |
| `workflow` | `00_infra/opentofu/modules/workflow/` |
| `pipeline_monitoring` | `00_infra/opentofu/modules/pipeline_monitoring/` |
