from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pyarrow as pa
from deltalake import write_deltalake

REJECTIONS_TABLE_PATH = os.environ.get(
    "SELF_HEALING_REJECTIONS_PATH", "data/self_healing/self_healing_rejections"
)


def write_rejection(source_failure_type: str, rejection_reason: str, proposed_diff: str) -> str:
    event_id = str(uuid.uuid4())
    record = {
        "event_id": event_id,
        "source_failure_type": source_failure_type,
        "rejection_reason": rejection_reason,
        "proposed_diff": proposed_diff,
        "rejected_at": datetime.now(timezone.utc),
    }
    table = pa.Table.from_pylist([record])
    write_deltalake(REJECTIONS_TABLE_PATH, table, mode="append")
    return event_id
