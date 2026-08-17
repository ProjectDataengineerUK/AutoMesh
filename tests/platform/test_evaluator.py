from datetime import datetime, timedelta, timezone
from platform.validation.evaluator import evaluate_maturity
from platform.validation.models import Evidence, EvidenceStatus, Gate, Maturity
from platform.validation.registry import Capability

NOW = datetime(2026, 8, 17, tzinfo=timezone.utc)
CAPABILITY = Capability(
    capability_id="CAP-01",
    name="test",
    owner="platform",
    required_gates=(Gate.UNIT, Gate.CONTRACT, Gate.LINT, Gate.LOCAL_INTEGRATION, Gate.EXTERNAL_SMOKE),
)


def evidence(gate: Gate, status: EvidenceStatus = EvidenceStatus.PASS, **overrides: object) -> Evidence:
    values = {
        "capability_id": "CAP-01",
        "gate": gate,
        "status": status,
        "reason_code": None if status is EvidenceStatus.PASS else "ASSERTION_FAILED",
        "environment": "test",
        "commit_sha": "abc",
        "started_at": NOW,
        "finished_at": NOW,
        "expires_at": (
            NOW + timedelta(days=30)
            if gate is Gate.EXTERNAL_SMOKE and status is EvidenceStatus.PASS
            else None
        ),
    }
    values.update(overrides)
    return Evidence(**values)


def test_missing_gate_cannot_promote() -> None:
    result = evaluate_maturity(CAPABILITY, (evidence(Gate.UNIT), evidence(Gate.LINT)), NOW, "abc")
    assert result is Maturity.NOT_VALIDATED


def test_skip_never_promotes() -> None:
    items = (evidence(Gate.UNIT), evidence(Gate.CONTRACT), evidence(Gate.LINT, EvidenceStatus.SKIP_WITH_REASON))
    assert evaluate_maturity(CAPABILITY, items, NOW, "abc") is Maturity.NOT_VALIDATED


def test_expired_external_evidence_is_ignored() -> None:
    items = tuple(evidence(gate) for gate in (Gate.UNIT, Gate.CONTRACT, Gate.LINT, Gate.LOCAL_INTEGRATION)) + (
        evidence(Gate.EXTERNAL_SMOKE, expires_at=NOW - timedelta(seconds=1)),
    )
    assert evaluate_maturity(CAPABILITY, items, NOW, "abc") is Maturity.LOCALLY_VALIDATED


def test_wrong_commit_evidence_is_ignored() -> None:
    items = tuple(evidence(gate, commit_sha="old") for gate in (Gate.UNIT, Gate.CONTRACT, Gate.LINT))
    assert evaluate_maturity(CAPABILITY, items, NOW, "abc") is Maturity.NOT_VALIDATED
