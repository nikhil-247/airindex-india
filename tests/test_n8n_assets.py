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
        "Anomaly + Quality Scoring",
        "Measurement Readiness Gate",
        "Stratify Route + Lead Window",
        "Controlled Batch Planner",
        "AirIndex API Ingest",
        "Build Run Audit Summary",
        "Anomaly Alert Gate",
        "Alert Webhook Configured?",
        "Send Anomaly Alert",
        "Index Read-Back Configured?",
        "Read Latest AirIndex",
        "Create Intelligence Snapshot",
        "Audit Sink Configured?",
        "Write Audit Snapshot",
        "Completion Summary",
        "Measurement Blocked Summary",
        "Error Trigger",
        "Critical Alert Configured?",
        "Critical Error Alert",
    }

    assert expected <= node_names
    assert "Controlled Batch Dispatcher" not in node_names
    assert workflow["active"] is False


def test_replay_source_is_explicitly_non_live() -> None:
    path = ROOT / "data" / "demo" / "replay_source.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["source"] == "airindex-demo-replay"
    assert payload["currency"] == "INR"
    assert len(payload["observations"]) >= 10


def test_vercel_entrypoint_and_dashboard_exist() -> None:
    assert (ROOT / "api" / "index.py").exists()
    assert (ROOT / "index.html").exists()
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    assert config["version"] == 2
