"""Probe selection, precondition handling and evidence persistence."""

import json
from datetime import datetime, timezone
from pathlib import Path
from platform.validation.inventory import Inventory
from platform.validation.models import Evidence, EvidenceStatus
from platform.validation.probes import Probe
from platform.validation.registry import load_reason_codes, validate_evidence_reason


def run_probes(probes: tuple[Probe, ...], inventory: Inventory, output_dir: Path) -> tuple[Evidence, ...]:
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    allowed_reasons = load_reason_codes()
    results: list[Evidence] = []
    for probe in probes:
        precondition = probe.precondition(inventory)
        if precondition.ready:
            result = probe.run()
        else:
            now = datetime.now(timezone.utc)
            result = Evidence(
                capability_id=probe.capability_id,
                gate=probe.gate,
                status=EvidenceStatus.SKIP_WITH_REASON,
                reason_code=precondition.reason_code or "PRECONDITION_FAILED",
                environment=inventory.environment,
                commit_sha="UNVERSIONED",
                started_at=now,
                finished_at=now,
            )
        validate_evidence_reason(result.reason_code, allowed_reasons)
        target = evidence_dir / f"{result.capability_id}-{result.gate.value}.json"
        target.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        results.append(result)
    return tuple(results)
