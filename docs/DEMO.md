# AirIndex India Prototype Demo

## Run locally

From the repository root:

```bash
python -m pip install -e '.[dev]'
alembic upgrade head
uvicorn airindex.api.app:app --reload
```

Open `http://127.0.0.1:8000/health` to verify the API, then open `demo/index-dashboard.html` through the same server or a local static server.

A quick static-server option is:

```bash
python -m http.server 8080 --directory demo
```

For the dashboard to load calculated values, serve the dashboard from the API host or configure the browser to allow the local API request. The dashboard is intentionally labelled **DEMO REPLAY DATA**.

## What to capture for the SIH presentation

1. Dashboard showing the national experimental index and the three route indices.
2. API response from `GET /api/v1/demo/index` showing methodology version, route weights and computed values.
3. n8n workflow showing Fetch → Validate/Normalize → Send to AirIndex API.
4. PostgreSQL migration/test CI check showing a reproducible backend.

## n8n

Import `n8n/airindex_ingest_demo.json` into n8n. Set:

- `AIRINDEX_SOURCE_URL` to a permitted source or replay JSON endpoint.
- `AIRINDEX_INGEST_URL` to the deployed AirIndex ingest endpoint.

The workflow is inactive by default. It validates route format, positive fare, travel date and advance-purchase days before forwarding the normalized batch.

Do not configure it to bypass CAPTCHAs, anti-bot controls or source restrictions.

## Important prototype wording

Use **experimental Airfare Price Index / prototype** in slides. Do not present replay values as live national market statistics or as an official CPI measure.
