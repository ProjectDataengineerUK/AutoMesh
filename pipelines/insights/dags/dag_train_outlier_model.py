from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task

from pipelines.insights.jobs.train_outlier_model import run as train_run

RETRY_ARGS = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}


@dag(
    dag_id="dag_train_outlier_model",
    schedule=None,
    start_date=datetime(2026, 8, 5, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["insights", "ml", "fase3"],
)
def dag_train_outlier_model():
    @task
    def train_model() -> dict:
        run_id, version = train_run()
        return {"run_id": run_id, "version": version}

    train_model()


dag_train_outlier_model()
