# Stratégie de Suivi des Coûts (FinOps)

Ce document décrit la stratégie de suivi, d'analyse et d'optimisation des coûts du projet **Data Market Pipeline** hébergé sur Google Cloud Platform (GCP).

---

## 1. Architecture du Pipeline de Facturation (Billing Export)

Pour suivre et maîtriser les coûts de notre architecture serverless, nous configurons l'export automatique de la facturation GCP vers un dataset BigQuery. 

```mermaid
flowchart LR
    GCPBill[GCP Cloud Billing] ➔|Export automatique| BQBill[BigQuery Dataset: gcp_billing_export]
    BQBill ➔|Vue SQL consolidée| BQView[Vue SQL: dynamic_costs]
    BQView ➔|Connexion directe| Looker[Dashboard Looker Studio FinOps]
```

### Étape 1 : Activer l'export de facturation GCP vers BigQuery
1. Accédez à la console **GCP Billing** (Facturation).
2. Cliquez sur **Billing Export** (Exportation de la facturation) dans le menu de gauche.
3. Dans l'onglet **BigQuery export**, activez le **Detailed cost data** (Données détaillées sur les coûts).
4. Spécifiez le projet cible (`data-market-386959`) et créez/choisissez le dataset de destination (ex: `billing_raw`).

### Étape 2 : Vue SQL consolidée dans BigQuery
Pour faciliter la visualisation des coûts, nous déployons une vue SQL BigQuery qui agrège les coûts journaliers par service, ressource et environnement.

```sql
-- Exemple de vue SQL déployée dans le dataset intermediate ou marts
create or replace view `data-market-386959.marts_dev.view_finops_daily_costs` as
select
    invoice.month as facturation_mois,
    date(usage_start_time) as date_usage,
    service.description as service_nom,
    sku.description as ressource_sku,
    project.id as gcp_project_id,
    
    -- Extraction des labels d'environnement si présents
    (select value from unnest(labels) where key = 'environment') as environnement,
    (select value from unnest(labels) where key = 'project') as projet_nom,
    
    sum(cost) as cout_brut,
    sum(cost) + sum(credits.amount) as cout_net,
    currency
from `data-market-386959.billing_raw.gcp_billing_export_v1_XXXXXX`
where project.id = 'data-market-386959'
group by 1, 2, 3, 4, 5, 6, 7, 10
order by date_usage desc;
```

---

## 2. Dashboard Looker Studio FinOps

Une fois la vue créée, nous connectons Looker Studio à BigQuery.

* **Lien vers le gabarit de rapport Looker Studio** : [Looker Studio Billing Template](https://lookerstudio.google.com/reporting/create?c.datasource.connector=bigquery)
* **Indicateurs Clés de Performance (KPIs) présents sur le dashboard** :
  1. **Coût total mensuel (Net)** : Somme des coûts nets après application des crédits d'utilisation gratuite GCP.
  2. **Coût par service** : Répartition graphique (diagramme en camembert) entre *BigQuery*, *Cloud Run*, *Cloud Storage*, *Cloud Workflows*, et *Cloud Scheduler*.
  3. **Tendance journalière** : Histogramme empilé montrant les pics de consommation mensuels.
  4. **Coût moyen par exécution du pipeline** : Évaluation du coût unitaire du workflow (en moyenne < 0,05 € par exécution complète).

---

## 3. Stratégie d'Optimisation des Coûts (FinOps Best Practices)

L'architecture du projet a été choisie spécifiquement pour sa nature **serverless pay-as-you-go**, réduisant les coûts fixes à **0 €** lorsque le pipeline ne tourne pas.

### A. BigQuery (Requêtes & Stockage)
* **Partitionnement et Clichage (Clustering)** : Nos tables intermédiaires et marts sont partitionnées par date de création ou de traitement pour réduire la quantité de données scannées par les requêtes BI.
* **Limitation des requêtes d'exploration** : Dans dbt, nous utilisons la variable `DBT_TARGET_ENV=local` pour développer et tester nos requêtes SQL localement sur une base SQLite (`staging_offres_ft.sqlite`) avant de lancer les modèles volumineux sur BigQuery.
* **Expiration des données brutes** : Les tables du dataset `raw` peuvent être configurées avec une politique d'expiration automatique à 90 jours.

### B. Cloud Run (Extracteurs & dbt)
* **Scale-to-Zero** : Les instances Cloud Run des extracteurs (FT, Géo, Adzuna) et du transformateur dbt sont configurées avec `min_instances = 0`. Aucun coût n'est généré en veille.
* **Allocation de ressources ajustée** : Les jobs d'extraction sont configurés avec 512 MiB de RAM et 1 vCPU, ce qui est suffisant pour du script Python léger, minimisant le coût par seconde d'utilisation.

### C. Cloud Storage (Data Lake)
* **Politique de cycle de vie (Lifecycle Rules)** :
  * Les fichiers bruts stockés dans `gs://data-market-386959-raw-landing/` sont automatiquement transférés vers la classe de stockage **Nearline** après 30 jours, puis **Coldline/Archive** après 90 jours.
  * Suppression automatique des fichiers temporaires après 7 jours.

### D. Cloud Workflows & Scheduler
* Ces services d'orchestration disposent d'un large palier gratuit (ex: 5 000 étapes gratuites par mois pour Workflows). Le pipeline consomme moins de 1% de ce quota gratuit chaque mois.

---

## 4. Modèle dbt FinOps

Un modèle dbt `mart_finops_costs` a été ajouté dans `03_transform/dbt/models/marts/`. Il écrit dans le dataset `finops_dev` et agrège les coûts par jour, service et environnement.

```bash
# Exécution en dev (BigQuery uniquement)
export DBT_TARGET_ENV=dev
uv run dbt run --project-dir 03_transform/dbt --profiles-dir 03_transform/dbt --select mart_finops_costs
```

**IAM requis** : Le SA `dbt-runner-dev` doit avoir `roles/bigquery.dataViewer` sur le dataset `billing_raw` (déjà configuré dans `main.tf`).

**Limitations** : Non disponible en local SQLite (dépend de l'export billing GCP).
