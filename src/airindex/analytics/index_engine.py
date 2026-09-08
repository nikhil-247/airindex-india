"""Deterministic AirIndex elementary and route-level calculations."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import exp, log
from typing import Mapping, Sequence


class IndexCalculationError(ValueError):
    """Raised when index inputs violate the configured methodology."""


@dataclass(frozen=True)
class ElementaryIndexResult:
    """Elementary Jévons index and the number of matched observations."""

    value: Decimal
    observation_count: int


def _to_positive_float(value: Decimal, label: str) -> float:
    if value <= 0:
        raise IndexCalculationError(f"{label} must be greater than zero")
    return float(value)


def calculate_jevons_index(
    reference_prices: Mapping[str, Decimal],
    current_prices: Mapping[str, Decimal],
    *,
    minimum_observations: int = 3,
    base_level: Decimal = Decimal("100.0"),
) -> ElementaryIndexResult:
    """Calculate a Jévons elementary index from matched price relatives.

    Only keys present in both periods are compared. Every matched price must be
    strictly positive because a price relative is undefined at zero.
    """
    if minimum_observations < 1:
        raise IndexCalculationError("minimum_observations must be at least one")
    if base_level <= 0:
        raise IndexCalculationError("base_level must be greater than zero")

    matched_keys = sorted(reference_prices.keys() & current_prices.keys())
    if len(matched_keys) < minimum_observations:
        raise IndexCalculationError(
            f"insufficient observations: {len(matched_keys)} < {minimum_observations}"
        )

    log_sum = 0.0
    for key in matched_keys:
        reference = _to_positive_float(reference_prices[key], f"reference price for {key}")
        current = _to_positive_float(current_prices[key], f"current price for {key}")
        log_sum += log(current / reference)

    geometric_relative = exp(log_sum / len(matched_keys))
    value = (float(base_level) * geometric_relative).quantize(Decimal("0.000001"))
    return ElementaryIndexResult(value=value, observation_count=len(matched_keys))


def aggregate_route_indices(
    route_indices: Mapping[str, Decimal],
    route_weights: Mapping[str, Decimal],
    *,
    base_level: Decimal = Decimal("100.0"),
) -> Decimal:
    """Aggregate route indices with configured fixed weights.

    The v0.1.0 methodology requires complete basket coverage and weights that
    sum to one. Missing routes therefore produce an insufficient-coverage error
    rather than silently imputing or renormalizing the remaining routes.
    """
    if not route_weights:
        raise IndexCalculationError("route_weights cannot be empty")
    if base_level <= 0:
        raise IndexCalculationError("base_level must be greater than zero")

    missing = sorted(set(route_weights) - set(route_indices))
    if missing:
        raise IndexCalculationError(
            "insufficient coverage: missing route indices for " + ", ".join(missing)
        )

    total_weight = sum(route_weights.values(), Decimal("0"))
    if total_weight != Decimal("1"):
        raise IndexCalculationError(
            f"route weights must sum to 1.0, got {total_weight}"
        )

    weighted_value = sum(
        route_indices[route] * route_weights[route] for route in route_weights
    )
    return weighted_value.quantize(Decimal("0.000001"))
