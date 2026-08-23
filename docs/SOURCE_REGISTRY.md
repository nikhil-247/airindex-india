# AirIndex India Source Registry

This registry records external data sources and their intended role. A source is not automatically approved for automated collection merely because it is publicly reachable.

| Source | Role | Collection class | Status |
|---|---|---|---|
| MoSPI CPI 2024 documentation | methodology/reference | public web/PDF | reference |
| MoSPI CPI/e-Sankhyiki | official statistical reference | public portal/API where available | to validate |
| DGCA publications | route/traffic/fare-monitoring reference | public government material | reference |
| Airline websites | airfare observations | source-specific permitted collection only | pending policy review |
| OTA websites | airfare observations | source-specific permitted collection only | pending policy review |
| Recorded observations | deterministic replay/demo | local fixture | approved |

## Source admission rules

A collector must have a source policy entry before it can run in live mode.

The policy records:

- source owner
- canonical URL
- robots.txt review timestamp
- terms/policy review status
- permitted collection mechanism
- request rate/budget
- authentication requirements
- parser version
- last successful collection
- health status
- replay fixture availability

## Free-first rule

No paid API is required for the core system. Official/public reference data and locally generated/replayed observations must be sufficient to run tests, index calculations and the dashboard.

Optional AI providers are advisory only. Their failure must not stop collection, cleaning, indexing or API operation.

## Provenance

Each retrieved artifact should retain:

```text
source_id
source_url
retrieved_at
content_hash
collector_version
source_policy_version
```

Where licensing or terms prohibit archival of raw source content, store only permitted derived fields plus provenance metadata.
