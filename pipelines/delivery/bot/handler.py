from __future__ import annotations

from datetime import datetime

from pipelines.delivery.common.authorization import authorize
from pipelines.delivery.common.models import (
    ActionType,
    Application,
    ApplicationStatus,
    DecisionStatus,
    utcnow,
)
from pipelines.delivery.common.storage import InMemoryDeliveryStore


class InvalidActivity(ValueError):
    pass


def handle_execute(
    store: InMemoryDeliveryStore,
    activity: dict,
    *,
    verified_actor_id: str,
    verified_actor_groups: set[str],
    policy: dict[str, set[str]],
    now: datetime | None = None,
) -> dict:
    if activity.get("name") != "adaptiveCard/action":
        raise InvalidActivity("unsupported activity")
    action = activity.get("value", {}).get("action", {})
    decision_id = action.get("data", {}).get("decision_id")
    verb = action.get("verb")
    if not decision_id or verb not in {DecisionStatus.APPROVED.value, DecisionStatus.REJECTED.value}:
        raise InvalidActivity("invalid decision action")

    decision = store.get_decision(decision_id)
    authorize(verified_actor_groups, decision.action_type, policy)
    current_time = now or utcnow()
    if decision.expires_at <= current_time:
        decision, _ = store.compare_and_set_decision(
            decision_id,
            DecisionStatus.PENDING,
            DecisionStatus.EXPIRED,
            verified_actor_id,
            now=current_time,
        )
        return {"decision_id": decision_id, "status": decision.status.value}

    target = DecisionStatus(verb)
    reason = action.get("data", {}).get("reason")
    if target == DecisionStatus.REJECTED and not reason:
        raise InvalidActivity("rejection reason is required")
    decision, changed = store.compare_and_set_decision(
        decision_id,
        DecisionStatus.PENDING,
        target,
        verified_actor_id,
        reason=reason,
        now=current_time,
    )
    if changed and target == DecisionStatus.APPROVED and decision.action_type == ActionType.PROMOTE_MODEL:
        application, _ = store.create_application(
            Application(
                decision_id=decision.decision_id,
                action_type=decision.action_type,
                resource_ref=decision.resource_ref,
                expected_state=decision.expected_state,
                status=ApplicationStatus.PENDING,
            )
        )
        decision.application_status = application.status
    return {"decision_id": decision_id, "status": decision.status.value, "changed": changed}
