"""Deterministic capability maturity evaluation."""

from datetime import datetime
from platform.validation.models import Evidence, EvidenceStatus, Gate, Maturity
from platform.validation.registry import Capability

IMPLEMENTED_GATES = frozenset({Gate.UNIT, Gate.CONTRACT, Gate.LINT})
LOCAL_GATES = frozenset({Gate.LOCAL_INTEGRATION})
INFRASTRUCTURE_GATES = frozenset({Gate.EXTERNAL_SMOKE})
OPERATIONAL_GATES = frozenset({Gate.RECOVERY, Gate.ALERT, Gate.RUNBOOK})


def evaluate_maturity(
    capability: Capability,
    evidence: tuple[Evidence, ...],
    now: datetime,
    commit_sha: str,
) -> Maturity:
    passed = {
        item.gate
        for item in evidence
        if item.capability_id == capability.capability_id
        and item.status is EvidenceStatus.PASS
        and item.is_current(now, commit_sha)
    }
    implemented_required = IMPLEMENTED_GATES.intersection(capability.required_gates)
    if not implemented_required or not implemented_required.issubset(passed):
        return Maturity.NOT_VALIDATED
    maturity = Maturity.IMPLEMENTED
    if LOCAL_GATES.intersection(capability.required_gates).issubset(passed):
        maturity = Maturity.LOCALLY_VALIDATED
    else:
        return maturity
    if INFRASTRUCTURE_GATES.intersection(capability.required_gates).issubset(passed):
        maturity = Maturity.INFRASTRUCTURE_VALIDATED
    else:
        return maturity
    if OPERATIONAL_GATES.intersection(capability.required_gates).issubset(passed):
        maturity = Maturity.OPERATIONALLY_COMPLETE
    return maturity
