from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from airflow.providers.apache.kafka.sensors.kafka import AwaitMessageSensor

from pipelines.ingestion.common.bronze_writer import write_bronze, write_dlq
from pipelines.ingestion.common.contract_validator import validate_batch
from pipelines.ingestion.common.kafka_config import consume_batch

SOURCE = "b3_quotes"
TOPIC = "automesh.market.b3_quotes.v1"

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


@dag(
    dag_id="dag_ingest_kafka_market",
    schedule="*/5 * * * *",
    start_date=datetime(2026, 7, 31, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["ingestion", "kafka", "fase1"],
)
def dag_ingest_kafka_market():
    wait_for_messages = AwaitMessageSensor(
        task_id="wait_for_b3_quotes",
        kafka_config_id="kafka_default",
        topics=[TOPIC],
        apply_function="pipelines.ingestion.common.kafka_config.has_messages",
        commit_offset=False,
        poll_timeout=30,
        poll_interval=15,
    )

    @task
    def consume_microbatch() -> list[dict]:
        return consume_batch(topic=TOPIC, max_messages=500)

    @task
    def validate_and_promote(records: list[dict]) -> None:
        valid, invalid = validate_batch(source=SOURCE, records=records)
        if valid:
            write_bronze(source=SOURCE, records=valid)
        if invalid:
            write_dlq(source=SOURCE, records=invalid)

    consumed = consume_microbatch()
    wait_for_messages >> consumed
    validate_and_promote(consumed)


dag_ingest_kafka_market()
