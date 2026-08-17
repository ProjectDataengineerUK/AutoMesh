"""Common structured event envelope."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pipelines.observability.context import current_context


@dataclass(frozen=True)
class EventEnvelope:
    event_type: str
    domain: str
    result: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, event_type: str, domain: str, result: str, **attributes: Any) -> "EventEnvelope":
        context = current_context()
        return cls(
            event_type=event_type,
            domain=domain,
            result=result,
            event_id=context.get("event_id", str(uuid4())),
            correlation_id=context.get("correlation_id", str(uuid4())),
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["occurred_at"] = self.occurred_at.isoformat()
        return payload
