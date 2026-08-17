import json
from platform.validation.inventory import collect_inventory
from platform.validation.models import Gate
from platform.validation.registry import Capability


def test_inventory_reports_names_without_values() -> None:
    capability = Capability("CAP-01", "test", "owner", (Gate.UNIT,), ("API_SECRET",))
    inventory = collect_inventory((capability,), environ={"API_SECRET": "never-leak-this"})
    serialized = json.dumps(inventory.to_dict())
    assert inventory.items[0].configured is True
    assert "API_SECRET" in serialized
    assert "never-leak-this" not in serialized


def test_empty_requirements_are_not_external_configuration() -> None:
    capability = Capability("CAP-01", "test", "owner", (Gate.UNIT,))
    assert collect_inventory((capability,), environ={}).items[0].configured is False
