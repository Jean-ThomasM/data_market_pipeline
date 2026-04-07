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
export ENV=local
export GCP_PROJECT_ID=your-gcp-project
export GCS_BUCKET_NAME=your-bucket
export FT_CLIENT_ID=your-france-travail-client-id
export FT_CLIENT_KEY=your-france-travail-client-key
export GEO_API_URL=https://geo.api.gouv.fr
```

Notes :

- `ENV` doit valoir `local` ou `prod`
- l'API France Travail exige `FT_CLIENT_ID` et `FT_CLIENT_KEY`
- l'API GEO exige `GEO_API_URL`
- en local, les donnees sont ecrites sous `02_extract/data/`

## Lancer les APIs en local

### France Travail

Depuis la racine du projet :

```bash
cd 02_extract/france_travail
uv run uvicorn ft_api:app --reload --host 0.0.0.0 --port 8000
```

Endpoints utiles :

- `GET /health`
- `POST /referentials`
- `POST /offers`

Exemples :

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/referentials
curl -X POST "http://127.0.0.1:8000/offers?mode=local"
```

### GEO

Depuis la racine du projet :

```bash
cd 02_extract/geo
uv run uvicorn geo_api:app --reload --host 0.0.0.0 --port 8001
```

Endpoints utiles :

- `GET /health`
- `POST /extract`

Exemples :

```bash
curl http://127.0.0.1:8001/health
curl -X POST http://127.0.0.1:8001/extract
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
docker run --rm -p 8000:8000 \
  -e ENV=local \
  -e GCP_PROJECT_ID=your-gcp-project \
  -e GCS_BUCKET_NAME=your-bucket \
  -e FT_CLIENT_ID=your-france-travail-client-id \
  -e FT_CLIENT_KEY=your-france-travail-client-key \
  data-market-ft:local
```

Test :

```bash
curl http://127.0.0.1:8000/health
curl -X POST "http://127.0.0.1:8000/offers?mode=local"
```

### Image GEO

Build :

```bash
docker build -f 02_extract/geo/Dockerfile -t data-market-geo:local .
```

Run :

```bash
docker run --rm -p 8001:8000 \
  -e ENV=local \
  -e GEO_API_URL=https://geo.api.gouv.fr \
  data-market-geo:local
```

Test :

```bash
curl http://127.0.0.1:8001/health
curl -X POST http://127.0.0.1:8001/extract
```
