from datetime import datetime, timezone
from platform.validation.registry import load_registry
from platform.validation.report import build_report


def test_report_always_contains_cap_01_through_cap_10() -> None:
    report = build_report(load_registry(), (), datetime.now(timezone.utc), "abc")
    assert [item["capability_id"] for item in report["capabilities"]] == [f"CAP-{index:02d}" for index in range(1, 11)]
