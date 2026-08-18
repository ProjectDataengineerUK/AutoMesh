"""Deterministic local Gold product builders."""

from collections.abc import Iterable
from typing import Any

from pipelines.gold.common.keys import latest_by_key
from pipelines.gold.common.metrics import count_by, sum_by
from pipelines.gold.common.quality import QualityResult, require_quality


def build_market_insights(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], QualityResult]:
    source = latest_by_key(rows, ("source_event_id",), "event_date")
    result = require_quality(
        source,
        "gold_market_insights",
        "source_event_id",
        ("source_event_id", "event_date", "source_class", "metric_value"),
    )
    return source, result


def build_lost_sales(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], QualityResult]:
    source = latest_by_key(rows, ("sale_id",), "event_date")
    result = require_quality(source, "gold_lost_sales", "sale_id", ("sale_id", "event_date", "region", "lost_value"))
    return source, result


def build_finops_costs(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], QualityResult]:
    source = latest_by_key(rows, ("usage_id",), "usage_date")
    result = require_quality(
        source,
        "gold_finops_costs",
        "usage_id",
        ("usage_id", "usage_date", "job_name", "consumption"),
    )
    return source, result


def build_platform_health(rows: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], QualityResult]:
    source = latest_by_key(rows, ("event_id",), "observed_at")
    result = require_quality(
        source,
        "gold_platform_health",
        "event_id",
        ("event_id", "observed_at", "capability_id", "result"),
    )
    return source, result


def executive_metrics(
    market: Iterable[dict[str, Any]],
    lost_sales: Iterable[dict[str, Any]],
    finops: Iterable[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    return {
        "market_total_value": sum_by(market, ("event_date", "source_class"), "metric_value"),
        "lost_sales_value": sum_by(lost_sales, ("event_date", "region"), "lost_value"),
        "finops_consumption": sum_by(finops, ("usage_date", "job_name"), "consumption"),
    }


def operational_metrics(health: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return count_by(health, ("observed_at", "capability_id", "result"))
