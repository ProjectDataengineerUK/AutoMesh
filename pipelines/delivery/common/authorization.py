from __future__ import annotations

from collections.abc import Mapping

from pipelines.delivery.common.models import ActionType


class AuthorizationError(PermissionError):
    pass


def authorize(actor_groups: set[str], action_type: ActionType, policy: Mapping[str, set[str]]) -> None:
    allowed = policy.get(action_type.value, set())
    if not allowed or actor_groups.isdisjoint(allowed):
        raise AuthorizationError(f"actor is not authorized for {action_type.value}")
