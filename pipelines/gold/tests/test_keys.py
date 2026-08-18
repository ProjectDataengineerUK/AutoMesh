import pytest

from pipelines.gold.common.keys import latest_by_key, merge_by_key


def test_latest_by_key_is_replay_safe() -> None:
    rows = [
        {"id": "a", "at": "2026-08-17T10:00:00", "value": 1},
        {"id": "a", "at": "2026-08-17T11:00:00", "value": 2},
    ]
    assert latest_by_key(rows, ("id",), "at") == [{"id": "a", "at": "2026-08-17T11:00:00", "value": 2}]


def test_null_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="business keys"):
        latest_by_key([{"id": None, "at": "1"}], ("id",), "at")


def test_merge_replaces_existing_key() -> None:
    result = merge_by_key([{"id": "a", "value": 1}], [{"id": "a", "value": 2}], "id")
    assert result == [{"id": "a", "value": 2}]
