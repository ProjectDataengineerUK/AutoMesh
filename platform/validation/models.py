"""Closed models used by the validation plane."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class Gate(StrEnum):
    UNIT = "unit"
    CONTRACT = "contract"
    LINT = "lint"
    DAGBAG = "dagbag"
    LOCAL_INTEGRATION = "local_integration"
    EXTERNAL_SMOKE = "external_smoke"
    RECOVERY = "recovery"
    ALERT = "alert"
    RUNBOOK = "runbook"


class EvidenceStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP_WITH_REASON = "SKIP_WITH_REASON"


class Maturity(StrEnum):
    NOT_VALIDATED = "Not Validated"
    IMPLEMENTED = "Implemented"
    LOCALLY_VALIDATED = "Locally Validated"
    INFRASTRUCTURE_VALIDATED = "Infrastructure Validated"
    OPERATIONALLY_COMPLETE = "Operationally Complete"


@dataclass(frozen=True)
class Evidence:
    capability_id: str
    gate: Gate
    status: EvidenceStatus
    environment: str
    commit_sha: str
    started_at: datetime
    finished_at: datetime
    reason_code: str | None = None
    expires_at: datetime | None = None
    artifact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status is EvidenceStatus.PASS and self.reason_code is not None:
            raise ValueError("PASS evidence cannot have a reason code")
        if self.status is not EvidenceStatus.PASS and not self.reason_code:
            raise ValueError("FAIL and SKIP evidence require a reason code")
        if self.gate is Gate.EXTERNAL_SMOKE and self.status is EvidenceStatus.PASS and self.expires_at is None:
            raise ValueError("external PASS evidence requires expiry")
        if self.finished_at < self.started_at:
            raise ValueError("finished_at cannot precede started_at")

    def is_current(self, now: datetime, commit_sha: str, code_independent: bool = False) -> bool:
        normalized_now = now.astimezone(timezone.utc)
        if self.expires_at is not None and self.expires_at.astimezone(timezone.utc) < normalized_now:
            return False
        return code_independent or self.commit_sha == commit_sha

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["gate"] = self.gate.value
        payload["status"] = self.status.value
        for field in ("started_at", "finished_at", "expires_at"):
            value = payload[field]
            payload[field] = value.isoformat() if value is not None else None
        payload["artifact_refs"] = list(self.artifact_refs)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Evidence":
        return cls(
            capability_id=str(payload["capability_id"]),
            gate=Gate(payload["gate"]),
            status=EvidenceStatus(payload["status"]),
            reason_code=payload.get("reason_code"),
            environment=str(payload["environment"]),
            commit_sha=str(payload["commit_sha"]),
            started_at=datetime.fromisoformat(payload["started_at"]),
            finished_at=datetime.fromisoformat(payload["finished_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]) if payload.get("expires_at") else None,
            artifact_refs=tuple(payload.get("artifact_refs", ())),
        )
