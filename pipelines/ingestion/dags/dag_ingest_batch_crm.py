from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from airflow.decorators import dag, task
from airflow.sdk import get_current_context

from pipelines.ingestion.common.bronze_writer import write_bronze, write_dlq
from pipelines.ingestion.common.contract_validator import validate_batch

SOURCE = "crm_lost_sales"
RAW_BASE_PATH = Path("data/raw/crm_lost_sales")

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
}


@dag(
    dag_id="dag_ingest_batch_crm",
    schedule="@daily",
    start_date=datetime(2026, 7, 31, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["ingestion", "batch", "fase1"],
)
def dag_ingest_batch_crm():
    @task
    def read_batch_file() -> list[dict]:
        ds = get_current_context()["ds"]
        target_file = RAW_BASE_PATH / ds / "lost_sales.json"
        if not target_file.exists():
            return []

        with target_file.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    @task
    def validate_and_promote(records: list[dict]) -> None:
        valid, invalid = validate_batch(source=SOURCE, records=records)
        if valid:
            write_bronze(source=SOURCE, records=valid)
        if invalid:
            write_dlq(source=SOURCE, records=invalid)

    validate_and_promote(read_batch_file())


dag_ingest_batch_crm()
