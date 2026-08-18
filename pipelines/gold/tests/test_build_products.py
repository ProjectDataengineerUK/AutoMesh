from pipelines.gold.jobs.build_products import (
    build_finops_costs,
    build_lost_sales,
    build_market_insights,
    build_platform_health,
    executive_metrics,
    operational_metrics,
)


def fixtures():
    market = [{"source_event_id": "m1", "event_date": "2026-08-17", "source_class": "b3", "metric_value": 10}]
    lost = [{"sale_id": "s1", "event_date": "2026-08-17", "region": "sudeste", "lost_value": 4}]
    finops = [{"usage_id": "u1", "usage_date": "2026-08-17", "job_name": "gold", "consumption": 2}]
    health = [{"event_id": "e1", "observed_at": "2026-08-17T10:00:00", "capability_id": "CAP-01", "result": "PASS"}]
    return market, lost, finops, health


def test_all_four_products_build() -> None:
    market, lost, finops, health = fixtures()
    assert build_market_insights(market)[1].passed
    assert build_lost_sales(lost)[1].passed
    assert build_finops_costs(finops)[1].passed
    assert build_platform_health(health)[1].passed


def test_consumer_metrics_are_available() -> None:
    market, lost, finops, health = fixtures()
    assert executive_metrics(market, lost, finops)["market_total_value"][0]["metric_value"] == 10.0
    assert operational_metrics(health)[0]["metric_count"] == 1
