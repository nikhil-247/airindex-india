# Canonical Airfare Data Dictionary

| Field | Type | Required | Description |
|---|---|---:|---|
| observation_id | UUID | yes | Stable identifier for a canonical observation |
| source | string | yes | Source system identifier |
| source_type | enum | yes | airline, ota, reference, replay |
| collected_at | datetime | yes | UTC collection timestamp |
| origin | string | yes | IATA origin airport code |
| destination | string | yes | IATA destination airport code |
| travel_date | date | yes | Intended travel date |
| advance_days | integer | yes | Days between collection date and travel date |
| carrier | string | no | Marketing/operating carrier when available |
| flight_number | string | no | Flight identifier when available |
| fare_class | string | no | Fare bucket/class when available |
| fare_family | string | no | Consumer-facing fare family when available |
| base_fare | decimal | no | Base fare in source currency |
| taxes | decimal | no | Taxes/mandatory government charges |
| user_development_fee | decimal | no | UDF when separately identified |
| convenience_fee | decimal | no | Booking/convenience charge when separately identified |
| total_fare | decimal | yes | Displayed total payable fare |
| currency | string | yes | ISO currency code |
| stops | integer | no | Number of stops |
| departure_time | time | no | Scheduled departure time |
| arrival_time | time | no | Scheduled arrival time |
| availability | enum | yes | available, sold_out, unknown |
| extraction_status | enum | yes | extracted, partial, failed |
| validation_status | enum | yes | valid, suspect, rejected |
| quality_score | decimal | no | 0–100 data quality score |
| collector_version | string | yes | Version of source adapter |
| raw_record_hash | string | yes | Hash linking to raw evidence |

## Invariants

- `origin != destination`.
- `travel_date >= collection local date` for forward-looking searches.
- `advance_days` must agree with the collection date and travel date after timezone normalization.
- monetary values cannot be negative.
- `total_fare` must be present for a usable price observation.
- if all fare components are present, their arithmetic relationship to `total_fare` is validated with a configurable tolerance.
- currency is normalized to an ISO code.

Raw source-specific fields may be retained separately. The canonical contract is intentionally smaller and stable so downstream statistical components do not depend on website markup.
