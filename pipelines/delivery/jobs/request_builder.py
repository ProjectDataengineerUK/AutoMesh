from __future__ import annotations

from datetime import timedelta

from pipelines.delivery.common.idempotency import notification_key
from pipelines.delivery.common.models import (
    ActionType,
    Channel,
    Decision,
    Notification,
    NotificationType,
    utcnow,
)
from pipelines.delivery.common.storage import InMemoryDeliveryStore

TYPE_TO_ACTION = {
    NotificationType.PR_REVIEW: ActionType.REVIEW_PR,
    NotificationType.MODEL_PROMOTION: ActionType.PROMOTE_MODEL,
    NotificationType.FINOPS: ActionType.ACK_FINOPS,
}


def enqueue(
    store: InMemoryDeliveryStore,
    *,
    notification_type: NotificationType,
    correlation_id: str,
    resource_ref: str,
    resource_version: str,
    recipient_ref: str,
    payload: dict[str, object],
    expected_state: dict[str, object] | None = None,
    decision_ttl_hours: int = 24,
) -> tuple[Notification, bool]:
    key = notification_key(
        notification_type.value,
        resource_ref,
        resource_version,
        recipient_ref,
        Channel.TEAMS.value,
    )
    if existing := store.get_notification_by_key(key):
        return existing, False

    decision = None
    if action_type := TYPE_TO_ACTION.get(notification_type):
        decision = store.create_decision(
            Decision(
                correlation_id=correlation_id,
                action_type=action_type,
                resource_ref=resource_ref,
                expected_state=expected_state or {},
                expires_at=utcnow() + timedelta(hours=decision_ttl_hours),
            )
        )

    item = Notification(
        correlation_id=correlation_id,
        notification_type=notification_type,
        recipient_ref=recipient_ref,
        channel=Channel.TEAMS,
        payload=payload,
        decision_id=decision.decision_id if decision else None,
        idempotency_key=key,
    )
    return store.create_notification(item)
