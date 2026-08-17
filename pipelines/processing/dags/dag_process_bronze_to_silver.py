from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

DATABRICKS_JOB_ID = os.environ.get("DATABRICKS_JOB_ID", "")

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}


@dag(
    dag_id="dag_process_bronze_to_silver",
    schedule="@hourly",
    start_date=datetime(2026, 8, 3, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["processing", "databricks", "fase2"],
)
def dag_process_bronze_to_silver():
    DatabricksRunNowOperator(
        task_id="run_bronze_to_silver_job",
        databricks_conn_id="databricks_default",
        job_id=DATABRICKS_JOB_ID,
        deferrable=True,
    )


dag_process_bronze_to_silver()
