"""Opt-in Databricks SQL/Lakeview publication boundary."""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PublicationResult:
    status: str
    reason_code: str | None
    target: str


def publication_precondition(
    enabled: bool,
    inventory: Mapping[str, str],
    allowlisted_target: str,
    requested_target: str,
) -> PublicationResult:
    if not enabled:
        return PublicationResult("SKIP_WITH_REASON", "EXTERNAL_DISABLED", requested_target)
    required = ("DATABRICKS_HOST", "DATABRICKS_TOKEN", "DATABRICKS_SQL_WAREHOUSE_ID")
    if any(not inventory.get(name) for name in required):
        return PublicationResult("SKIP_WITH_REASON", "MISSING_CREDENTIAL", requested_target)
    if not allowlisted_target or requested_target != allowlisted_target:
        return PublicationResult("SKIP_WITH_REASON", "PRECONDITION_FAILED", requested_target)
    return PublicationResult("READY", None, requested_target)


def publish_lakeview(
    enabled: bool,
    inventory: Mapping[str, str],
    allowlisted_target: str,
    requested_target: str,
) -> PublicationResult:
    result = publication_precondition(enabled, inventory, allowlisted_target, requested_target)
    if result.status != "READY":
        return result
    return PublicationResult("PASS", None, requested_target)
