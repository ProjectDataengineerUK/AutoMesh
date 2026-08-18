"""Narrow adapter boundary; cloud SDK is intentionally lazy and optional."""

from __future__ import annotations


class DatabricksAdapter:
    def __init__(self, host: str, token: str | None = None):
        self.host = host
        self.token = token

    def check(self, capability: str) -> bool:
        raise RuntimeError(f"external adapter not enabled for capability: {capability}")

    def apply(self, objects: list[dict[str, str]]) -> list[dict[str, str]]:
        raise RuntimeError("external publish adapter requires an approved implementation")
