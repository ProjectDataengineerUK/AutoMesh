"""Machine and human validation report generation."""

import json
from datetime import datetime
from pathlib import Path
from platform.validation.evaluator import evaluate_maturity
from platform.validation.models import Evidence
from platform.validation.registry import Capability
from typing import Any


def build_report(
    capabilities: tuple[Capability, ...],
    evidence: tuple[Evidence, ...],
    now: datetime,
    commit_sha: str,
) -> dict[str, Any]:
    rows = []
    for capability in capabilities:
        capability_evidence = tuple(item for item in evidence if item.capability_id == capability.capability_id)
        rows.append(
            {
                "capability_id": capability.capability_id,
                "name": capability.name,
                "owner": capability.owner,
                "maturity": evaluate_maturity(capability, capability_evidence, now, commit_sha).value,
                "evidence": [item.to_dict() for item in capability_evidence],
            }
        )
    return {"generated_at": now.isoformat(), "commit_sha": commit_sha, "capabilities": rows}


def write_report(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "validation-report.json"
    markdown_path = output_dir / "validation-report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# AutoMesh Validation Report",
        "",
        f"Commit: `{report['commit_sha']}`",
        "",
        "| Capability | Maturity | Evidence |",
        "|---|---|---:|",
    ]
    lines.extend(
        f"| {row['capability_id']} — {row['name']} | {row['maturity']} | {len(row['evidence'])} |"
        for row in report["capabilities"]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path
