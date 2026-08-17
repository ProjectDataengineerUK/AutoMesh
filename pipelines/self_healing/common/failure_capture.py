from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

import pyarrow as pa
from deltalake import write_deltalake

logger = logging.getLogger(__name__)

EVENTS_TABLE_PATH = os.environ.get("SELF_HEALING_EVENTS_PATH", "data/self_healing/self_healing_events")


def write_event(source: str, detail: str, source_failure_type: str = "execution") -> str:
    event_id = str(uuid.uuid4())
    record = {
        "event_id": event_id,
        "source_failure_type": source_failure_type,
        "source": source,
        "detail": detail,
        "detected_at": datetime.now(timezone.utc),
    }
    table = pa.Table.from_pylist([record])
    write_deltalake(EVENTS_TABLE_PATH, table, mode="append")
    return event_id


def on_task_failure(context: dict) -> None:
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    exception = context.get("exception", "unknown error")
    detail = f"DAG={dag_id} task={task_id} exception={exception}"

    try:
        event_id = write_event(source=dag_id, detail=detail)
        logger.info("Recorded execution failure as self-healing event %s", event_id)
    except Exception as e:  # noqa: BLE001 — must never break Airflow's failure handling
        logger.error("Failed to record self-healing event: %s", e)
