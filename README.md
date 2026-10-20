# AirIndex India

**Airfare Intelligence & CPI Augmentation Platform · SIH 2026 project**

AirIndex India is an evolving Python project for building an auditable data platform around airfare observations. The current repository provides the foundation for configuration, fare-domain validation, a small FastAPI service, database/migration scaffolding, and tests. Collection pipelines, indexing, production analytics and a user-facing dashboard are still planned work; they should not be treated as completed functionality.

## Current implementation

- FastAPI application with `GET /` and `GET /health` endpoints.
- Pydantic settings loaded from environment variables.
- Domain models for fare observations and search requests, including derived total-fare/advance-day fields and route validation.
- SQLAlchemy/Alembic scaffolding for relational storage.
- Tests for health metadata and core fare-domain validation.

## Architecture direction

```text
Data sources / permitted collectors
             |
             v
  Normalize + validate observations
             |
             v
  PostgreSQL / SQLAlchemy / Alembic
             |
             v
 Quality checks + analytics + indexing
             |
             v
   API and reporting/dashboard layer
```

This diagram describes the intended direction, not a claim that every component is implemented.

## Requirements

- Python 3.12+
- PostgreSQL if/when running database-backed flows
- Optional collection dependencies: Playwright and Scrapy, installed only when needed

## Set up locally

From the repository root:

```bash
python3.12 -m venv .venv
```

Activate the environment and install the package with developer tools:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

python -m pip install -e ".[dev]"
```

Copy the sample configuration and start the API:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS/Linux
cp .env.example .env

uvicorn airindex.main:app --app-dir src --reload
```

Open `http://127.0.0.1:8000/docs` for the generated API docs, or `http://127.0.0.1:8000/health` for the liveness endpoint.

## Run quality checks

```bash
pytest
ruff check .
mypy src
```

## Data and compliance notes

- Use permitted, documented data sources and respect each source's terms, robots policies, and request limits.
- Store collection time, source, route/date, fare components, and scraper version so records remain auditable.
- Do not describe collected prices as real-time until a scheduled/operational collector is implemented and monitored.
- Do not commit database credentials, API keys, or private data. Change the development-only secret before any deployment.
