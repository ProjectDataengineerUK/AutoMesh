"""Versioned metric calculations shared by local and SQL builds."""

from collections import defaultdict
from collections.abc import Iterable
from typing import Any


def sum_by(rows: Iterable[dict[str, Any]], group: tuple[str, ...], value: str) -> list[dict[str, Any]]:
    totals: dict[tuple[Any, ...], float] = defaultdict(float)
    for row in rows:
        totals[tuple(row[column] for column in group)] += float(row[value])
    return [dict(zip(group, key, strict=True), **{value: total}) for key, total in totals.items()]


def count_by(rows: Iterable[dict[str, Any]], group: tuple[str, ...]) -> list[dict[str, Any]]:
    counts: dict[tuple[Any, ...], int] = defaultdict(int)
    for row in rows:
        counts[tuple(row[column] for column in group)] += 1
    return [dict(zip(group, key, strict=True), metric_count=count) for key, count in counts.items()]
