# AirIndex India Canonical Data Model

## Purpose

The canonical model is the contract between source collectors, the normalization/data-quality pipeline, the index engine and the API. Source-specific collectors may retain richer fields internally, but anything entering the statistical pipeline must conform to the canonical contract.

## FareObservation

A `FareObservation` represents one quoted itinerary/fare at a particular collection timestamp. It is an observation of a displayed offer, not proof of a completed transaction.

### Identity and provenance

- `observation_id`: globally unique immutable identifier.
- `source_name` / `source_type`: origin of the quote.
- `source_url`: source page when legally and technically available.
- `collected_at`: timestamp of collection.
- `collection_run_id`: groups observations produced by one collector run.
- `scraper_version`: parser/collector version used to create the observation.

### Route and travel context

- IATA origin and destination.
- Travel date.
- Carrier and optional flight number.
- Fare class/family where available.
- Departure/arrival time and number of stops.
- `advance_days` is derived from travel date minus collection date.

### Fare decomposition

The canonical fare is represented as separate non-negative components:

`total_fare = base_fare + taxes + user_development_fee + convenience_fee + other_fees`

This preserves the evidence needed for different analytical definitions and prevents the index engine from depending on a single opaque total.

### Availability and quality

Availability is explicitly represented as `available`, `sold_out` or `unknown`. Quality is represented separately using a status and optional 0–100 score. Raw observations are not deleted merely because a downstream quality rule rejects them.

## Database entities

- `sources`: source identity and policy version.
- `airports`: normalized airport master.
- `airlines`: normalized carrier master.
- `routes`: directed city/airport pair.
- `route_baskets`: versioned statistical basket.
- `route_basket_members`: route membership and weights.
- `collection_runs`: execution-level provenance and health.
- `fare_observations`: durable quote observations.
- `index_runs`: versioned statistical publication records.

## Design constraints

1. Money uses PostgreSQL `NUMERIC`, never floating point.
2. IATA codes are normalized to uppercase three-character codes.
3. Travel date cannot precede collection date.
4. Origin and destination cannot be identical.
5. Raw observations remain available for audit/reprocessing.
6. Derived status and score fields are separate from raw fare fields.
7. Statistical configuration is versioned outside the observation itself and referenced by index runs.

## Future extensions

The schema deliberately leaves room for:

- fare snapshots/raw payload archives in object storage;
- source-specific metadata;
- cabin/brand normalization;
- baggage and ancillary attributes;
- airport-to-city aggregation;
- revision lineage;
- index contribution records;
- backtest runs and metrics.
