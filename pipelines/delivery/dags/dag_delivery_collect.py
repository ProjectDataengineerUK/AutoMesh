from __future__ import annotations

from datetime import datetime, timezone

from airflow.decorators import dag, task
from airflow.sdk import get_current_context

from pipelines.delivery.common.models import NotificationType
from pipelines.delivery.common.runtime import get_store
from pipelines.delivery.jobs.request_builder import enqueue


@dag(
    dag_id="dag_delivery_collect",
    schedule=None,
    start_date=datetime(2026, 8, 14, tzinfo=timezone.utc),
    catchup=False,
    tags=["delivery", "hitl", "fase5"],
)
def dag_delivery_collect():
    @task
    def collect() -> dict:
        event = get_current_context().get("params", {}).get("event")
        if not event:
            return {"created": False, "reason": "no_event"}
        _, created = enqueue(
            get_store(),
            notification_type=NotificationType(event["notification_type"]),
            correlation_id=event["correlation_id"],
            resource_ref=event["resource_ref"],
            resource_version=event["resource_version"],
            recipient_ref=event["recipient_ref"],
            payload=event["payload"],
            expected_state=event.get("expected_state"),
        )
        return {"created": created}

    collect()


dag_delivery_collect()
