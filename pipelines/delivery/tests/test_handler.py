from __future__ import annotations

from datetime import timedelta

import pytest

from pipelines.delivery.bot.handler import InvalidActivity, handle_execute
from pipelines.delivery.common.authorization import AuthorizationError
from pipelines.delivery.common.models import ActionType, Decision, DecisionStatus, utcnow
from pipelines.delivery.common.storage import InMemoryDeliveryStore

POLICY = {ActionType.REVIEW_PR.value: {"reviewers"}}


def _activity(decision_id: str, verb: str, reason: str | None = None) -> dict:
    data = {"decision_id": decision_id}
    if reason:
        data["reason"] = reason
    return {"name": "adaptiveCard/action", "value": {"action": {"verb": verb, "data": data}}}


def _store_with_decision(expires_delta: timedelta = timedelta(hours=1)) -> tuple[InMemoryDeliveryStore, Decision]:
    store = InMemoryDeliveryStore()
    decision = store.create_decision(
        Decision("c1", ActionType.REVIEW_PR, "pr:1", {}, utcnow() + expires_delta)
    )
    return store, decision


def test_authorized_approval_is_idempotent() -> None:
    store, decision = _store_with_decision()
    first = handle_execute(
        store,
        _activity(decision.decision_id, "approved"),
        verified_actor_id="actor",
        verified_actor_groups={"reviewers"},
        policy=POLICY,
    )
    second = handle_execute(
        store,
        _activity(decision.decision_id, "approved"),
        verified_actor_id="actor",
        verified_actor_groups={"reviewers"},
        policy=POLICY,
    )
    assert first["changed"] is True
    assert second["changed"] is False


def test_unknown_group_is_denied_without_state_change() -> None:
    store, decision = _store_with_decision()
    with pytest.raises(AuthorizationError):
        handle_execute(
            store,
            _activity(decision.decision_id, "approved"),
            verified_actor_id="actor",
            verified_actor_groups={"unknown"},
            policy=POLICY,
        )
    assert store.get_decision(decision.decision_id).status == DecisionStatus.PENDING


def test_rejection_requires_reason() -> None:
    store, decision = _store_with_decision()
    with pytest.raises(InvalidActivity, match="reason"):
        handle_execute(
            store,
            _activity(decision.decision_id, "rejected"),
            verified_actor_id="actor",
            verified_actor_groups={"reviewers"},
            policy=POLICY,
        )


def test_expired_decision_cannot_be_approved() -> None:
    store, decision = _store_with_decision(timedelta(seconds=-1))
    result = handle_execute(
        store,
        _activity(decision.decision_id, "approved"),
        verified_actor_id="actor",
        verified_actor_groups={"reviewers"},
        policy=POLICY,
    )
    assert result["status"] == "expired"
