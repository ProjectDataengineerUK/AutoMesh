from pipelines.observability.context import bind_context, current_context


def test_context_is_nested_and_restored() -> None:
    assert current_context() == {}
    with bind_context(correlation_id="corr-1"):
        assert current_context() == {"correlation_id": "corr-1"}
        with bind_context(event_id="event-1"):
            assert current_context() == {"correlation_id": "corr-1", "event_id": "event-1"}
        assert current_context() == {"correlation_id": "corr-1"}
    assert current_context() == {}
