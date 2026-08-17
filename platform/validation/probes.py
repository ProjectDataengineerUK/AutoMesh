"""Probe contracts and safe precondition results."""

from dataclasses import dataclass
from platform.validation.inventory import Inventory
from platform.validation.models import Evidence, Gate
from typing import Protocol


@dataclass(frozen=True)
class Precondition:
    ready: bool
    reason_code: str | None = None


class Probe(Protocol):
    capability_id: str
    gate: Gate

    def precondition(self, inventory: Inventory) -> Precondition: ...

    def run(self) -> Evidence: ...
