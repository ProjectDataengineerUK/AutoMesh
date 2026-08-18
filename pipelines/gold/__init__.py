"""Governed Gold products and semantic consumption contracts."""

from pipelines.gold.common.keys import latest_by_key
from pipelines.gold.common.quality import QualityFailure, require_quality

__all__ = ["QualityFailure", "latest_by_key", "require_quality"]
