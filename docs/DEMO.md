# AirIndex India Prototype Demo

## Run locally

From the repository root:

```bash
python -m pip install -e '.[dev]'
alembic upgrade head
uvicorn airindex.api.app:app --reload
```

Open `http://127.0.0.1:8000/` for the dashboard and `http://127.0.0.1:8000/health` for the API health check. The dashboard is intentionally labelled **DEMO REPLAY DATA**.

A static-server option is only useful for viewing the HTML itself; the live dashboard fetches its calculated values from the FastAPI endpoint, so the API-hosted version is recommended for the presentation.

## What to capture for the SIH presentation

1. Dashboard showing the national experimental index, route indices and lead-time windows.
2. API response from `GET /api/v1/demo/index` showing methodology version, route weights and computed values.
3. Advanced n8n workflow showing scheduled/manual trigger, permitted-source fetch, hard validation, anomaly scoring, lead-time stratification, controlled dispatch, API ingestion, alerting, index read-back and audit sink.
4. PostgreSQL migration/test CI check showing a reproducible backend.

## n8n: advanced intelligence pipeline

For the full prototype, import `n8n/airindex_intelligence_pipeline.json` into n8n. It is inactive by default and is designed as an orchestration layer around the AirIndex API rather than as a substitute for the statistical engine.

Configure these environment variables:

- `AIRINDEX_SOURCE_URL`: a permitted source or replay JSON endpoint.
- `AIRINDEX_INGEST_URL`: AirIndex observation-ingest endpoint.
- `AIRINDEX_INDEX_URL`: latest-index endpoint used for read-back after ingestion.
- `AIRINDEX_ALERT_WEBHOOK_URL`: optional webhook for anomaly and execution-error alerts.
- `AIRINDEX_AUDIT_WEBHOOK_URL`: optional sink for run/audit snapshots.
- `AIRINDEX_FRESHNESS_LIMIT_MINUTES`: freshness threshold, default `180`.
- `AIRINDEX_ANOMALY_THRESHOLD_PCT`: fare deviation threshold, default `35`.
- `AIRINDEX_ALERT_ANOMALY_RATE_PCT`: anomaly-rate alert threshold, default `20`.
- `AIRINDEX_BATCH_SIZE`: controlled batch size, default `100`.

The workflow adds provenance and operational controls around the measurement pipeline: run IDs, route/carrier/date/fare checks, currency checks, duplicate detection, freshness scoring, route-level median deviation, anomaly flags, quality scoring, lead-time windows, batching, post-ingest index read-back, an audit snapshot, warning alerts and an error-trigger path.

Do not configure it to bypass CAPTCHAs, anti-bot controls or source restrictions. The workflow is intended for permitted collection and replay/demo sources.

## Important prototype wording

Use **experimental Airfare Price Index / prototype** in slides. Do not present replay values as live national market statistics or as an official CPI measure.
