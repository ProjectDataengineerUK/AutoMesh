from __future__ import annotations

from pipelines.delivery.common.models import Notification, NotificationType
from pipelines.delivery.jobs.request_builder import enqueue


def enqueue_pr_result(store, result: dict, recipient_ref: str) -> tuple[Notification | None, bool]:
    """Translate a successful self-healing PR result into the delivery contract."""
    if result.get("status") != "pr_opened":
        return None, False

    event = result["event"]
    diagnosis = result["diagnosis"]
    pr_url = result["pr_url"]
    return enqueue(
        store,
        notification_type=NotificationType.PR_REVIEW,
        correlation_id=event["event_id"],
        resource_ref=pr_url,
        resource_version=f"{event['event_id']}:{diagnosis['target_file']}",
        recipient_ref=recipient_ref,
        payload={
            "title": f"AutoMesh review: {diagnosis['root_cause'][:72]}",
            "summary": diagnosis["explanation"],
            "url": pr_url,
        },
        expected_state={"pr_url": pr_url, "target_file": diagnosis["target_file"]},
    )
