# PROJECT_CONTEXT.md

## Project overview

This project is a **school data engineering brief** carried out by a team of **4 students**.

The goal is to design and implement a full cloud data pipeline able to answer the following business question:

> Where are companies recruiting Data Engineers in France, in which companies, and at what salaries?

The project uses the following public data sources:

- **France Travail API** for job offers
- **INSEE Sirene stock** for company and establishment reference data
- **API Géo** for geographic enrichment

The pipeline must follow a **Medallion architecture**:

- `raw`
- `staging`
- `intermediate`
- `marts`

The target cloud provider is:

- **GCP**

The project must include:

- Python ingestion scripts
- SQL transformations
- Infrastructure as Code
- CI/CD
- public analytical dashboard
- architecture documentation
- data catalog
- cost monitoring

---

## Team context

The project is developed by a team of **4 teammates**.

This means the repository and workflow must be designed for:

- parallel development
- low conflict risk
- clear branch responsibilities
- easy code review
- safe integration before production merge

Keep collaboration in mind in all proposed changes.

---

## Git and branching strategy

GitHub is the central collaboration platform.

### Branch model

The repository must use the following branch strategy:

- `main`  
  Protected production branch.  
  Only reviewed and validated code can be merged here.

- `integration`  
  Shared branch used to consolidate validated features before merging to `main`.

- `feature/<name>`  
  Used for new development work.

- `fix/<name>`  
  Used for bug fixes and corrections.

### Rules

- Never work directly on `main`
- Never suggest direct commits on `main`
- Prefer small, focused branches
- Prefer small pull requests
- Any new work should target `integration` first
- `main` must remain stable and demonstrable

When proposing Git commands, always respect this workflow.

---

## Technical stack

### Runtime and local development

The project must use:

- **Python**
- **uv** for Python environment and dependency management
- **Docker** for reproducible execution
- **GCP** for cloud services

### Important expectations

- Use clean and modular Python code
- Follow **PEP 8**
- Keep code production-oriented
- Use clear folder organization
- Write code in English
- Write comments in English
- Prefer maintainable and team-friendly code

---

## Cloud target

The selected cloud provider is **Google Cloud Platform**.

The architecture should be aligned with common GCP data services, for example:

- object storage
- data warehouse
- scheduler
- container execution
- secret management
- IAM

Suggested direction:

- raw files in GCP object storage
- analytical warehouse in GCP
- containerized ingestion jobs
- scheduled execution
- IaC for all cloud resources

Do not propose Azure or AWS unless explicitly requested.

---

## Development constraints

### Docker

Docker must be part of the project to ensure:

- consistent local setup
- reproducible execution
- easier CI/CD
- easier deployment of ingestion jobs

When relevant, propose:

- a `Dockerfile`
- a `docker-compose.yml` for local development
- clear environment variable handling
- non-hardcoded secrets

### uv

Dependency management must use **uv**.

When generating Python project setup, prefer:

- `uv init`
- `uv add`
- `uv sync`

Do not default to `pip` + `requirements.txt` unless explicitly needed for compatibility.
If both are needed, keep `uv` as the source of truth.

---

## Repository expectations

The repository should stay clear and professional.

A possible structure is:

```text
.
├── src/
│   ├── ingestion/
│   ├── utils/
│   └── config/
├── sql/
│   ├── staging/
│   ├── intermediate/
│   └── marts/
├── infra/
│   ├── modules/
│   └── environments/
├── docs/
├── tests/
├── .github/workflows/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md