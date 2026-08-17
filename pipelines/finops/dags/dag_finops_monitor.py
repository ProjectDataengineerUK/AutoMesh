from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task

from pipelines.finops.jobs.cost_monitor import run as cost_monitor_run

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


@dag(
    dag_id="dag_finops_monitor",
    schedule="@hourly",
    start_date=datetime(2026, 8, 5, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["finops", "fase3"],
)
def dag_finops_monitor():
    @task
    def monitor() -> int:
        return cost_monitor_run()

    monitor()


dag_finops_monitor()
