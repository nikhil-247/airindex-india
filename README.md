# AirIndex India

**Real-Time Airfare Intelligence & CPI Augmentation Platform**

SIH 2026 project repository.

AirIndex is designed as an auditable measurement pipeline: it turns permitted airfare observations into a reproducible experimental Airfare Price Index (APIx), rather than treating a collection of raw fares as the statistic itself.

## Current prototype

The public-facing website is structured as a government-style statistical information portal (demonstration only), with Home, Market Dashboard, Routes, Airlines, Airports, Data Quality, Methodology, Data Catalogue, Releases, API & Downloads, and About/Governance sections.

The rich demonstration dataset includes a 30-day national index series, 12 route indicators, 7 carrier indicators, 10 airport indicators, booking-horizon measures, regional summaries, a source registry, release archive and data catalogue. The replay layer is intentionally separate from future authorized live connectors.

The public portal is now backed by a deterministic SQLite demo store. On first startup it seeds 18,000 synthetic fare observations plus source, release, alert, route, airline and airport tables. The browser ingestion console writes new observations into this local store and the website reads aggregate statistics back through FastAPI endpoints. Set `AIRINDEX_RUNTIME_DB` to move the demo store elsewhere. On Vercel, the demo store uses `/tmp` and is therefore not durable production storage.



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
GET  /api/v1/demo/portal
GET  /api/v1/stats/summary
GET  /api/v1/stats/routes
GET  /api/v1/stats/airlines
GET  /api/v1/stats/airports
GET  /api/v1/stats/sources
GET  /api/v1/stats/releases
GET  /api/v1/stats/alerts
GET  /api/v1/stats/series
GET  /api/v1/stats/observations
POST /api/v1/ingest/fare-observations
~~~

The current ingest endpoint validates and persists an n8n-compatible batch in the local SQLite demo store. It is real local demo persistence, not durable production persistence.

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