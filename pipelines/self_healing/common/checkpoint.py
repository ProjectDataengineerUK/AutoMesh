from __future__ import annotations

import os
from datetime import datetime, timezone

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

CHECKPOINT_TABLE_PATH = os.environ.get(
    "SELF_HEALING_CHECKPOINT_PATH", "data/self_healing/self_healing_checkpoint"
)

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def latest_timestamp(records: list[dict], field: str) -> datetime:
    if not records:
        raise ValueError("records must not be empty")

    values = []
    for record in records:
        value = record[field]
        values.append(datetime.fromisoformat(value) if isinstance(value, str) else value)
    return max(values)


def _table_exists(path: str) -> bool:
    return os.path.isdir(os.path.join(path, "_delta_log"))


def get_checkpoint(source: str) -> datetime:
    if not _table_exists(CHECKPOINT_TABLE_PATH):
        return EPOCH

    rows = DeltaTable(CHECKPOINT_TABLE_PATH).to_pyarrow_table().to_pylist()
    for row in rows:
        if row["source"] == source:
            return row["last_processed_at"]
    return EPOCH


def set_checkpoint(source: str, timestamp: datetime) -> None:
    existing: list[dict] = []
    if _table_exists(CHECKPOINT_TABLE_PATH):
        existing = [
            row
            for row in DeltaTable(CHECKPOINT_TABLE_PATH).to_pyarrow_table().to_pylist()
            if row["source"] != source
        ]

    existing.append({"source": source, "last_processed_at": timestamp})
    table = pa.Table.from_pylist(existing)
    write_deltalake(CHECKPOINT_TABLE_PATH, table, mode="overwrite")
