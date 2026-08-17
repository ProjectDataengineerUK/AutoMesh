from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer

from pipelines.ingestion.common.kafka_config import PRODUCER_CONFIG

logger = logging.getLogger(__name__)

TELEMETRY_TOPIC = "automesh.infra.telemetry.v1"
USAGE_LOGS_TOPIC = "automesh.infra.usage_logs.v1"

HOST_IDS = [f"cluster-node-{i:02d}" for i in range(1, 6)]
METRIC_NAMES = ["cpu_utilization_pct", "memory_utilization_pct", "job_queue_depth"]
ACTIONS = ["dashboard_view", "query_run", "export_report", "login"]
RESOURCES = ["lakeview_dashboard", "bronze_table", "silver_table", "gold_table"]


def _on_delivery(err, msg) -> None:
    if err:
        logger.error("Delivery failed: %s", err)


def generate_telemetry_batch(count: int = 20) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "host_id": random.choice(HOST_IDS),
            "metric_name": random.choice(METRIC_NAMES),
            "metric_value": round(random.uniform(5.0, 95.0), 2),
            "collected_at": now,
        }
        for _ in range(count)
    ]


def generate_usage_logs_batch(count: int = 20) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "user_id": f"user-{uuid.uuid4().hex[:8]}",
            "action": random.choice(ACTIONS),
            "resource": random.choice(RESOURCES),
            "occurred_at": now,
        }
        for _ in range(count)
    ]


def publish_batch(topic: str, records: list[dict], producer: Producer | None = None) -> int:
    producer = producer or Producer(PRODUCER_CONFIG)
    for record in records:
        producer.produce(
            topic=topic,
            key=record.get("host_id", record.get("user_id", "")).encode("utf-8"),
            value=json.dumps(record).encode("utf-8"),
            on_delivery=_on_delivery,
        )
    producer.flush()
    return len(records)


def run() -> tuple[int, int]:
    producer = Producer(PRODUCER_CONFIG)
    telemetry_count = publish_batch(TELEMETRY_TOPIC, generate_telemetry_batch(), producer)
    logs_count = publish_batch(USAGE_LOGS_TOPIC, generate_usage_logs_batch(), producer)
    return telemetry_count, logs_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
