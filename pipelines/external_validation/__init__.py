"""Opt-in external validation harness for Databricks artifacts."""

from .config import ValidationConfig
from .gates import GateResult, run_preflight

__all__ = ["GateResult", "ValidationConfig", "run_preflight"]
