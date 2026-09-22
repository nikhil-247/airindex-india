import json
from pathlib import Path

from airindex.analytics.quality_engine import assess_observations

ROOT = Path(__file__).resolve().parents[1]


def test_replay_quality_detects_bad_and_duplicate_rows() -> None:
    payload = json.loads(
        (ROOT / "data" / "demo" / "replay_source.json").read_text(encoding="utf-8")
    )

    assessment = assess_observations(payload["observations"])

    assert assessment.source_count == 12
    assert len(assessment.accepted) == 9
    assert assessment.rejected == [
        {"row_number": 10, "reason": "duplicate observation"},
        {"row_number": 11, "reason": "invalid route"},
        {"row_number": 12, "reason": "invalid total_fare"},
    ]
    assert assessment.duplicate_count == 1
    assert assessment.distinct_routes == 3
    assert assessment.anomaly_count >= 1
    assert set(assessment.window_counts) <= {"T+1", "T+7", "T+15", "T+30", "T+45"}


def test_replay_quality_scores_are_bounded() -> None:
    payload = json.loads(
        (ROOT / "data" / "demo" / "replay_source.json").read_text(encoding="utf-8")
    )
    assessment = assess_observations(payload["observations"])

    assert 0.0 <= assessment.quality_avg <= 1.0
    assert all(0.0 <= float(row["quality_score"]) <= 1.0 for row in assessment.accepted)
