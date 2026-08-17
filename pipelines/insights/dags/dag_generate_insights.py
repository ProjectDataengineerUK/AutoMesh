from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

from pipelines.insights.jobs.drift_check import run as drift_run
from pipelines.insights.jobs.generate_insights import run as insights_run

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


@dag(
    dag_id="dag_generate_insights",
    schedule="@hourly",
    start_date=datetime(2026, 8, 5, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["insights", "ml", "fase3"],
)
def dag_generate_insights():
    @task
    def generate() -> int:
        return insights_run()

    @task
    def check_drift() -> dict:
        return drift_run()

    @task.branch
    def decide_retrain(drift_result: dict) -> str:
        return "trigger_retrain" if drift_result["drifted"] else "skip_retrain"

    @task
    def skip_retrain() -> None:
        return None

    trigger_retrain = TriggerDagRunOperator(
        task_id="trigger_retrain",
        trigger_dag_id="dag_train_outlier_model",
    )

    generated = generate()
    drift_result = check_drift()
    branch = decide_retrain(drift_result)
    skipped = skip_retrain()

    generated >> drift_result
    drift_result >> branch >> [trigger_retrain, skipped]


dag_generate_insights()
