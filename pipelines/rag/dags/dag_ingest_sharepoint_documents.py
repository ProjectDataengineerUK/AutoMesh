from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task

from pipelines.rag.jobs.ingest_sharepoint import run as ingest_run

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


@dag(
    dag_id="dag_ingest_sharepoint_documents",
    schedule="*/30 * * * *",
    start_date=datetime(2026, 8, 10, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["rag", "sharepoint", "fase4"],
)
def dag_ingest_sharepoint_documents():
    @task
    def ingest() -> dict:
        return ingest_run()

    ingest()


dag_ingest_sharepoint_documents()
