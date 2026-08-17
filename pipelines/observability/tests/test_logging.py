import json
import logging

from pipelines.observability.logging import JsonFormatter, redact


def test_redaction_is_recursive() -> None:
    payload = {"token": "abc", "nested": {"password": "def"}, "message": "Bearer ghi"}
    assert redact(payload) == {
        "token": "[REDACTED]",
        "nested": {"password": "[REDACTED]"},
        "message": "Bearer [REDACTED]",
    }


def test_json_formatter_redacts_extra_attributes() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "complete", (), None)
    record.attributes = {"api_key": "secret"}
    payload = json.loads(JsonFormatter().format(record))
    assert payload["attributes"]["api_key"] == "[REDACTED]"
