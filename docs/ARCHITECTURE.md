# AirIndex India — Architecture

## System context

```text
                    ┌──────────────────────────┐
                    │ Permitted data sources   │
                    │ Airlines / OTAs / refs   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Collection Orchestrator  │
                    │ schedule + policy        │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Source Adapter Layer     │
                    │ Playwright / HTTP / CSV  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Immutable Raw Evidence   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Quality + Normalization  │
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       ┌───────────────────┐            ┌───────────────────┐
       │ Canonical Dataset │            │ Data Quality      │
       │ PostgreSQL/Parquet│            │ scores + issues   │
       └─────────┬─────────┘            └─────────┬─────────┘
                 │                                │
                 └──────────────┬─────────────────┘
                                ▼
                    ┌──────────────────────────┐
                    │ Index & Analytics Engine │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
        ┌──────────┐       ┌──────────┐       ┌──────────┐
        │ FastAPI  │       │ Backtest │       │ Exports  │
        └────┬─────┘       └──────────┘       └──────────┘
             │
             ▼
        ┌──────────────────────────────┐
        │ Institutional Web Dashboard │
        └──────────────────────────────┘
```

## Core boundaries

### Collectors
Convert source-specific responses into a shared `FareObservation` contract. Collectors must not contain index calculations.

### Pipeline
Validate, normalize, deduplicate and classify observations. Pipeline stages are deterministic and independently testable.

### Index engine
Consumes canonical observations plus versioned basket/weight/methodology configuration. It does not know how data was scraped.

### API
Read-only analytical surface initially. Mutating/admin endpoints will be isolated and authenticated when introduced.

### Web application
Presentation and interaction only. Statistical calculations belong in backend services.

## Failure model

A source failure is data about the source, not a reason to crash the platform. The orchestrator records the failure, applies bounded retry policy and continues with other sources.

## Reproducibility

Every index result stores references to:

- methodology version;
- route basket version;
- weight version;
- pipeline version;
- observation window;
- source snapshot/run identifiers.

## Deployment target

Local development uses Docker Compose. Production deployment can be split into web, API, workers, PostgreSQL and Redis components. Object storage is optional until raw evidence volume requires it.
