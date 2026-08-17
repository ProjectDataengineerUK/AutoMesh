from __future__ import annotations

import importlib
from unittest.mock import MagicMock

import pandas as pd

from pipelines.insights.jobs.generate_insights import score


def test_score_uses_model_decision_function() -> None:
    model = MagicMock()
    model.decision_function.return_value = [0.1, -0.2, 0.3]
    features = pd.DataFrame(
        {"price_change_pct": [0, 0, 0], "volume_zscore": [0, 0, 0], "lost_sales_value_zscore": [0, 0, 0]}
    )

    result = score(model, features)

    assert list(result) == [0.1, -0.2, 0.3]


def test_write_insights_only_persists_negative_scores(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GOLD_INSIGHTS_PATH", str(tmp_path / "market_insights"))
    from pipelines.insights.jobs import generate_insights as module

    importlib.reload(module)

    scores = pd.Series([0.5, -0.3, -0.1, 0.2])

    written = module.write_insights(scores, model_version="3")

    assert written == 2

    from deltalake import DeltaTable

    rows = DeltaTable(str(tmp_path / "market_insights")).to_pyarrow_table().to_pylist()
    assert len(rows) == 2
    assert all(r["model_version"] == "3" for r in rows)


def test_write_insights_empty_when_no_anomalies(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GOLD_INSIGHTS_PATH", str(tmp_path / "market_insights"))
    from pipelines.insights.jobs import generate_insights as module

    importlib.reload(module)

    written = module.write_insights(pd.Series([0.5, 0.2]), model_version="3")

    assert written == 0
