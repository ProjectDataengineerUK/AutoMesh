"""Strict, observable quality gates for Gold products."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualityResult:
    product_id: str
    rows: int
    passed: bool
    reason_codes: tuple[str, ...]


class QualityFailure(ValueError):
    """Raised when a critical Gold quality rule fails."""

    def __init__(self, product_id: str, reasons: tuple[str, ...]) -> None:
        self.product_id = product_id
        self.reasons = reasons
        super().__init__(f"QUALITY_FAILED:{product_id}:{','.join(reasons)}")


def require_quality(
    rows: list[dict[str, Any]],
    product_id: str,
    key: str,
    required: tuple[str, ...],
    sensitive: tuple[str, ...] = (),
) -> QualityResult:
    reasons: list[str] = []
    if any(row.get(key) is None for row in rows):
        reasons.append("NULL_PRIMARY_KEY")
    keys = [row.get(key) for row in rows]
    if len(set(keys)) != len(keys):
        reasons.append("DUPLICATE_BUSINESS_KEY")
    if any(any(row.get(column) is None for column in required) for row in rows):
        reasons.append("REQUIRED_COLUMN_NULL")
    if any(column in required for column in sensitive):
        reasons.append("SENSITIVE_COLUMN_IN_REQUIRED_SCHEMA")
    if reasons:
        raise QualityFailure(product_id, tuple(reasons))
    return QualityResult(product_id, len(rows), True, ())
