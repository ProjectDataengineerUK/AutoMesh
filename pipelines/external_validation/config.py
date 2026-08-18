"""Safe configuration loading for local and external validation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

SECRET_RE = re.compile(r"(?i)(token|password|secret|authorization|pat)")
ALLOWED_ENV = {
    "AUTOMESH_DATABRICKS_HOST",
    "AUTOMESH_DATABRICKS_CATALOG",
    "AUTOMESH_DATABRICKS_SCHEMA",
    "AUTOMESH_VALIDATION_MODE",
}


@dataclass(frozen=True)
class ValidationConfig:
    mode: str = "preflight"
    host: str | None = None
    catalog: str | None = None
    schema: str | None = None
    confirm_publish: bool = False

    @classmethod
    def from_env(cls, mode: str | None = None, confirm_publish: bool = False) -> "ValidationConfig":
        selected = mode or os.getenv("AUTOMESH_VALIDATION_MODE", "preflight")
        if selected not in {"preflight", "dry-run", "publish"}:
            raise ValueError("mode must be preflight, dry-run or publish")
        return cls(
            selected,
            os.getenv("AUTOMESH_DATABRICKS_HOST"),
            os.getenv("AUTOMESH_DATABRICKS_CATALOG"),
            os.getenv("AUTOMESH_DATABRICKS_SCHEMA"),
            confirm_publish,
        )

    def validate(self) -> list[str]:
        errors = []
        if self.mode == "publish" and not self.confirm_publish:
            errors.append("publish requires confirm_publish")
        for name, value in (("host", self.host), ("catalog", self.catalog), ("schema", self.schema)):
            if value and SECRET_RE.search(value):
                errors.append(f"unsafe secret-like value in {name}")
        if self.host and not self.host.startswith(("https://", "http://")):
            errors.append("host must use http:// or https://")
        return errors

    def redacted(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "host": self.host,
            "catalog": self.catalog,
            "schema": self.schema,
            "confirm_publish": self.confirm_publish,
        }
