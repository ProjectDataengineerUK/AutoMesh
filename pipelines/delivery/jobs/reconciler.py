from __future__ import annotations

from datetime import datetime

from pipelines.delivery.common.models import DecisionStatus, utcnow
from pipelines.delivery.common.storage import InMemoryDeliveryStore


def expire_decisions(store: InMemoryDeliveryStore, now: datetime | None = None) -> int:
    current_time = now or utcnow()
    expired = 0
    for decision in store.list_pending_decisions():
        if decision.expires_at <= current_time:
            _, changed = store.compare_and_set_decision(
                decision.decision_id,
                DecisionStatus.PENDING,
                DecisionStatus.EXPIRED,
                actor_id="system:expiry",
                now=current_time,
            )
            expired += int(changed)
    return expired
