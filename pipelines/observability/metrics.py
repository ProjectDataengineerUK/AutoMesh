"""Bounded in-process metrics facade with optional exporters."""

from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Mapping, Protocol

ALLOWED_ATTRIBUTES = frozenset({"domain", "result", "reason_code", "source_class", "gate", "capability_id"})


class MetricExporter(Protocol):
    def emit(self, name: str, amount: float, attributes: Mapping[str, str]) -> None: ...


@dataclass(frozen=True)
class MetricPoint:
    name: str
    amount: float
    attributes: tuple[tuple[str, str], ...]


class Metrics:
    def __init__(self, exporter: MetricExporter | None = None) -> None:
        self._exporter = exporter
        self._values: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._lock = Lock()

    def counter(self, name: str, amount: float = 1, attributes: Mapping[str, str] | None = None) -> None:
        if amount < 0:
            raise ValueError("counter amount must be non-negative")
        normalized = self._normalize(attributes or {})
        with self._lock:
            self._values[(name, normalized)] += amount
        if self._exporter is not None:
            self._exporter.emit(name, amount, dict(normalized))

    def snapshot(self) -> tuple[MetricPoint, ...]:
        with self._lock:
            return tuple(MetricPoint(name, amount, attributes) for (name, attributes), amount in self._values.items())

    @staticmethod
    def _normalize(attributes: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
        unknown = set(attributes).difference(ALLOWED_ATTRIBUTES)
        if unknown:
            raise ValueError(f"unbounded metric attributes: {', '.join(sorted(unknown))}")
        return tuple(sorted((key, str(value)) for key, value in attributes.items()))
