from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task

from pipelines.rag.jobs.content_factory import run as content_run

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


@dag(
    dag_id="dag_generate_content",
    schedule="@hourly",
    start_date=datetime(2026, 8, 10, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["rag", "content-factory", "fase4"],
)
def dag_generate_content():
    @task
    def generate() -> list[str]:
        return content_run()

    generate()


dag_generate_content()
