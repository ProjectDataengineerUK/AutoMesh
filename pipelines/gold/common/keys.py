"""Stable-key and replay-safe deduplication helpers."""

from collections.abc import Iterable
from typing import Any


def latest_by_key(records: Iterable[dict[str, Any]], keys: tuple[str, ...], watermark: str) -> list[dict[str, Any]]:
    selected: dict[tuple[Any, ...], dict[str, Any]] = {}
    for record in records:
        if any(record.get(key) is None for key in keys):
            raise ValueError("Gold business keys cannot be null")
        if record.get(watermark) is None:
            raise ValueError(f"Gold watermark cannot be null: {watermark}")
        key = tuple(record[key] for key in keys)
        previous = selected.get(key)
        if previous is None or record[watermark] > previous[watermark]:
            selected[key] = dict(record)
    return list(selected.values())


def merge_by_key(
    existing: Iterable[dict[str, Any]], incoming: Iterable[dict[str, Any]], key: str
) -> list[dict[str, Any]]:
    merged = {row[key]: dict(row) for row in existing}
    for row in incoming:
        if row.get(key) is None:
            raise ValueError("Gold business keys cannot be null")
        merged[row[key]] = dict(row)
    return list(merged.values())
