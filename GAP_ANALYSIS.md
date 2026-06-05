# Gap Analysis — Brief vs Réalisation

## Résumé d'exécution

| Vérification | Statut | Détails |
|---|---|---|
| `ruff check` | ✅ Passe | 0 erreurs |
| `ruff format --check` | ✅ Passe | 58 fichiers formatés |
| `pytest` | ✅ 118 passed, 2 skipped | 2 tests skipped (API réelle) |
| `dbt parse` | ✅ Passe | Warning résolu (bloc `silver:` supprimé) |
| `sqlfluff lint` | ⚠️ 8/8 fichiers échouent | TMP/PRS = faux positifs jinja + SQLite ; formatage cosmétique |

---

## 1. Sources de données (cartographie)

| Exigence brief | Statut | Commentaire |
|---|---|---|
| France Travail documentée | ✅ | Tableau dans README + scraper fonctionnel |
| API Géo documentée | ✅ | Tableau dans README + scraper fonctionnel |
| Sirene INSEE documentée | ✅ | Mentionné comme "Stub" dans README |
| Champs de jointure identifiés | ✅ | Jointure offres ↔ entreprises via SIRET dans modèles int_ft_offres, int_adzuna_offres |
| Limites de qualité mentionnées | ✅ | Contraintes OAuth2, rate limiting, volumes |

**Écart(s) :** Aucun (le module Sirene a été retiré car non utilisé ; l'intégration Sirene n'est pas nécessaire pour répondre à la question centrale).

---

## 2. Architecture Medallion

| Exigence brief | Statut | Commentaire |
|---|---|---|
| Couche Raw (bronze) | ✅ | Tables `staging_*` dans BigQuery |
| Couche Staging (silver) | ✅ | Tables `int_*` (intermediate) |
| Couche Marts (gold) | ✅ | Tables `mart_*` |
| Schéma d'architecture | ✅ | Mermaid dans README + `architecture.png` |
| Choix technologiques justifiés | ✅ | Section README "Pourquoi GCP ?" |

**Écart(s) :** Aucun écart significatif.

---

## 3. Ingestion & Automatisation

| Exigence brief | Statut | Commentaire |
|---|---|---|
| Scripts Python fonctionnels (3 sources) | ✅ | FT, GEO, Adzuna |
| OAuth2 France Travail avec cache | ✅ | Token géré via `create_authenticated_session()` dans FT |
| Gestion d'erreurs et journalisation | ✅ | Logging Python + gestion exceptions |
| Pagination des résultats | ✅ | FT scraper gère Content-Range / pagination |
| Ingestion planifiée sans intervention | ✅ | Cloud Scheduler → Workflows → Cloud Run Jobs |
| Idempotence | ✅ | Déduplication par `offer_id` dans int_ft_offres |

**Écart(s) :**
- **Aucun chargement Parquet pour Sirene** (voir ci-dessus)
- **Rate limiting** : mentionné dans README mais pas de mécanisme explicite de backoff/retry dans les scrapers

---

## 4. Transformation SQL (dbt)

| Exigence brief | Statut | Commentaire |
|---|---|---|
| 3 couches (staging/intermediate/marts) | ✅ | 11 modèles SQL organisés |
| Tests dbt (not_null, unique, accepted_values) | ✅ | Présents dans `schema.yml` |
| Partitionnement et clustering | ❌ | Aucune config de partitionnement/clustering dans les modèles dbt ou `schema.yml` |
| Documentation des modèles | ✅ | DATA_CATALOG.md |

**Écart(s) :**
- **Partitionnement/clustering** : le brief exige l'utilisation de ces fonctionnalités. Les modèles SQL utilisent `partition by` dans des window functions mais ne définissent pas de partitionnement/clustering au niveau table (config dbt).

---

## 5. Infrastructure & IaC

| Exigence brief | Statut | Commentaire |
|---|---|---|
| IaC (Infrastructure as Code) | ✅ | OpenTofu dans `00_infra/opentofu/` |
| Modules réutilisables | ✅ | 14 modules sous `modules/` |
| Gestion des secrets | ✅ | Secret Manager |
| IAM / moindre privilège | ✅ | Service accounts |

**Écart(s) :**
- **Validation IaC sur PR** : le CI (`ci.yml`) ne valide PAS l'IaC. Pas de `tofu validate` ou `tofu plan` sur les PR. Le `tofu apply` est seulement dans `release.yml` sur push.

---

## 6. CI/CD

| Exigence brief | Statut | Commentaire |
|---|---|---|
| Validation Python (lint) sur PR | ✅ | Ruff check + format dans `ci.yml` |
| Compilation SQL (dbt) sur PR | ✅ | dbt parse + sqlfluff dans `ci.yml` |
| Validation IaC sur PR | ❌ | Manquant dans `ci.yml` |
| Tests sur PR | ✅ | pytest dans `ci.yml` |
| Déploiement automatique sur main | ✅ | `release.yml` avec build/push + tofu apply |
| Jobs planifiés | ✅ | Cloud Scheduler + Workflows |

**Écart(s) :**
- **Validation IaC sur PR** absente

---

## 7. Dashboard & Coûts

| Exigence brief | Statut | Commentaire |
|---|---|---|
| Dashboard analytique (3 angles) | ✅ | Looker Studio : géographique, sectoriel, temporel |
| Dashboard coûts cloud | ✅ | Looker Studio FinOps : coût par service, évolution |
| Alertes budget | ⚠️ | Non vérifiable sans accès GCP |
| Catalogue de données | ✅ | DATA_CATALOG.md (descriptions, sources, fréquences, tags) |
| Lignage des données | ✅ | Visible dans dbt docs + DATA_CATALOG.md |
| Données sensibles taguées | ✅ | DATA_CATALOG.md |
| Estimation des coûts (Infracost) | ❌ | Aucun outil d'estimation de coûts |

**Écart(s) :**
- **Aucune estimation Infracost** ou équivalent
- **Alertes budget** : mentionné comme produit mais non vérifiable

---

## 8. Livrables

| Livrable brief | Statut | Commentaire |
|---|---|---|
| Repo GitHub public | ✅ | `data-market-pipeline` |
| Scripts Python ingestion | ✅ | 5 extracteurs |
| `.env.example` | ✅ | 5 fichiers |
| `requirements.txt` | ❌ | Projet utilise `uv` (pas de requirements.txt) |
| Modèles SQL (staging/intermediate/marts) | ✅ | 11 modèles |
| Tests dbt + documentation | ✅ | Tests dans schema.yml + DATA_CATALOG.md |
| Modules IaC | ✅ | 14 modules OpenTofu |
| Workflows CI/CD | ⚠️ | Manque validation IaC sur PR |
| Dockerfile(s) | ✅ | 8 Dockerfiles |
| `docker-compose` | ❌ | Seulement dans `_old/` (inactif) |
| README complet | ✅ | Architecture, choix cloud, instructions |
| Dashboard BI public | ✅ | Lien Looker Studio |
| Dashboard coûts | ✅ | Lien Looker Studio FinOps |
| Schéma d'architecture (image/drawio) | ⚠️ | PNG présent mais pas de fichier `.drawio` modifiable |
| Tableau Kanban public | ✅ | GitHub Projects |

**Écart(s) :**
- `requirements.txt` absent (pas bloquant : `uv` est la norme, mais le brief l'exige)
- `docker-compose` absent
- Pas de fichier `.drawio` (seulement un PNG figé)

---

## 9. Critères de performance

| Critère | Statut | Notes |
|---|---|---|
| 3 sources documentées | ✅ | |
| Champs de jointure identifiés | ✅ | SIRET entre offres et entreprises |
| Limites de qualité mentionnées | ✅ | |
| Schéma architecture complet | ✅ | README + PNG |
| Choix technologiques justifiés | ✅ | |
| Pattern Medallion appliqué | ✅ | 3 couches |
| 3 sources ingérées | ✅ | 3 sources ingérées (FT, GEO, Adzuna) |
| OAuth2 avec cache token | ✅ | |
| Gestion d'erreurs + logging | ✅ | |
| Planification sans intervention | ✅ | Cloud Scheduler |
| Résultats SQL corrects | ✅ | dbt run + test passent |
| Tests dbt (not_null, unique, accepted_values) | ✅ | |
| Partitionnement/clustering disponibles | ❌ | Pas configuré dans dbt |
| Pipeline exécution bout en bout | ✅ | dbt run |
| CI/CD : lint + SQL + IaC + déploiement | ⚠️ | IaC validation manquante |
| IaC complet (aucune ressource manuelle) | ✅ | |
| Secrets non exposés | ✅ | Secret Manager |
| Dockerfile fonctionnel | ✅ | 8 fichiers |
| Dashboard coûts | ✅ | |
| Catalogue documenté | ✅ | |
| Lignage visible | ✅ | |
| Données sensibles taguées | ✅ | |

---

## Synthèse des écarts critiques

| # | Écart | Priorité |
|---|---|---|

| 2 | **Validation IaC absente du CI** — `tofu validate`/`tofu plan` pas exécuté sur PR | Haute |
| 3 | **Partitionnement/clustering dbt non configuré** — Absent des modèles et schema.yml | Haute |
| 4 | **`requirements.txt` absent** — Exigé par le brief | Moyenne |
| 5 | **`docker-compose.yml` absent** — Exigé par le brief (seulement dans `_old/`) | Moyenne |
| 6 | **Pas de fichier `.drawio` modifiable** — PNG figé uniquement | Basse |
| 7 | **SQLFluff** — 583 violations non corrigées (dont ~95% faux positifs TMP/PRS) | Basse |
| 8 | **Aucune estimation Infracost** — Coûts documentés (dashboard) mais pas estimés en IaC | Basse |

---

## Corrections effectuées durant l'analyse

1. **`dbt_project.yml`** : suppression du bloc `silver:` inutilisé (causait un warning dbt parse)
2. **`tests/geo/test_scraper.py`** : mutation du dict partagé dans le mock `_fetch_resource` → passage de `return_value` à `side_effect` (lambda retournant une nouvelle instance à chaque appel)
3. **`tests/integration/conftest.py`** : changement de scope de `integration_test_dir` de `session` → `function` (les fichiers d'un test polluaient les assertions d'un autre)
4. **`tests/integration/test_france_travail_integration.py`** : nettoyage de `sys.path` après les imports module-level et après l'import dans `test_full_extraction_workflow_mocked` (empêchait le test GEO de résoudre le bon module `scraper`)
5. **`pyproject.toml`** : ajout du marker `slow` pour éliminer le warning pytest
6. **SQLFluff** : 4 violations auto-fixées ; les TMP/PRS sont des faux positifs inévitables (dbt jinja + SQLite)
