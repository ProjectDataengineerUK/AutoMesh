"""Capability registry loading and validation."""

from dataclasses import dataclass
from pathlib import Path
from platform.validation.models import Gate
from typing import Any

import yaml


@dataclass(frozen=True)
class Capability:
    capability_id: str
    name: str
    owner: str
    required_gates: tuple[Gate, ...]
    external_required_names: tuple[str, ...] = ()


def load_registry(path: Path | None = None) -> tuple[Capability, ...]:
    registry_path = path or Path(__file__).with_name("capabilities.yaml")
    payload: dict[str, Any] = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    capabilities = tuple(
        Capability(
            capability_id=item["id"],
            name=item["name"],
            owner=item["owner"],
            required_gates=tuple(Gate(gate) for gate in item["required_gates"]),
            external_required_names=tuple(item.get("external_required_names", ())),
        )
        for item in payload["capabilities"]
    )
    identifiers = [item.capability_id for item in capabilities]
    expected = [f"CAP-{index:02d}" for index in range(1, 11)]
    if identifiers != expected:
        raise ValueError("registry must contain CAP-01 through CAP-10 in order")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("capability identifiers must be unique")
    return capabilities


def load_reason_codes(path: Path | None = None) -> frozenset[str]:
    codes_path = path or Path(__file__).with_name("reason_codes.yaml")
    payload: dict[str, Any] = yaml.safe_load(codes_path.read_text(encoding="utf-8"))
    return frozenset(str(code) for code in payload["reason_codes"])


def validate_evidence_reason(reason_code: str | None, allowed: frozenset[str]) -> None:
    if reason_code is not None and reason_code not in allowed:
        raise ValueError(f"unknown reason code: {reason_code}")
