import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_advanced_n8n_workflow_has_expected_nodes_and_is_inactive() -> None:
    path = ROOT / "n8n" / "airindex_intelligence_pipeline.json"
    workflow = json.loads(path.read_text(encoding="utf-8"))

    node_names = {node["name"] for node in workflow["nodes"]}
    expected = {
        "Manual Run",
        "Scheduled Run - Every 6h",
        "Run Config + Audit ID",
        "Fetch Permitted Source",
        "Normalize + Hard Validation",
        "Quality Gate",
        "Anomaly + Quality Scoring",
        "Stratify by Route + Lead Window",
        "Controlled Batch Dispatcher",
        "AirIndex API Ingest",
        "Build Audit Record",
        "Anomaly Alert Gate",
        "Refresh / Read Latest Index",
        "Create Intelligence Snapshot",
        "Audit Sink / SIEM / Drive",
        "Completion Summary",
        "Error Trigger",
        "Critical Error Alert",
    }

    assert expected <= node_names
    assert workflow["active"] is False


def test_replay_source_is_explicitly_non_live() -> None:
    path = ROOT / "data" / "demo" / "replay_source.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["source"] == "airindex-demo-replay"
    assert payload["currency"] == "INR"
    assert len(payload["observations"]) >= 10
