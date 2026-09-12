# AirIndex India n8n automation

`airindex_intelligence_pipeline.json` is the full prototype orchestration workflow. It is intentionally inactive after import so configuration can be reviewed first.

## Pipeline

`Manual/Schedule -> Run config -> permitted source -> normalize + hard validation -> quality gate -> anomaly/quality scoring -> route + lead-time stratification -> controlled batches -> AirIndex ingest -> audit -> anomaly alert -> latest-index read-back -> intelligence snapshot -> audit sink`

An `Error Trigger -> Critical Error Alert` path provides operational failure visibility.

## Environment

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
```

For a local presentation, `data/demo/replay_source.json` is a safe replay source. It includes normal observations plus deliberately invalid/duplicate examples so the validation layer can be demonstrated without claiming live market data.

## Quality controls demonstrated

- Route and carrier-format validation
- INR-only validation
- Positive fare and bounded fare checks
- Travel-date and advance-purchase validation
- Duplicate detection within a source batch
- Freshness scoring
- Route-level median deviation and anomaly flags
- Observation quality score
- T+1/T+7/T+15/T+30/T+45 lead-time stratification
- Batch dispatch to protect downstream APIs
- Run-level provenance and audit identifiers
- Optional anomaly alerts
- Latest-index read-back
- Optional audit/SIEM sink
- Workflow-level critical error alerting

The workflow does not bypass CAPTCHAs, anti-bot controls, paywalls or other access restrictions. Use only data sources that the collection method is permitted to access.
