from decimal import Decimal
from math import isclose

import pytest

from airindex.analytics.index_engine import (
    IndexCalculationError,
    aggregate_route_indices,
    calculate_jevons_index,
)


def test_jevons_index_matches_geometric_mean_of_price_relatives() -> None:
    result = calculate_jevons_index(
        {
            "f1": Decimal("100"),
            "f2": Decimal("200"),
            "f3": Decimal("400"),
        },
        {
            "f1": Decimal("110"),
            "f2": Decimal("180"),
            "f3": Decimal("440"),
        },
    )

    expected = 100.0 * (1.10 * 0.90 * 1.10) ** (1.0 / 3.0)
    assert result.observation_count == 3
    assert isclose(float(result.value), expected, abs_tol=0.000001)


def test_jevons_ignores_unmatched_observations_but_requires_minimum() -> None:
    result = calculate_jevons_index(
        {"f1": Decimal("100"), "f2": Decimal("200"), "old": Decimal("50")},
        {"f1": Decimal("110"), "f2": Decimal("220"), "new": Decimal("75")},
        minimum_observations=2,
    )

    assert result.observation_count == 2
    assert result.value == Decimal("110.000000")

    with pytest.raises(IndexCalculationError, match="insufficient observations"):
        calculate_jevons_index(
            {"f1": Decimal("100")},
            {"f1": Decimal("110")},
            minimum_observations=2,
        )


def test_jevons_rejects_zero_or_negative_prices() -> None:
    with pytest.raises(IndexCalculationError, match="must be greater than zero"):
        calculate_jevons_index(
            {"f1": Decimal("0"), "f2": Decimal("100"), "f3": Decimal("200")},
            {"f1": Decimal("10"), "f2": Decimal("110"), "f3": Decimal("220")},
        )


def test_route_aggregation_uses_fixed_weights() -> None:
    result = aggregate_route_indices(
        {"DEL-BOM": Decimal("110"), "DEL-BLR": Decimal("90")},
        {"DEL-BOM": Decimal("0.6"), "DEL-BLR": Decimal("0.4")},
    )

    assert result == Decimal("102.000000")


def test_route_aggregation_rejects_missing_coverage() -> None:
    with pytest.raises(IndexCalculationError, match="insufficient coverage"):
        aggregate_route_indices(
            {"DEL-BOM": Decimal("110")},
            {"DEL-BOM": Decimal("0.6"), "DEL-BLR": Decimal("0.4")},
        )


def test_route_aggregation_rejects_weights_that_do_not_sum_to_one() -> None:
    with pytest.raises(IndexCalculationError, match="sum to 1.0"):
        aggregate_route_indices(
            {"DEL-BOM": Decimal("110"), "DEL-BLR": Decimal("90")},
            {"DEL-BOM": Decimal("0.5"), "DEL-BLR": Decimal("0.4")},
        )
