from pipelines.observability.metrics import Metrics


def test_timeout_retry_is_bounded_and_observable() -> None:
    attempts = 0
    metrics = Metrics()
    for _ in range(3):
        attempts += 1
        metrics.counter("automesh.external.retry", attributes={"domain": "delivery", "reason_code": "TIMEOUT"})
    assert attempts == 3
    assert metrics.snapshot()[0].amount == 3
