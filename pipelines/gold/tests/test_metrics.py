from pipelines.gold.common.metrics import count_by, sum_by


def test_sum_by_groups_metrics() -> None:
    rows = [{"day": "2026-08-17", "value": 2}, {"day": "2026-08-17", "value": 3}]
    assert sum_by(rows, ("day",), "value") == [{"day": "2026-08-17", "value": 5.0}]


def test_count_by_groups_metrics() -> None:
    rows = [{"cap": "CAP-01"}, {"cap": "CAP-01"}]
    assert count_by(rows, ("cap",)) == [{"cap": "CAP-01", "metric_count": 2}]
