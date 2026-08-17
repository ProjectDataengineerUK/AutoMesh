from __future__ import annotations

from collections.abc import Callable

from pipelines.delivery.common.cards import render_card
from pipelines.delivery.common.models import Notification, NotificationStatus
from pipelines.delivery.common.storage import InMemoryDeliveryStore
from pipelines.delivery.common.teams_client import TeamsDeliveryError


def dispatch_one(
    store: InMemoryDeliveryStore,
    notification_id: str,
    send_teams: Callable[[dict], str],
    send_outlook: Callable[[str, str, str], None],
    max_attempts: int = 3,
) -> Notification:
    item = store.get_notification(notification_id)
    if item.status == NotificationStatus.DELIVERED:
        return item

    claimed = store.claim_notification(notification_id)
    if claimed is None:
        return store.get_notification(notification_id)
    item = claimed

    decision = store.get_decision(item.decision_id) if item.decision_id else None

    try:
        item.external_message_id = send_teams(render_card(item, decision))
        item.status = NotificationStatus.DELIVERED
    except TeamsDeliveryError as exc:
        if exc.retryable and item.attempt_count < max_attempts:
            item.status = NotificationStatus.RETRYABLE
        else:
            item.status = NotificationStatus.FAILED
            store.save_notification(item)
            send_outlook(
                item.recipient_ref,
                item.payload.get("title", "AutoMesh notification"),
                item.payload.get("summary", "Delivery through Teams failed."),
            )
    store.save_notification(item)
    return item


def run(
    store: InMemoryDeliveryStore,
    send_teams: Callable[[dict], str],
    send_outlook: Callable[[str, str, str], None],
) -> list[Notification]:
    return [dispatch_one(store, item.notification_id, send_teams, send_outlook) for item in store.list_dispatchable()]
