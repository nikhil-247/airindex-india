import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_json(name: str) -> dict:
    return json.loads((ROOT / "n8n" / name).read_text(encoding="utf-8"))


def test_advanced_n8n_workflow_has_expected_nodes_and_is_inactive() -> None:
    workflow = _load_json("airindex_intelligence_pipeline.json")

    nodes = workflow["nodes"]
    node_names = {node["name"] for node in nodes}
    node_ids = {node["id"] for node in nodes}
    expected = {
        "Manual Run",
        "Scheduled Run - Every 6h",
        "Run Config + Audit ID",
        "Fetch Permitted Source",
        "Normalize + Hard Validation",
        "Anomaly + Quality Scoring",
        "Measurement Readiness Gate",
        "Stratify by Route + Lead Window",
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
    assert len(node_ids) == len(nodes)
    assert "Controlled Batch Dispatcher" not in node_names
    assert workflow["active"] is False

    for connection in workflow["connections"].values():
        for output_group in connection.get("main", []):
            for edge in output_group:
                assert edge["node"] in node_names


def test_cloud_demo_is_importable_without_env_configuration() -> None:
    workflow = _load_json("airindex_cloud_demo.json")

    node_names = {node["name"] for node in workflow["nodes"]}
    assert workflow["active"] is False
    assert "Run Cloud Demo" in node_names
    assert "Demo Configuration" in node_names
    assert "Fetch Replay Source" in node_names
    assert "Completion Summary" in node_names

    config_code = next(
        node["parameters"]["jsCode"]
        for node in workflow["nodes"]
        if node["name"] == "Demo Configuration"
    )
    assert "ingest_enabled:false" in config_code
    assert "index_enabled:false" in config_code
    assert "YOUR-PROJECT.vercel.app" in config_code


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

    spec = importlib.util.spec_from_file_location("vercel_entrypoint", ROOT / "api" / "index.py")
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.app.title == "AirIndex India API"
