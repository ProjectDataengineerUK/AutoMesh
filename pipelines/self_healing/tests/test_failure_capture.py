from __future__ import annotations

import importlib
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def failure_capture_module(tmp_path, monkeypatch):
    monkeypatch.setenv("SELF_HEALING_EVENTS_PATH", str(tmp_path / "self_healing_events"))

    from pipelines.self_healing.common import failure_capture as module

    return importlib.reload(module)


def test_write_event_defaults_to_execution_type(failure_capture_module, tmp_path) -> None:
    event_id = failure_capture_module.write_event(source="dag_x", detail="boom")

    from deltalake import DeltaTable

    rows = DeltaTable(str(tmp_path / "self_healing_events")).to_pyarrow_table().to_pylist()

    assert len(rows) == 1
    assert rows[0]["event_id"] == event_id
    assert rows[0]["source_failure_type"] == "execution"


def test_write_event_accepts_custom_failure_type(failure_capture_module, tmp_path) -> None:
    failure_capture_module.write_event(
        source="dag_generate_insights", detail="drift", source_failure_type="model_promotion"
    )

    from deltalake import DeltaTable

    rows = DeltaTable(str(tmp_path / "self_healing_events")).to_pyarrow_table().to_pylist()

    assert rows[0]["source_failure_type"] == "model_promotion"


def test_on_task_failure_still_uses_execution_type(failure_capture_module, tmp_path) -> None:
    context = {
        "dag": MagicMock(dag_id="dag_x"),
        "task_instance": MagicMock(task_id="task_y"),
        "exception": "boom",
    }

    failure_capture_module.on_task_failure(context)

    from deltalake import DeltaTable

    rows = DeltaTable(str(tmp_path / "self_healing_events")).to_pyarrow_table().to_pylist()

    assert rows[0]["source_failure_type"] == "execution"
