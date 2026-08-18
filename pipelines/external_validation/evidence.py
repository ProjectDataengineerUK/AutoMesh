"""Redacted validation evidence writers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_report(
    config: dict[str, object],
    gates: list[dict[str, object]],
    objects=None,
    reconciliation=None,
    commit: str | None = None,
) -> dict[str, object]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "config": config,
        "gates": gates,
        "objects": objects or [],
        "reconciliation": reconciliation or [],
    }


def write_json(report: dict[str, object], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
