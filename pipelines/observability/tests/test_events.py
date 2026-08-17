from pipelines.observability.context import bind_context
from pipelines.observability.events import EventEnvelope


def test_event_preserves_correlation_context() -> None:
    with bind_context(correlation_id="corr-1", event_id="event-1"):
        first = EventEnvelope.create("ingestion.accepted", "ingestion", "success")
        second = EventEnvelope.create("processing.completed", "processing", "success")
    assert first.correlation_id == second.correlation_id == "corr-1"
    assert first.event_id == second.event_id == "event-1"
    assert first.to_dict()["occurred_at"].endswith("+00:00")
