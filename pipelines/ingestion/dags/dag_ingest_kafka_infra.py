from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from airflow.providers.apache.kafka.sensors.kafka import AwaitMessageSensor

from pipelines.ingestion.common.bronze_writer import write_bronze, write_dlq
from pipelines.ingestion.common.contract_validator import validate_batch
from pipelines.ingestion.common.kafka_config import consume_batch

SOURCES = [
    {"source": "infra_telemetry", "topic": "automesh.infra.telemetry.v1"},
    {"source": "usage_logs", "topic": "automesh.infra.usage_logs.v1"},
]

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


@dag(
    dag_id="dag_ingest_kafka_infra",
    schedule="*/15 * * * *",
    start_date=datetime(2026, 7, 31, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["ingestion", "kafka", "fase1"],
)
def dag_ingest_kafka_infra():
    wait_for_infra_topics = AwaitMessageSensor(
        task_id="wait_for_infra_topics",
        kafka_config_id="kafka_default",
        topics=[source["topic"] for source in SOURCES],
        apply_function="pipelines.ingestion.common.kafka_config.has_messages",
        commit_offset=False,
        poll_timeout=30,
        poll_interval=15,
    )

    @task
    def consume_microbatch(source_config: dict) -> dict:
        records = consume_batch(topic=source_config["topic"], max_messages=500)
        return {"source": source_config["source"], "records": records}

    @task
    def validate_and_promote(batch: dict) -> None:
        valid, invalid = validate_batch(source=batch["source"], records=batch["records"])
        if valid:
            write_bronze(source=batch["source"], records=valid)
        if invalid:
            write_dlq(source=batch["source"], records=invalid)

    batches = consume_microbatch.expand(source_config=SOURCES)
    wait_for_infra_topics >> batches
    validate_and_promote.expand(batch=batches)


dag_ingest_kafka_infra()
