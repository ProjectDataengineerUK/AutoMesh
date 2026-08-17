from __future__ import annotations

from datetime import timedelta

from pipelines.delivery.common.cards import render_card
from pipelines.delivery.common.models import (
    ActionType,
    Channel,
    Decision,
    Notification,
    NotificationType,
    utcnow,
)


def test_card_contains_only_decision_reference_in_execute_data() -> None:
    decision = Decision("c1", ActionType.PROMOTE_MODEL, "model", {"secret": "server-only"}, utcnow() + timedelta(1))
    notification = Notification(
        "c1",
        NotificationType.MODEL_PROMOTION,
        "user",
        Channel.TEAMS,
        {"title": "Review", "summary": "Promote model", "url": "https://example.test"},
        "key",
        decision_id=decision.decision_id,
    )
    card = render_card(notification, decision)
    execute_actions = [action for action in card["actions"] if action["type"] == "Action.Execute"]
    assert all(set(action["data"]) == {"decision_id", "schema_version"} for action in execute_actions)
    assert "server-only" not in str(card)
