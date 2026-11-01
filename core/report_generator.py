import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_report(
    config: dict[str, Any],
    status: str,
    outputs: dict[str, Any] | None = None,
    directory: str | Path = "reports",
) -> Path:
    project = config["project"]
    cloud = config["cloud"]
    timestamp = datetime.now(timezone.utc)
    report = {
        "provider": cloud["provider"],
        "environment": project["environment"],
        "region": cloud["region"],
        "status": status,
        "timestamp": timestamp.isoformat(),
        "outputs": outputs or {},
    }
    report_dir = Path(directory)
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{project['name']}-{project['environment']}-{timestamp:%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return path
