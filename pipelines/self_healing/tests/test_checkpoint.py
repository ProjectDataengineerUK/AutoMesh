from __future__ import annotations

import importlib
from datetime import datetime, timezone

import pytest


@pytest.fixture
def checkpoint_module(tmp_path, monkeypatch):
    monkeypatch.setenv("SELF_HEALING_CHECKPOINT_PATH", str(tmp_path / "checkpoint"))

    from pipelines.self_healing.common import checkpoint as module

    return importlib.reload(module)


def test_get_checkpoint_defaults_to_epoch_when_missing(checkpoint_module) -> None:
    result = checkpoint_module.get_checkpoint("bronze_dlq")

    assert result == checkpoint_module.EPOCH


def test_set_then_get_round_trips(checkpoint_module) -> None:
    now = datetime.now(timezone.utc)

    checkpoint_module.set_checkpoint("bronze_dlq", now)

    assert checkpoint_module.get_checkpoint("bronze_dlq") == now


def test_sources_are_isolated(checkpoint_module) -> None:
    now = datetime.now(timezone.utc)

    checkpoint_module.set_checkpoint("bronze_dlq", now)

    assert checkpoint_module.get_checkpoint("self_healing_events") == checkpoint_module.EPOCH


def test_set_overwrites_previous_value_for_same_source(checkpoint_module) -> None:
    first = datetime(2026, 1, 1, tzinfo=timezone.utc)
    second = datetime(2026, 6, 1, tzinfo=timezone.utc)

    checkpoint_module.set_checkpoint("bronze_dlq", first)
    checkpoint_module.set_checkpoint("bronze_dlq", second)

    assert checkpoint_module.get_checkpoint("bronze_dlq") == second


def test_latest_timestamp_uses_processed_record_watermark() -> None:
    from pipelines.self_healing.common.checkpoint import latest_timestamp

    result = latest_timestamp(
        [
            {"detected_at": "2026-08-14T10:00:00+00:00"},
            {"detected_at": "2026-08-14T10:05:00+00:00"},
        ],
        "detected_at",
    )

    assert result == datetime(2026, 8, 14, 10, 5, tzinfo=timezone.utc)


def test_latest_timestamp_rejects_empty_batch() -> None:
    from pipelines.self_healing.common.checkpoint import latest_timestamp

    with pytest.raises(ValueError, match="must not be empty"):
        latest_timestamp([], "detected_at")
