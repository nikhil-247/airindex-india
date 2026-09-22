"""Deterministic observation validation and quality scoring for AirIndex replay data."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime

_ROUTE_PATTERN = re.compile(r"^[A-Z]{3}-[A-Z]{3}$")
_CARRIER_PATTERN = re.compile(r"^[A-Z0-9]{2,3}$")
_LEAD_WINDOWS = (1, 7, 15, 30, 45)


@dataclass(frozen=True)
class QualityAssessment:
    """Audit summary for a batch of fare observations."""

    accepted: list[dict[str, object]]
    rejected: list[dict[str, object]]
    source_count: int
    duplicate_count: int
    anomaly_count: int
    anomaly_rate_pct: float
    quality_avg: float
    distinct_routes: int
    window_counts: dict[str, int]


class QualityEngineError(ValueError):
    """Raised when quality-engine configuration is invalid."""


def _parse_datetime(value: object, label: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise QualityEngineError(f"{label} is invalid") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_date(value: object, label: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise QualityEngineError(f"{label} is invalid") from exc


def _lead_window(advance_days: int) -> str:
    for window in _LEAD_WINDOWS:
        if advance_days <= window:
            return f"T+{window}"
    return f"T+{_LEAD_WINDOWS[-1]}"


def assess_observations(
    observations: Iterable[Mapping[str, object]],
    *,
    reference_time: datetime | None = None,
    freshness_limit_minutes: int = 180,
    anomaly_threshold_pct: float = 35.0,
) -> QualityAssessment:
    """Validate, deduplicate, score and flag a batch of airfare observations."""
    if freshness_limit_minutes <= 0:
        raise QualityEngineError("freshness_limit_minutes must be positive")
    if anomaly_threshold_pct < 0:
        raise QualityEngineError("anomaly_threshold_pct cannot be negative")

    rows = list(observations)
    accepted: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    seen: set[str] = set()
    duplicates = 0

    observed_times: list[datetime] = []
    if reference_time is None:
        for row in rows:
            try:
                observed_times.append(
                    _parse_datetime(row.get("observed_at"), "observed_at")
                )
            except QualityEngineError:
                continue
        reference_time = max(observed_times, default=datetime.now(UTC))
    elif reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=UTC)
    reference_time = reference_time.astimezone(UTC)

    for row_number, row in enumerate(rows, start=1):
        try:
            route = str(row.get("route", "")).strip().upper()
            carrier = str(
                row.get("carrier_code", row.get("carrier", ""))
            ).strip().upper()
            fare = float(row.get("total_fare", row.get("totalFare", 0)))
            observed_at = _parse_datetime(row.get("observed_at"), "observed_at")
            travel_date = _parse_date(row.get("travel_date"), "travel_date")
            currency = str(row.get("currency", "INR")).strip().upper()
            advance_days = (travel_date - observed_at.date()).days

            if not _ROUTE_PATTERN.fullmatch(route):
                raise QualityEngineError("invalid route")
            if not _CARRIER_PATTERN.fullmatch(carrier):
                raise QualityEngineError("invalid carrier_code")
            if not 0 < fare <= 1_000_000:
                raise QualityEngineError("invalid total_fare")
            if currency != "INR":
                raise QualityEngineError("currency must be INR")
            if not 1 <= advance_days <= 365:
                raise QualityEngineError("advance_days outside 1..365")
            if travel_date < observed_at.date():
                raise QualityEngineError("travel_date before observed_at")

            key = f"{route}|{carrier}|{travel_date.isoformat()}|{fare:.2f}"
            if key in seen:
                duplicates += 1
                raise QualityEngineError("duplicate observation")
            seen.add(key)

            age_minutes = max(0.0, (reference_time - observed_at).total_seconds() / 60)
            freshness = max(0.0, min(1.0, 1.0 - age_minutes / freshness_limit_minutes))

            accepted.append(
                {
                    "route": route,
                    "carrier_code": carrier,
                    "observed_at": observed_at.isoformat(),
                    "travel_date": travel_date.isoformat(),
                    "total_fare": round(fare, 2),
                    "advance_days": advance_days,
                    "lead_time_window": _lead_window(advance_days),
                    "currency": currency,
                    "source": str(row.get("source", "configured_source")),
                    "freshness_score": round(freshness, 4),
                    "row_number": row_number,
                }
            )
        except (QualityEngineError, TypeError, ValueError) as exc:
            rejected.append({"row_number": row_number, "reason": str(exc)})

    medians: dict[str, float] = {}
    grouped: dict[str, list[float]] = {}
    for row in accepted:
        grouped.setdefault(str(row["route"]), []).append(float(row["total_fare"]))
    for route, fares in grouped.items():
        values = sorted(fares)
        middle = len(values) // 2
        medians[route] = (
            values[middle]
            if len(values) % 2
            else (values[middle - 1] + values[middle]) / 2
        )

    anomaly_count = 0
    windows: dict[str, int] = {}
    for row in accepted:
        median = medians[str(row["route"])]
        deviation = 100.0 * (float(row["total_fare"]) - median) / median
        anomaly = abs(deviation) >= anomaly_threshold_pct
        if anomaly:
            anomaly_count += 1
        row["route_median_fare"] = round(median, 2)
        row["deviation_pct"] = round(deviation, 2)
        row["anomaly_flag"] = anomaly
        score = 0.55 + 0.30 * float(row["freshness_score"])
        score += 0.15 * (0.25 if anomaly else 1.0)
        row["quality_score"] = round(max(0.0, min(1.0, score)), 4)
        window = str(row["lead_time_window"])
        windows[window] = windows.get(window, 0) + 1

    quality_avg = (
        sum(float(row["quality_score"]) for row in accepted) / len(accepted)
        if accepted
        else 0.0
    )
    anomaly_rate = 100.0 * anomaly_count / len(accepted) if accepted else 0.0

    return QualityAssessment(
        accepted=accepted,
        rejected=rejected,
        source_count=len(rows),
        duplicate_count=duplicates,
        anomaly_count=anomaly_count,
        anomaly_rate_pct=round(anomaly_rate, 2),
        quality_avg=round(quality_avg, 4),
        distinct_routes=len(grouped),
        window_counts=windows,
    )
