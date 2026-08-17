from __future__ import annotations

import os

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

DELTA_CURSOR_TABLE_PATH = os.environ.get("RAG_DELTA_CURSOR_PATH", "data/rag/sharepoint_delta_cursor")


def _table_exists(path: str) -> bool:
    return os.path.isdir(os.path.join(path, "_delta_log"))


def get_delta_link(source: str) -> str | None:
    if not _table_exists(DELTA_CURSOR_TABLE_PATH):
        return None

    rows = DeltaTable(DELTA_CURSOR_TABLE_PATH).to_pyarrow_table().to_pylist()
    return next((row["delta_link"] for row in rows if row["source"] == source), None)


def set_delta_link(source: str, delta_link: str) -> None:
    existing: list[dict] = []
    if _table_exists(DELTA_CURSOR_TABLE_PATH):
        existing = [
            row
            for row in DeltaTable(DELTA_CURSOR_TABLE_PATH).to_pyarrow_table().to_pylist()
            if row["source"] != source
        ]

    existing.append({"source": source, "delta_link": delta_link})
    table = pa.Table.from_pylist(existing)
    write_deltalake(DELTA_CURSOR_TABLE_PATH, table, mode="overwrite")
