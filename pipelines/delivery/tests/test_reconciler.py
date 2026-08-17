from __future__ import annotations

from datetime import timedelta

from pipelines.delivery.common.models import ActionType, Decision, DecisionStatus, utcnow
from pipelines.delivery.common.storage import InMemoryDeliveryStore
from pipelines.delivery.jobs.reconciler import expire_decisions


def test_reconciler_expires_only_overdue_decisions() -> None:
    store = InMemoryDeliveryStore()
    expired = store.create_decision(Decision("c1", ActionType.REVIEW_PR, "pr:1", {}, utcnow() - timedelta(1)))
    active = store.create_decision(Decision("c2", ActionType.REVIEW_PR, "pr:2", {}, utcnow() + timedelta(1)))
    assert expire_decisions(store) == 1
    assert store.get_decision(expired.decision_id).status == DecisionStatus.EXPIRED
    assert store.get_decision(active.decision_id).status == DecisionStatus.PENDING
