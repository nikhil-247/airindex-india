# AirIndex India n8n automation

AirIndex provides two n8n imports:

- `airindex_intelligence_pipeline.json`: full configurable orchestration workflow using instance environment variables.
- `airindex_cloud_demo.json`: n8n Cloud-friendly presentation workflow with configuration stored inside the workflow, so it does not depend on instance environment variables.

Both are intentionally inactive after import.

## Full intelligence pipeline

`Manual/Schedule -> Run config -> permitted source -> normalize + hard validation -> anomaly/quality scoring -> measurement readiness -> route + lead-time stratification -> controlled batching -> AirIndex ingest -> audit -> alerting -> index read-back -> intelligence snapshot -> audit sink`

An `Error Trigger -> Critical Error Alert` path provides operational failure visibility.

## Cloud demo pipeline

`Manual -> Demo Configuration -> Replay Source -> Validation -> Anomaly/Quality -> Readiness -> Route/Lead-Time -> Batch -> optional Vercel Ingest -> Audit -> optional Index Read-back -> Snapshot -> Completion`

The cloud demo starts with `ingest_enabled=false` and `index_enabled=false`, so it can run against the public replay dataset without any secret or server environment configuration. After Vercel deployment, edit the `Demo Configuration` node, set the Vercel URLs and switch both flags to `true` for the integrated run.

## Full-pipeline environment

```text
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
```

## Quality controls

- Route and carrier-format validation
- INR-only validation
- Positive and bounded fare checks
- Travel-date and advance-purchase validation
- Duplicate detection
- Freshness scoring
- Route-level median deviation and anomaly flags
- Observation quality score
- T+1/T+7/T+15/T+30/T+45 lead-time stratification
- Measurement-readiness gate
- Controlled batch dispatch
- Run-level provenance and audit identifiers
- Optional anomaly alerts
- Optional latest-index read-back
- Optional audit/SIEM/Drive sink
- Workflow-level critical error alerts

## Presentation demo

Use `data/demo/replay_source.json` as the controlled replay source. It contains valid observations plus deliberately invalid and duplicate examples so the quality layer can be demonstrated without presenting fabricated values as live market data.

Recommended demo sequence:

1. Import `airindex_cloud_demo.json`.
2. Open `Demo Configuration` and leave the two integration flags off for the first run.
3. Run manually and show the validation, anomaly, stratification, batching and final audit nodes.
4. After deploying AirIndex to Vercel, set `ingest_url` and `index_url`, then turn the flags on.
5. Run again and show the same pipeline crossing the deployed API boundary.

Do not configure the workflows to bypass CAPTCHAs, anti-bot controls, paywalls or source restrictions. Use only data sources that the collection method is permitted to access.
