# AirIndex India — Project Specification

## 1. Problem

Develop a real-time, high-frequency airfare price intelligence platform for India that can augment official price statistics with granular observations from permitted airline and online travel sources.

SIH Problem Statement: **26056**.

## 2. Product objective

The platform must transform airfare observations into a transparent statistical product:

1. collect permitted fare observations;
2. preserve provenance and raw evidence;
3. validate and normalize observations;
4. maintain a representative route basket;
5. construct configurable airfare indices;
6. quantify route, airline and lead-time movements;
7. validate/back-test against comparable authoritative/public reference data;
8. expose results through an API and institutional dashboard.

## 3. Required dimensions

Every canonical fare observation should support, where available:

- origin and destination airport/city;
- carrier;
- flight number;
- travel date;
- collection timestamp;
- advance-purchase window;
- fare class/fare family;
- base fare;
- taxes;
- user development fee;
- convenience/booking fees;
- total displayed fare;
- currency;
- stops and schedule metadata;
- source and collector version;
- availability/status;
- validation and quality status.

## 4. Collection principles

The collection layer is adapter-based and source-aware. It must not depend on a single website.

Collection must respect:

- robots.txt where applicable;
- source terms and permitted access;
- reasonable request rates;
- source-specific restrictions;
- data minimization;
- transparent identification where appropriate.

The project must not rely on bypassing CAPTCHAs or security controls. If a source is unavailable, the collector records the failure and the system can fall back to another permitted source or replay data.

## 5. Data quality principles

Raw observations are immutable evidence. Cleaning creates derived records instead of overwriting raw evidence.

Statuses include:

- VALID
- SUSPECT
- OUTLIER
- MISSING
- SOLD_OUT
- SOURCE_ERROR
- PARSER_ERROR
- DUPLICATE

Quality scoring and validation rules must be versioned.

## 6. Index methodology

The index engine is configurable. The implementation should support elementary price relatives, geometric/Jevons-style elementary aggregation and weighted/chain aggregation where appropriate to the selected methodology.

The platform must clearly distinguish an experimental Airfare Price Index from an official CPI measure. Every published index value must record its methodology version, route basket version, weight version and observation window.

## 7. Route basket

The route basket should be data-driven rather than permanently hardcoded. Candidate routes can be ranked using passenger traffic, service frequency, persistence, source coverage and geographic diversity. Weights and selection thresholds are configuration, not source code.

## 8. Frequencies

The platform targets:

- intraday collection where operationally feasible;
- daily index;
- weekly summaries;
- monthly index.

The SIH prototype must prioritize correctness and reproducibility over artificial collection frequency.

## 9. Backtesting

The validation system must support a 30-day or longer historical/replay window and compare AirIndex outputs with comparable public/official reference data. Metrics should include correlation, MAE, RMSE, MAPE where appropriate, directional accuracy and turning-point agreement.

## 10. Institutional product requirements

The dashboard should expose:

- national/index trend;
- route contributions;
- route heatmap;
- lead-time curves;
- fare distributions;
- source health;
- data quality;
- index methodology and calculation provenance;
- backtest performance;
- export/API access.

## 11. Non-functional requirements

- reproducible builds;
- typed interfaces;
- automated tests;
- database migrations;
- structured logging;
- health endpoints;
- secure configuration;
- graceful source failure;
- replay mode for deterministic demonstrations;
- documented deployment process.
