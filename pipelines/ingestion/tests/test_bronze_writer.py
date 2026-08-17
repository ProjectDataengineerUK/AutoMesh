from __future__ import annotations

import importlib

import pytest
from deltalake import DeltaTable


@pytest.fixture
def bronze_writer(tmp_path, monkeypatch):
    monkeypatch.setenv("BRONZE_BASE_PATH", str(tmp_path / "bronze"))
    monkeypatch.setenv("DLQ_TABLE_PATH", str(tmp_path / "bronze" / "_dlq" / "bronze_dlq"))

    from pipelines.ingestion.common import bronze_writer as module

    return importlib.reload(module)


def test_write_bronze_creates_delta_table(bronze_writer, tmp_path) -> None:
    records = [{"ticker": "PETR4", "price": 38.5, "quote_timestamp": "2026-07-31T10:00:00Z"}]

    written = bronze_writer.write_bronze("b3_quotes", records)

    table_path = tmp_path / "bronze" / "b3_quotes"
    dt = DeltaTable(str(table_path))
    rows = dt.to_pyarrow_table().to_pylist()

    assert written == 1
    assert len(rows) == 1
    assert rows[0]["ticker"] == "PETR4"
    assert "ingestion_date" in rows[0]


def test_write_bronze_empty_batch_is_noop(bronze_writer, tmp_path) -> None:
    written = bronze_writer.write_bronze("b3_quotes", [])

    assert written == 0
    assert not (tmp_path / "bronze" / "b3_quotes").exists()


def test_write_dlq_attaches_source_and_reason(bronze_writer, tmp_path) -> None:
    records = [{"ticker": None, "price": 38.5, "_failure_reason": "null_violation:ticker"}]

    written = bronze_writer.write_dlq("b3_quotes", records)

    dt = DeltaTable(str(tmp_path / "bronze" / "_dlq" / "bronze_dlq"))
    rows = dt.to_pyarrow_table().to_pylist()

    assert written == 1
    assert rows[0]["source"] == "b3_quotes"
    assert rows[0]["_failure_reason"] == "null_violation:ticker"


def test_write_bronze_appends_across_calls(bronze_writer, tmp_path) -> None:
    bronze_writer.write_bronze("b3_quotes", [{"ticker": "PETR4", "price": 38.5, "quote_timestamp": "t1"}])
    bronze_writer.write_bronze("b3_quotes", [{"ticker": "VALE3", "price": 65.2, "quote_timestamp": "t2"}])

    dt = DeltaTable(str(tmp_path / "bronze" / "b3_quotes"))
    rows = dt.to_pyarrow_table().to_pylist()

    assert len(rows) == 2
