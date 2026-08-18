"""Deterministic preflight gates."""

from __future__ import annotations

from dataclasses import dataclass

from .config import ValidationConfig


@dataclass(frozen=True)
class GateResult:
    code: str
    status: str
    message: str
    remediation: str = ""


def run_preflight(config: ValidationConfig, adapter=None) -> list[GateResult]:
    results: list[GateResult] = []
    errors = config.validate()
    if errors:
        return [GateResult("CONFIG_INVALID", "FAIL", "; ".join(errors), "Correct configuration before retrying")]
    if not config.host:
        return [
            GateResult(
                "EXTERNAL_CONTEXT_MISSING",
                "SKIP_EXTERNAL",
                "No Databricks host configured",
                "Provide approved workspace context",
            )
        ]
    results.append(GateResult("CONFIG_VALID", "PASS", "Configuration is valid"))
    if adapter is None:
        return results + [
            GateResult(
                "ADAPTER_NOT_CONFIGURED",
                "SKIP_EXTERNAL",
                "No external adapter supplied",
                "Use approved adapter for workspace smoke",
            )
        ]
    checks = (
        ("WORKSPACE_REACHABLE", "workspace", "Workspace identity available"),
        ("UC_READY", "catalog", "Catalog and schema available"),
        ("PERMISSIONS_READY", "permissions", "Required permissions available"),
    )
    for code, check, message in checks:
        try:
            ok = bool(adapter.check(check))
        except (OSError, RuntimeError, ValueError) as exc:  # adapter boundary must classify failures
            ok = False
            message = f"{type(exc).__name__}: external check failed"
        results.append(
            GateResult(
                code,
                "PASS" if ok else "FAIL",
                message,
                "Verify workspace and permissions" if not ok else "",
            )
        )
        if not ok:
            break
    return results
