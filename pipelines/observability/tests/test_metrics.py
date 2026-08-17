import pytest

from pipelines.observability.metrics import Metrics


def test_counter_accumulates_bounded_attributes() -> None:
    metrics = Metrics()
    metrics.counter("automesh.records", 2, {"domain": "ingestion", "result": "accepted"})
    metrics.counter("automesh.records", 3, {"result": "accepted", "domain": "ingestion"})
    assert metrics.snapshot()[0].amount == 5


def test_dynamic_identifier_is_rejected() -> None:
    with pytest.raises(ValueError, match="correlation_id"):
        Metrics().counter("automesh.records", attributes={"correlation_id": "dynamic"})
