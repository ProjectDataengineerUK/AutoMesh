from __future__ import annotations

from pipelines.delivery.common.idempotency import notification_key


def test_notification_key_is_stable_and_sensitive_to_version() -> None:
    first = notification_key("report", "r1", "v1", "user", "teams")
    assert first == notification_key("report", "r1", "v1", "user", "teams")
    assert first != notification_key("report", "r1", "v2", "user", "teams")
