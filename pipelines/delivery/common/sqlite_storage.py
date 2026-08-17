from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from pipelines.delivery.common.models import (
    ActionType,
    Application,
    ApplicationStatus,
    Channel,
    Decision,
    DecisionStatus,
    Notification,
    NotificationStatus,
    NotificationType,
)
from pipelines.delivery.common.storage import InMemoryDeliveryStore


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"unsupported value: {type(value).__name__}")


def _notification(data: dict) -> Notification:
    for field in ("created_at", "updated_at", "lease_until"):
        if data.get(field):
            data[field] = datetime.fromisoformat(data[field])
    data["notification_type"] = NotificationType(data["notification_type"])
    data["channel"] = Channel(data["channel"])
    data["status"] = NotificationStatus(data["status"])
    return Notification(**data)


def _decision(data: dict) -> Decision:
    for field in ("expires_at", "decided_at"):
        if data.get(field):
            data[field] = datetime.fromisoformat(data[field])
    data["action_type"] = ActionType(data["action_type"])
    data["status"] = DecisionStatus(data["status"])
    data["application_status"] = ApplicationStatus(data["application_status"])
    return Decision(**data)


def _application(data: dict) -> Application:
    data["action_type"] = ActionType(data["action_type"])
    data["status"] = ApplicationStatus(data["status"])
    return Application(**data)


class SQLiteDeliveryStore:
    """Transactional low-volume store used by local Airflow and the reference build."""

    def __init__(self, path: str) -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS delivery_state "
                "(id INTEGER PRIMARY KEY, state TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT OR IGNORE INTO delivery_state(id, state) VALUES (1, ?)",
                (json.dumps({"notifications": [], "decisions": [], "applications": []}),),
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    @staticmethod
    def _decode(raw: str) -> InMemoryDeliveryStore:
        state = json.loads(raw)
        store = InMemoryDeliveryStore()
        store._notifications = {item["notification_id"]: _notification(item) for item in state["notifications"]}
        store._notification_keys = {
            item.idempotency_key: item.notification_id for item in store._notifications.values()
        }
        store._decisions = {item["decision_id"]: _decision(item) for item in state["decisions"]}
        store._applications = {item["application_id"]: _application(item) for item in state["applications"]}
        return store

    @staticmethod
    def _encode(store: InMemoryDeliveryStore) -> str:
        return json.dumps(
            {
                "notifications": [asdict(item) for item in store._notifications.values()],
                "decisions": [asdict(item) for item in store._decisions.values()],
                "applications": [asdict(item) for item in store._applications.values()],
            },
            default=_json_default,
        )

    def _read(self) -> InMemoryDeliveryStore:
        with self._connect() as connection:
            raw = connection.execute("SELECT state FROM delivery_state WHERE id = 1").fetchone()[0]
        return self._decode(raw)

    def _mutate(self, method: str, *args, **kwargs):
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            raw = connection.execute("SELECT state FROM delivery_state WHERE id = 1").fetchone()[0]
            store = self._decode(raw)
            result = getattr(store, method)(*args, **kwargs)
            connection.execute("UPDATE delivery_state SET state = ? WHERE id = 1", (self._encode(store),))
            connection.commit()
            return result

    def create_notification(self, notification: Notification):
        return self._mutate("create_notification", notification)

    def get_notification(self, notification_id: str) -> Notification:
        return self._read().get_notification(notification_id)

    def get_notification_by_key(self, idempotency_key: str) -> Notification | None:
        return self._read().get_notification_by_key(idempotency_key)

    def list_dispatchable(self) -> list[Notification]:
        return self._read().list_dispatchable()

    def claim_notification(self, notification_id: str) -> Notification | None:
        return self._mutate("claim_notification", notification_id)

    def save_notification(self, notification: Notification) -> None:
        self._mutate("save_notification", notification)

    def create_decision(self, decision: Decision) -> Decision:
        return self._mutate("create_decision", decision)

    def get_decision(self, decision_id: str) -> Decision:
        return self._read().get_decision(decision_id)

    def compare_and_set_decision(
        self,
        decision_id: str,
        expected: DecisionStatus,
        target: DecisionStatus,
        actor_id: str,
        **kwargs,
    ):
        return self._mutate(
            "compare_and_set_decision", decision_id, expected, target, actor_id, **kwargs
        )

    def list_pending_decisions(self) -> list[Decision]:
        return self._read().list_pending_decisions()

    def create_application(self, application: Application):
        return self._mutate("create_application", application)

    def get_application(self, application_id: str) -> Application:
        return self._read().get_application(application_id)

    def list_pending_applications(self) -> list[Application]:
        return self._read().list_pending_applications()

    def save_application(self, application: Application) -> None:
        self._mutate("save_application", application)
