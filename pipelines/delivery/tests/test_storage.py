from __future__ import annotations

from datetime import timedelta

from pipelines.delivery.common.models import (
    ActionType,
    Channel,
    Decision,
    DecisionStatus,
    Notification,
    NotificationType,
    utcnow,
)
from pipelines.delivery.common.storage import InMemoryDeliveryStore


def test_notification_idempotency_key_returns_existing_record() -> None:
    store = InMemoryDeliveryStore()
    item = Notification("c1", NotificationType.REPORT, "user", Channel.TEAMS, {}, "stable-key")
    first, created_first = store.create_notification(item)
    second, created_second = store.create_notification(
        Notification("c1", NotificationType.REPORT, "user", Channel.TEAMS, {}, "stable-key")
    )
    assert created_first is True
    assert created_second is False
    assert first.notification_id == second.notification_id


def test_compare_and_set_has_one_winner() -> None:
    store = InMemoryDeliveryStore()
    decision = store.create_decision(
        Decision("c1", ActionType.REVIEW_PR, "pr:1", {}, utcnow() + timedelta(hours=1))
    )
    approved, first_changed = store.compare_and_set_decision(
        decision.decision_id, DecisionStatus.PENDING, DecisionStatus.APPROVED, "actor-1"
    )
    repeated, second_changed = store.compare_and_set_decision(
        decision.decision_id, DecisionStatus.PENDING, DecisionStatus.APPROVED, "actor-1"
    )
    assert first_changed is True
    assert second_changed is False
    assert approved.status == repeated.status == DecisionStatus.APPROVED


def test_notification_claim_has_one_winner() -> None:
    store = InMemoryDeliveryStore()
    item, _ = store.create_notification(
        Notification("c1", NotificationType.REPORT, "user", Channel.TEAMS, {}, "claim-key")
    )
    assert store.claim_notification(item.notification_id) is not None
    assert store.claim_notification(item.notification_id) is None
