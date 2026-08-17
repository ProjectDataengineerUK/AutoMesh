from pipelines.delivery.common.idempotency import notification_key


def test_replayed_event_has_one_logical_key() -> None:
    keys = {notification_key("alert", "resource", "1", "recipient", "teams") for _ in range(10)}
    assert len(keys) == 1
