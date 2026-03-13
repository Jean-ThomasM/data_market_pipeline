# Test Setup - France Travail PostgreSQL

Test setup for loading France Travail job offers JSON into a PostgreSQL database running in Docker.

## Structure

```
test_postgres_setup/
├── docker-compose.yml       # PostgreSQL container configuration
├── init.sql                 # Database schema initialization
├── loader.py                # Script to load JSON into PostgreSQL
├── test_db_loader.py        # Pytest tests
├── fixtures/
│   └── test_offres.json     # Sample test data
└── README.md                # This file
```

## Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Dependencies: `psycopg2`, `pytest`

## Installation

Install the required dependencies:

```bash
uv add psycopg2-binary pytest
```

## Usage

### 1. Start the PostgreSQL container

```bash
cd test_postgres_setup
docker-compose up -d
```

Wait a few seconds for the database to be ready.

### 2. Load test data

```bash
python loader.py
```

### 3. Run tests

```bash
pytest test_db_loader.py -v
```

The tests will:
- Start the PostgreSQL container automatically
- Load the test fixtures
- Verify data insertion, upserts, and queries
- Clean up the container after completion

### 4. Stop the container

```bash
docker-compose down -v
```

## Database Schema

### Tables

- **offres**: Main table storing job offers
- **offres_competences**: Required skills/competences for each offer
- **offres_permis**: Required licenses/permits for each offer

### Connection Details

| Parameter | Value |
|-----------|-------|
| Host | localhost |
| Port | 5432 |
| Database | francetravail_test |
| User | test_user |
| Password | test_password |

## Environment Variables

You can override the default connection settings:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=francetravail_test
export DB_USER=test_user
export DB_PASSWORD=test_password
```

## Example Queries

```sql
-- Count offers by contract type
SELECT type_contrat, COUNT(*) FROM offres GROUP BY type_contrat;

-- Find offers by ROME code
SELECT intitule, lieu_travail_libelle FROM offres WHERE rome_code = 'M1811';

-- Query JSONB field
SELECT intitule FROM offres WHERE raw_json->>'entrepriseAdaptee' = 'true';

-- Get competences for an offer
SELECT c.competence_libelle 
FROM offres_competences c 
JOIN offres o ON c.offre_id = o.id 
WHERE o.id = 'TEST001';
```
