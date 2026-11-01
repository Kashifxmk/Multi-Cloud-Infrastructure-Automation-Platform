import json

from core.report_generator import write_report


def test_report_generation(tmp_path):
    config = {"project": {"name": "demo", "environment": "dev"}, "cloud": {"provider": "gcp", "region": "test"}}
    report = write_report(config, "deployed", {"ip": {"value": "127.0.0.1"}}, tmp_path)
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["status"] == "deployed"
    assert data["provider"] == "gcp"
