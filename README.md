# AirIndex India

**Real-Time Airfare Intelligence & CPI Augmentation Platform**

SIH 2026 project repository.

AirIndex is designed as an auditable measurement pipeline: it turns permitted airfare observations into a reproducible experimental Airfare Price Index (APIx), rather than treating a collection of raw fares as the statistic itself.

## Current prototype

The repository now includes a multi-page product website with Home, Dashboard, Route Explorer, Quality & Audit, Methodology, Pipeline controls and FastAPI docs. All pages use the same-origin API and the committed replay dataset for a deterministic demo.


- Deterministic Jévons elementary-index calculation with fixed route weights.
- PostgreSQL schema and Alembic migration foundations for observations, routes, sources, baskets and index runs.
- FastAPI endpoints for the replay index and a deterministic data-quality audit.
- A presentation-ready intelligence dashboard.
- An advanced n8n orchestration workflow for source ingestion, validation, deduplication, freshness scoring, anomaly detection, lead-time stratification, batching, audit snapshots and optional alerts.
- A replay dataset with valid, duplicate and invalid observations so the quality path is demonstrable without claiming live-market data.
- Vercel-ready deployment files for the dashboard and FastAPI API.

## Prototype endpoints

~~~text
GET  /health
GET  /api/v1/demo/index
GET  /api/v1/demo/quality
GET  /api/v1/demo/overview
POST /api/v1/ingest/fare-observations
~~~

The current ingest endpoint validates an n8n-compatible batch for the prototype and returns an acceptance count. It does not claim durable persistence.

## Local demo

~~~bash
python -m pip install -e '.[dev]'
alembic upgrade head
uvicorn airindex.api.app:app --reload
~~~

Open http://127.0.0.1:8000/.

## Vercel

The repository includes api/index.py, index.html and vercel.json for a same-domain Vercel deployment. Use the repository root as the Vercel project root and deploy the connected GitHub branch.

## n8n

Import:

n8n/airindex_intelligence_pipeline.json

The workflow supports manual execution and a six-hour schedule. Configure:

~~~text
AIRINDEX_SOURCE_URL
AIRINDEX_INGEST_URL
AIRINDEX_INDEX_URL
AIRINDEX_ALERT_WEBHOOK_URL
AIRINDEX_AUDIT_WEBHOOK_URL
AIRINDEX_FRESHNESS_LIMIT_MINUTES=180
AIRINDEX_ANOMALY_THRESHOLD_PCT=35
AIRINDEX_ALERT_ANOMALY_RATE_PCT=20
AIRINDEX_BATCH_SIZE=100
AIRINDEX_MIN_OBSERVATIONS=3
AIRINDEX_MIN_ROUTES=3
~~~

Use only permitted data sources. The workflow is not designed to bypass CAPTCHAs, anti-bot controls, paywalls or other access restrictions.

## Presentation wording

Use **Experimental Airfare Price Index / prototype** when showing replay results.

Do not present replay values as live national market statistics or as an official CPI measure.

## Core principle

**We are not comparing fares. We are measuring airfare movement.**