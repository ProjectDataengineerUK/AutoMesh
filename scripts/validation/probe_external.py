"""Safe external-probe precondition dispatcher."""

from platform.validation.inventory import Inventory
from platform.validation.probes import Precondition


def external_precondition(capability_id: str, inventory: Inventory, enabled: bool) -> Precondition:
    if not enabled:
        return Precondition(False, "EXTERNAL_DISABLED")
    item = next((candidate for candidate in inventory.items if candidate.capability_id == capability_id), None)
    if item is None or not item.configured:
        return Precondition(False, "MISSING_CREDENTIAL")
    return Precondition(True)
