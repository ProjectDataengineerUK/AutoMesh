from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

PRODUCER_CONFIG = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "enable.idempotence": True,
    "acks": "all",
    "retries": 5,
    "max.in.flight.requests.per.connection": 5,
    "compression.type": "zstd",
    "linger.ms": 10,
}

CONSUMER_GROUP_ID = os.environ.get("KAFKA_CONSUMER_GROUP_ID", "automesh-fase1-ingestion")


def build_consumer_config(group_id: str = CONSUMER_GROUP_ID) -> dict:
    return {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "max.poll.interval.ms": 300000,
        "session.timeout.ms": 45000,
    }


def consume_batch(topic: str, max_messages: int = 500, timeout_seconds: float = 5.0) -> list[dict]:
    from confluent_kafka import Consumer, KafkaError

    consumer = Consumer(build_consumer_config())
    consumer.subscribe([topic])

    records: list[dict] = []
    try:
        while len(records) < max_messages:
            msg = consumer.poll(timeout=timeout_seconds)
            if msg is None:
                break
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    break
                logger.error("Consumer error on %s: %s", topic, msg.error())
                break

            try:
                records.append(json.loads(msg.value().decode("utf-8")))
                consumer.commit(message=msg, asynchronous=False)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error("Malformed message on %s: %s", topic, e)
                consumer.commit(message=msg, asynchronous=False)
    finally:
        consumer.close()

    return records


def has_messages(message) -> bool:
    return True
