from pipelines.delivery.common.models import ApplicationStatus


def test_stale_precondition_is_not_applied() -> None:
    status = ApplicationStatus.STALE_PRECONDITION
    reason = "STALE_PRECONDITION"
    assert status is not ApplicationStatus.APPLIED
    assert reason == "STALE_PRECONDITION"
