from __future__ import annotations

from pathlib import Path

import yaml

CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"

_TYPE_MAP = {
    "string": str,
    "decimal": (int, float),
    "long": int,
    "timestamp": str,
}


def _load_contract(source: str, contracts_dir: Path | None = None) -> dict:
    path = (contracts_dir or CONTRACTS_DIR) / f"{source}.contract.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_batch(
    source: str, records: list[dict], contracts_dir: Path | None = None
) -> tuple[list[dict], list[dict]]:
    contract = _load_contract(source, contracts_dir)
    columns = contract["schema"]["columns"]

    valid: list[dict] = []
    invalid: list[dict] = []
    for record in records:
        reason = _check_record(record, columns)
        if reason is None:
            valid.append(record)
        else:
            invalid.append({**record, "_failure_reason": reason})

    return valid, invalid


def _check_record(record: dict, columns: list[dict]) -> str | None:
    for col in columns:
        name = col["name"]
        required = col.get("required", False)
        expected_type = col["type"]
        value = record.get(name)

        if value is None:
            if required:
                return f"null_violation:{name}"
            continue

        py_type = _TYPE_MAP.get(expected_type)
        if py_type is not None and not isinstance(value, py_type):
            return f"type_mismatch:{name}"

        constraints = col.get("constraints") or {}
        minimum = constraints.get("minimum")
        if minimum is not None and isinstance(value, (int, float)) and value < minimum:
            return f"constraint_violation:{name}"

    return None
