# data_market_pipeline

Pipeline de donnees sur le marche DATA en France.

## Prerequis

- Python 3.12
- `uv`
- Docker, si vous voulez tester les images localement

## Installation locale

Depuis la racine du projet :

```bash
uv sync --dev
```

## Variables d'environnement

Exemple minimal pour lancer les APIs en local :

```bash
# France Travail
export STORAGE=local
export GCP_PROJECT_ID=your-gcp-project
export GCS_BUCKET_NAME=your-bucket
export FT_CLIENT_ID=your-france-travail-client-id
export FT_CLIENT_KEY=your-france-travail-client-key

# GEO
export STORAGE=local
```

Notes :

- `STORAGE` pilote `france_travail` et doit valoir `local` ou `gcs`
- `STORAGE` pilote aussi `geo` et doit valoir `local` ou `gcs`
- l'API France Travail exige `FT_CLIENT_ID` et `FT_CLIENT_KEY`
- en local, les donnees sont ecrites sous `02_extract/data/`

## Lancer les APIs en local

### France Travail

Depuis la racine du projet :

```bash
cd 02_extract/france_travail
export FT_EXTRACT_TARGET=offers
uv run python main.py
```

Valeurs utiles pour `FT_EXTRACT_TARGET` :

- `offers`
- `referentials`
- `all`

Exemples :

```bash
FT_EXTRACT_TARGET=offers uv run python 02_extract/france_travail/main.py
FT_EXTRACT_TARGET=referentials uv run python 02_extract/france_travail/main.py
FT_EXTRACT_TARGET=all uv run python 02_extract/france_travail/main.py
```

### GEO

Depuis la racine du projet :

```bash
cd 02_extract/geo
uv run python main.py
```

## Tester avec Docker

Les Dockerfiles sont concus pour etre buildes depuis la racine du repository.

### Image France Travail

Build :

```bash
docker build -f 02_extract/france_travail/Dockerfile -t data-market-ft:local .
```

Run :

```bash
docker run --rm \
  -e STORAGE=local \
  -e GCP_PROJECT_ID=your-gcp-project \
  -e GCS_BUCKET_NAME=your-bucket \
  -e FT_CLIENT_ID=your-france-travail-client-id \
  -e FT_CLIENT_KEY=your-france-travail-client-key \
  -e FT_EXTRACT_TARGET=offers \
  data-market-ft:local
```

Exemples :

```bash
docker run --rm \
  -e STORAGE=local \
  -e GCP_PROJECT_ID=your-gcp-project \
  -e GCS_BUCKET_NAME=your-bucket \
  -e FT_CLIENT_ID=your-france-travail-client-id \
  -e FT_CLIENT_KEY=your-france-travail-client-key \
  -e FT_EXTRACT_TARGET=offers \
  data-market-ft:local

docker run --rm \
  -e STORAGE=local \
  -e GCP_PROJECT_ID=your-gcp-project \
  -e GCS_BUCKET_NAME=your-bucket \
  -e FT_CLIENT_ID=your-france-travail-client-id \
  -e FT_CLIENT_KEY=your-france-travail-client-key \
  -e FT_EXTRACT_TARGET=all \
  data-market-ft:local
```

### Image GEO

Build :

```bash
docker build -f 02_extract/geo/Dockerfile -t data-market-geo:local .
```

Tag et push vers Artifact Registry :

```bash
docker build -f 02_extract/geo/Dockerfile -t extract-geo:latest .
docker tag extract-geo:latest europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/extract-geo:latest
docker push europe-west1-docker.pkg.dev/data-market-386959/data-market-docker-repository/extract-geo:latest
```

Run :

```bash
docker run --rm \
  -e STORAGE=local \
  data-market-geo:local
```
