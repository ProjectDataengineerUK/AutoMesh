from pipelines.gold.jobs.build_products import (
    build_finops_costs,
    build_lost_sales,
    build_market_insights,
    build_platform_health,
)
from pipelines.gold.jobs.publish_databricks import publish_lakeview


def test_acceptance_products_and_external_skip() -> None:
    assert build_market_insights(
        [{"source_event_id": "m", "event_date": "2026-08-17", "source_class": "b3", "metric_value": 1}]
    )[1].passed
    assert build_lost_sales(
        [{"sale_id": "s", "event_date": "2026-08-17", "region": "sul", "lost_value": 1}]
    )[1].passed
    assert build_finops_costs(
        [{"usage_id": "u", "usage_date": "2026-08-17", "job_name": "x", "consumption": 1}]
    )[1].passed
    assert build_platform_health(
        [{"event_id": "e", "observed_at": "2026-08-17T10:00:00", "capability_id": "CAP-01", "result": "PASS"}]
    )[1].passed
    assert publish_lakeview(False, {}, "test", "test").reason_code == "EXTERNAL_DISABLED"
