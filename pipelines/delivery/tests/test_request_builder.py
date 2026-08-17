from __future__ import annotations

from pipelines.delivery.common.models import NotificationType
from pipelines.delivery.common.storage import InMemoryDeliveryStore
from pipelines.delivery.jobs.request_builder import enqueue


def test_duplicate_request_reuses_notification_and_decision() -> None:
    store = InMemoryDeliveryStore()
    kwargs = {
        "notification_type": NotificationType.PR_REVIEW,
        "correlation_id": "event-1",
        "resource_ref": "pr:42",
        "resource_version": "sha-1",
        "recipient_ref": "reviewer",
        "payload": {"title": "Review"},
    }
    first, first_created = enqueue(store, **kwargs)
    second, second_created = enqueue(store, **kwargs)
    assert first_created is True
    assert second_created is False
    assert first.notification_id == second.notification_id
    assert first.decision_id == second.decision_id
