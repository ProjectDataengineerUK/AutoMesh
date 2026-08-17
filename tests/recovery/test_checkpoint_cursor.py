from pipelines.self_healing.common.checkpoint import latest_timestamp


def test_cursor_advances_only_to_latest_completed_item() -> None:
    records = [{"updated_at": "2026-08-17T10:00:00+00:00"}, {"updated_at": "2026-08-17T11:00:00+00:00"}]
    assert latest_timestamp(records, "updated_at").hour == 11
