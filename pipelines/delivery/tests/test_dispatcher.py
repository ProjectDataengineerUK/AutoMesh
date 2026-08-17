from __future__ import annotations

from unittest.mock import Mock

from pipelines.delivery.common.models import Channel, Notification, NotificationStatus, NotificationType
from pipelines.delivery.common.storage import InMemoryDeliveryStore
from pipelines.delivery.common.teams_client import TeamsDeliveryError
from pipelines.delivery.jobs.dispatcher import dispatch_one


def _store_with_notification() -> tuple[InMemoryDeliveryStore, Notification]:
    store = InMemoryDeliveryStore()
    item, _ = store.create_notification(
        Notification("c1", NotificationType.REPORT, "user@example.test", Channel.TEAMS, {}, "key")
    )
    return store, item


def test_successful_delivery_is_not_sent_twice() -> None:
    store, item = _store_with_notification()
    teams = Mock(return_value="activity-1")
    outlook = Mock()
    result = dispatch_one(store, item.notification_id, teams, outlook)
    repeated = dispatch_one(store, item.notification_id, teams, outlook)
    assert result.status == repeated.status == NotificationStatus.DELIVERED
    teams.assert_called_once()
    outlook.assert_not_called()


def test_transient_failure_retries_before_fallback() -> None:
    store, item = _store_with_notification()
    teams = Mock(side_effect=TeamsDeliveryError("temporary", retryable=True))
    outlook = Mock()
    result = dispatch_one(store, item.notification_id, teams, outlook, max_attempts=3)
    assert result.status == NotificationStatus.RETRYABLE
    outlook.assert_not_called()


def test_permanent_failure_uses_outlook_fallback() -> None:
    store, item = _store_with_notification()
    teams = Mock(side_effect=TeamsDeliveryError("forbidden", retryable=False))
    outlook = Mock()
    result = dispatch_one(store, item.notification_id, teams, outlook)
    assert result.status == NotificationStatus.FAILED
    outlook.assert_called_once()
