from __future__ import annotations

from typing import Protocol

from pipelines.delivery.common.models import Application, ApplicationStatus
from pipelines.delivery.common.storage import InMemoryDeliveryStore


class ModelRegistry(Protocol):
    def get_alias_version(self, model_name: str, alias: str) -> str | None: ...

    def set_alias(self, model_name: str, alias: str, version: str) -> None: ...


class MLflowRegistry:
    def __init__(self) -> None:
        from mlflow import MlflowClient

        self._client = MlflowClient()

    def get_alias_version(self, model_name: str, alias: str) -> str | None:
        try:
            return str(self._client.get_model_version_by_alias(model_name, alias).version)
        except Exception:  # noqa: BLE001 - a missing bootstrap alias is represented as None
            return None

    def set_alias(self, model_name: str, alias: str, version: str) -> None:
        self._client.set_registered_model_alias(model_name, alias, version)


def apply_model_promotion(
    store: InMemoryDeliveryStore,
    application_id: str,
    registry: ModelRegistry,
) -> Application:
    application = store.get_application(application_id)
    expected = application.expected_state
    current = registry.get_alias_version(expected["model_name"], expected["alias"])
    if current != expected.get("current_version"):
        application.status = ApplicationStatus.STALE_PRECONDITION
        application.result_detail = "alias changed since approval request"
    else:
        registry.set_alias(expected["model_name"], expected["alias"], expected["approved_version"])
        application.status = ApplicationStatus.APPLIED
        application.result_detail = "alias promoted"
    application.attempt_count += 1
    store.save_application(application)
    return application


def run_pending(store: InMemoryDeliveryStore, registry: ModelRegistry) -> list[Application]:
    return [
        apply_model_promotion(store, item.application_id, registry)
        for item in store.list_pending_applications()
        if item.action_type.value == "promote_model"
    ]
