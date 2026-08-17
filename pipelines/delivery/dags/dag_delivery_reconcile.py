from __future__ import annotations

from datetime import datetime, timezone

from airflow.decorators import dag, task

from pipelines.delivery.common.runtime import get_store
from pipelines.delivery.jobs.reconciler import expire_decisions


@dag(
    dag_id="dag_delivery_reconcile",
    schedule="*/15 * * * *",
    start_date=datetime(2026, 8, 14, tzinfo=timezone.utc),
    catchup=False,
    tags=["delivery", "reconciliation", "fase5"],
)
def dag_delivery_reconcile():
    @task
    def reconcile() -> int:
        return expire_decisions(get_store())

    reconcile()


dag_delivery_reconcile()
