"""Convert an existing test or lint result into validation evidence."""

from datetime import datetime, timezone
from platform.validation.models import Evidence, EvidenceStatus, Gate


def result_evidence(capability_id: str, gate: Gate, return_code: int, commit_sha: str) -> Evidence:
    now = datetime.now(timezone.utc)
    passed = return_code == 0
    return Evidence(
        capability_id=capability_id,
        gate=gate,
        status=EvidenceStatus.PASS if passed else EvidenceStatus.FAIL,
        reason_code=None if passed else "ASSERTION_FAILED",
        environment="ci",
        commit_sha=commit_sha,
        started_at=now,
        finished_at=now,
    )
