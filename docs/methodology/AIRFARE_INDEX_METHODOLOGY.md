# AirIndex India: Airfare Index Methodology

**Status:** Phase 1 working specification  
**Problem Statement:** SIH 2026, PS 26056  
**Methodology version:** `0.1.0`

## 1. Purpose

AirIndex India is an experimental, high-frequency airfare indicator designed to augment official statistical measurement with granular online airfare observations. It is **not an official MoSPI index** and must never be presented as one.

The system is designed around five principles:

1. comparable observations
2. transparent aggregation
3. reproducibility
4. explicit data-quality treatment
5. full provenance

## 2. Official-methodology alignment

MoSPI's CPI 2024 series introduced online sources for selected services, including airfares, alongside traditional and administrative sources. The project therefore treats AirIndex as an augmentation and research platform rather than claiming to replace current official collection.

The elementary index implementation will support a geometric-mean (Jevons-style) formulation because this is useful for an elementary price-relative indicator and is consistent with the methodological direction documented for CPI 2024. Higher-level aggregation remains a separate configurable layer.

## 3. Observation unit

The canonical observation is a consumer-facing one-way airfare quote for a specific:

- origin airport/city
- destination airport/city
- travel date
- collection timestamp
- carrier
- flight/fare option when available
- fare family/class when available
- advance-purchase window
- fare components
- source

Raw observations are immutable. Cleaning creates a derived status; it does not overwrite the raw record.

## 4. Advance-purchase windows

The first specification uses:

- `T+1`
- `T+7`
- `T+15`
- `T+30`
- `T+45`

where `T` is the collection date in the source's relevant local date context.

The actual travel date is retained so observations can be re-bucketed if the methodology changes.

## 5. Canonical price

The preferred index price is the comparable consumer-facing total payable fare for a standardized search. The dataset separately stores:

- base fare
- taxes
- user development fee, when separately exposed
- convenience/platform fee, when exposed
- other mandatory charges
- total payable fare

Optional services such as seats, meals, insurance and baggage add-ons are excluded unless the methodology version explicitly defines them as mandatory for comparability.

If a source exposes only a total fare, the total is retained and component fields are null rather than fabricated.

## 6. Observation validation

An observation is eligible only when required fields are valid and the fare is positive.

Core checks include:

```text
origin != destination
travel_date >= collection_date
advance_days == date_difference(travel_date, collection_date)
total_fare > 0
base_fare >= 0 when present
taxes >= 0 when present
fees >= 0 when present
currency == INR for the initial domestic index
```

Invalid records are retained with a rejection reason.

## 7. Duplicate handling

Duplicates are identified using a canonical fingerprint built from the source, route, travel date, carrier, flight/fare identifiers, departure context and quoted price.

A duplicate is not silently deleted from raw storage. The pipeline marks the observation as duplicate and selects a canonical record for downstream calculations.

## 8. Outlier treatment

Airfares are genuinely volatile, so an extreme value is not automatically an error.

The pipeline therefore separates:

- **data error:** impossible or malformed observation
- **statistical anomaly:** unusual but potentially real fare
- **valid observation:** suitable for index calculation

Candidate anomaly methods include route/window-level robust statistics such as median absolute deviation (MAD) and interquartile range (IQR). Thresholds are versioned configuration, not hidden constants.

The first implementation should flag anomalies before exclusion. Exclusion requires a documented rule and leaves an audit trail.

## 9. Elementary route/window index

For a route/window cell `c`, let `p_ti` be the valid comparable price observation at time `t` and `p_0i` its reference-period price.

The Jevons-style elementary price index is:

```text
J_t,c = 100 * exp( mean_i[ ln(p_ti / p_0i) ] )
```

Equivalent form:

```text
J_t,c = 100 * ( product_i(p_ti / p_0i) ) ^ (1/n)
```

The exact matched-observation rule is part of the configuration. We will prefer a stable cell definition rather than accidentally comparing different fare populations.

## 10. Route aggregation

Each route receives a versioned weight `w_r` with:

```text
sum_r(w_r) = 1
```

The route-level aggregate is configurable. The baseline research implementation will support a weighted arithmetic aggregation of route relatives:

```text
A_t = sum_r( w_r * J_t,r )
```

A chain-linking layer can then connect successive reference periods where basket or source composition changes.

This separation is deliberate: the elementary calculation, route weighting and temporal linking are independently testable.

## 11. Route basket

The problem statement's example routes are treated as initial candidates, not permanent weights.

The basket engine will eventually use official aviation traffic evidence, route persistence, source coverage and geographic representation to select a configurable basket. Selection and weighting are separate artifacts and each basket version is immutable after publication.

## 12. Missing observations

Missingness is classified rather than imputed blindly:

- `SOURCE_UNAVAILABLE`
- `FLIGHT_SOLD_OUT`
- `NO_MATCHING_FARE`
- `PARSER_FAILURE`
- `NETWORK_FAILURE`
- `QUALITY_REJECTED`

The first index implementation will use explicit coverage thresholds. A cell with insufficient valid observations is marked `insufficient_coverage` rather than silently receiving a fabricated price.

## 13. Publication levels

AirIndex will publish:

- daily experimental index
- weekly summary
- monthly summary
- route/window indices
- contribution analysis
- coverage and data-quality indicators

Every published value should expose:

- methodology version
- basket version
- weight version
- observation count
- coverage percentage
- generated timestamp
- freshness status

## 14. Backtesting

The required validation period is at least 30 days.

Backtesting will compare AirIndex-derived movements against comparable public/official reference information where definitions permit. It will report:

- Pearson/Spearman correlation where appropriate
- MAE
- RMSE
- MAPE only where denominators are meaningful
- directional accuracy
- turning-point agreement
- coverage rate

The report will explicitly document conceptual differences between a quote-based high-frequency indicator and any monthly official fare statistic.

## 15. Reproducibility

Every index run records:

```text
methodology_version
basket_version
weight_version
source_registry_version
pipeline_version
input_time_range
observation_count
quality_rules_version
```

An index value must be reproducible from the same immutable inputs and configuration.

## 16. Revision policy

Live observations may be corrected after parser or quality improvements. Published values therefore carry a revision status.

The dashboard will distinguish:

- provisional
- revised
- finalized

The project will never overwrite historical raw observations.

## 17. Non-goals

The following are explicitly outside the first methodology version:

- claiming official CPI status
- predicting future fares as the core index
- scraping around access controls
- fabricating missing observations
- using an LLM to calculate official statistics
- making causal claims from correlation alone

## 18. Primary references

- MoSPI, CPI 2024 FAQ and series documentation: https://mospi.gov.in/uploads/documents/documents/1770891066052-Annexure_V.pdf
- MoSPI, CPI January 2026 release / methodology discussion: https://mospi.gov.in/uploads/latestReleases/latest_release_1770891893893_6b458c0a-c327-4fef-a554-41131ea67273_Press_Relase_of_CPI_for_Jan26.pdf
- DGCA Tariff Monitoring Unit information in Parliamentary material: https://sansad.in/getFile/annex/270/AU967_7LwIXw.pdf?source=pqars

These references are evidence for project design decisions. They do not imply endorsement of AirIndex India.
