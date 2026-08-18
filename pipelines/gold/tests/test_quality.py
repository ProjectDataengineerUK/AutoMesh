import pytest

from pipelines.gold.common.quality import QualityFailure, require_quality


def test_quality_accepts_complete_unique_rows() -> None:
    result = require_quality([{"id": "a", "value": 1}], "product", "id", ("id", "value"))
    assert result.passed is True


@pytest.mark.parametrize(
    "rows,reason",
    [
        ([{"id": None, "value": 1}], "NULL_PRIMARY_KEY"),
        ([{"id": "a", "value": None}], "REQUIRED_COLUMN_NULL"),
    ],
)
def test_quality_blocks_invalid_rows(rows, reason) -> None:
    with pytest.raises(QualityFailure, match=reason):
        require_quality(rows, "product", "id", ("id", "value"))


def test_quality_blocks_duplicate_keys() -> None:
    with pytest.raises(QualityFailure, match="DUPLICATE_BUSINESS_KEY"):
        require_quality([{"id": "a", "value": 1}, {"id": "a", "value": 2}], "product", "id", ("id", "value"))
