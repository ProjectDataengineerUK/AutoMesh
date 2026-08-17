from __future__ import annotations

from pipelines.delivery.common.storage import InMemoryDeliveryStore
from pipelines.delivery.jobs.source_adapters import enqueue_pr_result


def _result(status: str = "pr_opened") -> dict:
    return {
        "status": status,
        "pr_url": "https://github.example/automesh/pull/42",
        "event": {"event_id": "event-42"},
        "diagnosis": {
            "root_cause": "schema drift",
            "target_file": "pipelines/ingestion/contracts/source.contract.yaml",
            "explanation": "A source column changed.",
        },
    }


def test_pr_result_is_enqueued_idempotently() -> None:
    store = InMemoryDeliveryStore()
    first, first_created = enqueue_pr_result(store, _result(), "reviewer@example.test")
    second, second_created = enqueue_pr_result(store, _result(), "reviewer@example.test")
    assert first_created is True
    assert second_created is False
    assert first is not None and second is not None
    assert first.notification_id == second.notification_id
    assert first.payload["url"].endswith("/42")


def test_rejected_result_is_not_enqueued() -> None:
    notification, created = enqueue_pr_result(
        InMemoryDeliveryStore(), {"status": "rejected"}, "reviewer@example.test"
    )
    assert notification is None
    assert created is False
