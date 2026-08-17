from __future__ import annotations

from datetime import datetime, timezone

from airflow.decorators import dag, task

from pipelines.delivery.common.runtime import get_store
from pipelines.delivery.jobs.applications import MLflowRegistry, run_pending


@dag(
    dag_id="dag_delivery_apply",
    schedule="*/5 * * * *",
    start_date=datetime(2026, 8, 14, tzinfo=timezone.utc),
    catchup=False,
    tags=["delivery", "hitl", "mlflow", "fase5"],
)
def dag_delivery_apply():
    @task
    def apply_pending() -> int:
        return len(run_pending(get_store(), MLflowRegistry()))

    apply_pending()


dag_delivery_apply()
