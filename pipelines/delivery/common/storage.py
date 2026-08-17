from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import Lock

from pipelines.delivery.common.models import (
    Application,
    ApplicationStatus,
    Decision,
    DecisionStatus,
    Notification,
    NotificationStatus,
    utcnow,
)


class InvalidTransition(ValueError):
    pass


class InMemoryDeliveryStore:
    """Reference store for unit/local execution; production must use transactional CAS."""

    def __init__(self) -> None:
        self._notifications: dict[str, Notification] = {}
        self._notification_keys: dict[str, str] = {}
        self._decisions: dict[str, Decision] = {}
        self._applications: dict[str, Application] = {}
        self._lock = Lock()

    def create_notification(self, notification: Notification) -> tuple[Notification, bool]:
        with self._lock:
            existing_id = self._notification_keys.get(notification.idempotency_key)
            if existing_id:
                return deepcopy(self._notifications[existing_id]), False
            self._notifications[notification.notification_id] = deepcopy(notification)
            self._notification_keys[notification.idempotency_key] = notification.notification_id
            return deepcopy(notification), True

    def get_notification(self, notification_id: str) -> Notification:
        return deepcopy(self._notifications[notification_id])

    def get_notification_by_key(self, idempotency_key: str) -> Notification | None:
        notification_id = self._notification_keys.get(idempotency_key)
        return self.get_notification(notification_id) if notification_id else None

    def list_dispatchable(self) -> list[Notification]:
        return [
            deepcopy(item)
            for item in self._notifications.values()
            if item.status in {NotificationStatus.PENDING, NotificationStatus.RETRYABLE}
        ]

    def claim_notification(self, notification_id: str) -> Notification | None:
        with self._lock:
            item = self._notifications[notification_id]
            if item.status not in {NotificationStatus.PENDING, NotificationStatus.RETRYABLE}:
                return None
            item.status = NotificationStatus.DELIVERING
            item.attempt_count += 1
            item.updated_at = utcnow()
            return deepcopy(item)

    def save_notification(self, notification: Notification) -> None:
        notification.updated_at = utcnow()
        self._notifications[notification.notification_id] = deepcopy(notification)

    def create_decision(self, decision: Decision) -> Decision:
        with self._lock:
            self._decisions.setdefault(decision.decision_id, deepcopy(decision))
            return deepcopy(self._decisions[decision.decision_id])

    def get_decision(self, decision_id: str) -> Decision:
        return deepcopy(self._decisions[decision_id])

    def compare_and_set_decision(
        self,
        decision_id: str,
        expected: DecisionStatus,
        target: DecisionStatus,
        actor_id: str,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> tuple[Decision, bool]:
        allowed = {
            DecisionStatus.PENDING: {
                DecisionStatus.APPROVED,
                DecisionStatus.REJECTED,
                DecisionStatus.EXPIRED,
            }
        }
        with self._lock:
            decision = self._decisions[decision_id]
            if decision.status != expected:
                return deepcopy(decision), False
            if target not in allowed.get(expected, set()):
                raise InvalidTransition(f"{expected.value}->{target.value}")
            decision.status = target
            decision.actor_id = actor_id
            decision.reason = reason
            decision.decided_at = now or utcnow()
            decision.revision += 1
            return deepcopy(decision), True

    def list_pending_decisions(self) -> list[Decision]:
        return [deepcopy(item) for item in self._decisions.values() if item.status == DecisionStatus.PENDING]

    def create_application(self, application: Application) -> tuple[Application, bool]:
        with self._lock:
            existing = next(
                (item for item in self._applications.values() if item.decision_id == application.decision_id),
                None,
            )
            if existing:
                return deepcopy(existing), False
            self._applications[application.application_id] = deepcopy(application)
            return deepcopy(application), True

    def get_application(self, application_id: str) -> Application:
        return deepcopy(self._applications[application_id])

    def list_pending_applications(self) -> list[Application]:
        return [
            deepcopy(item)
            for item in self._applications.values()
            if item.status == ApplicationStatus.PENDING
        ]

    def save_application(self, application: Application) -> None:
        self._applications[application.application_id] = deepcopy(application)
