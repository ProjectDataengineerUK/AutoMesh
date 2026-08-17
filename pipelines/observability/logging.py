"""Structured JSON logging with recursive sensitive-field redaction."""

import json
import logging
import re
from typing import Any

from pipelines.observability.context import current_context

SENSITIVE_KEYS = re.compile(r"(authorization|cookie|password|secret|token|api[_-]?key|email)", re.IGNORECASE)
BEARER_VALUE = re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE)


def redact(value: Any, key: str = "") -> Any:
    if SENSITIVE_KEYS.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {item_key: redact(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return BEARER_VALUE.sub("Bearer [REDACTED]", value)
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **current_context(),
        }
        extra = getattr(record, "attributes", None)
        if extra is not None:
            payload["attributes"] = extra
        return json.dumps(redact(payload), separators=(",", ":"), sort_keys=True)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
