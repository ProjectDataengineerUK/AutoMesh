from __future__ import annotations

import os
from datetime import datetime, timezone

import pyarrow as pa
from deltalake import write_deltalake

BRONZE_BASE_PATH = os.environ.get("BRONZE_BASE_PATH", "data/bronze")
DLQ_TABLE_PATH = os.environ.get("DLQ_TABLE_PATH", f"{BRONZE_BASE_PATH}/_dlq/bronze_dlq")


def _current_ingestion_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _with_ingestion_date(records: list[dict]) -> list[dict]:
    ingestion_date = _current_ingestion_date()
    return [{**record, "ingestion_date": ingestion_date} for record in records]


def write_bronze(source: str, records: list[dict]) -> int:
    if not records:
        return 0

    table_path = f"{BRONZE_BASE_PATH}/{source}"
    table = pa.Table.from_pylist(_with_ingestion_date(records))
    write_deltalake(table_path, table, mode="append", partition_by=["ingestion_date"])
    return len(records)


def write_dlq(source: str, records: list[dict]) -> int:
    if not records:
        return 0

    detected_at = datetime.now(timezone.utc)
    enriched = [
        {**record, "source": source, "detected_at": detected_at}
        for record in _with_ingestion_date(records)
    ]
    table = pa.Table.from_pylist(enriched)
    write_deltalake(DLQ_TABLE_PATH, table, mode="append", partition_by=["source", "ingestion_date"])
    return len(records)
