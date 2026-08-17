from __future__ import annotations

from pipelines.delivery.common.models import Decision, Notification


def render_card(notification: Notification, decision: Decision | None = None) -> dict:
    body = [
        {"type": "TextBlock", "text": notification.payload.get("title", "AutoMesh"), "weight": "Bolder"},
        {"type": "TextBlock", "text": notification.payload.get("summary", ""), "wrap": True},
    ]
    actions = []
    if decision is not None:
        actions.extend(
            [
                {
                    "type": "Action.Execute",
                    "title": "Aprovar",
                    "verb": "approved",
                    "data": {"decision_id": decision.decision_id, "schema_version": 1},
                },
                {
                    "type": "Action.Execute",
                    "title": "Rejeitar",
                    "verb": "rejected",
                    "data": {"decision_id": decision.decision_id, "schema_version": 1},
                },
            ]
        )
    if url := notification.payload.get("url"):
        actions.append({"type": "Action.OpenUrl", "title": "Abrir evidência", "url": url})
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
        "actions": actions,
    }
