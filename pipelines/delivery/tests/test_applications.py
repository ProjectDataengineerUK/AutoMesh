from __future__ import annotations

from pipelines.delivery.common.models import ActionType, Application, ApplicationStatus
from pipelines.delivery.common.storage import InMemoryDeliveryStore
from pipelines.delivery.jobs.applications import apply_model_promotion


class FakeRegistry:
    def __init__(self, current: str) -> None:
        self.current = current

    def get_alias_version(self, model_name: str, alias: str) -> str | None:
        return self.current

    def set_alias(self, model_name: str, alias: str, version: str) -> None:
        self.current = version


def _application(store: InMemoryDeliveryStore) -> Application:
    item, _ = store.create_application(
        Application(
            "decision-1",
            ActionType.PROMOTE_MODEL,
            "model",
            {"model_name": "market", "alias": "champion", "current_version": "1", "approved_version": "2"},
        )
    )
    return item


def test_model_promotion_applies_when_precondition_matches() -> None:
    store = InMemoryDeliveryStore()
    item = _application(store)
    registry = FakeRegistry("1")
    result = apply_model_promotion(store, item.application_id, registry)
    assert result.status == ApplicationStatus.APPLIED
    assert registry.current == "2"


def test_model_promotion_stops_when_alias_changed() -> None:
    store = InMemoryDeliveryStore()
    item = _application(store)
    registry = FakeRegistry("9")
    result = apply_model_promotion(store, item.application_id, registry)
    assert result.status == ApplicationStatus.STALE_PRECONDITION
    assert registry.current == "9"
