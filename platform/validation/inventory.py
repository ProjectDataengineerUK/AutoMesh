"""Environment inventory that never exposes secret values."""

import os
import platform as runtime_platform
from dataclasses import asdict, dataclass
from platform.validation.registry import Capability
from typing import Mapping


@dataclass(frozen=True)
class InventoryItem:
    capability_id: str
    configured: bool
    required_names: tuple[str, ...]


@dataclass(frozen=True)
class Inventory:
    environment: str
    python_version: str
    items: tuple[InventoryItem, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "environment": self.environment,
            "python_version": self.python_version,
            "items": [asdict(item) for item in self.items],
        }


def collect_inventory(
    capabilities: tuple[Capability, ...],
    environment: str = "local",
    environ: Mapping[str, str] | None = None,
) -> Inventory:
    names = os.environ if environ is None else environ
    items = tuple(
        InventoryItem(
            capability_id=capability.capability_id,
            configured=bool(capability.external_required_names)
            and all(bool(names.get(name)) for name in capability.external_required_names),
            required_names=capability.external_required_names,
        )
        for capability in capabilities
    )
    return Inventory(environment=environment, python_version=runtime_platform.python_version(), items=items)
