from __future__ import annotations

import pandas as pd

from pipelines.insights.jobs.drift_check import build_shadow_comparison, has_drifted


def test_has_drifted_detects_shifted_distribution() -> None:
    baseline = pd.Series([1.0, 1.1, 0.9, 1.05, 0.95] * 10)
    current = pd.Series([5.0, 5.1, 4.9, 5.05, 4.95] * 10)

    assert has_drifted(baseline, current) is True


def test_has_drifted_false_for_same_distribution() -> None:
    baseline = pd.Series([1.0, 1.1, 0.9, 1.05, 0.95] * 10)
    current = pd.Series([1.0, 1.1, 0.9, 1.05, 0.95] * 10)

    assert has_drifted(baseline, current) is False


def test_has_drifted_false_for_insufficient_samples() -> None:
    assert has_drifted(pd.Series([1.0]), pd.Series([1.0, 2.0])) is False


def test_build_shadow_comparison_computes_anomaly_rates() -> None:
    champion_scores = pd.Series([0.1, -0.2, 0.3, -0.1])
    challenger_scores = pd.Series([-0.1, -0.2, 0.1, 0.2])

    comparison = build_shadow_comparison(champion_scores, challenger_scores)

    assert comparison["champion_anomaly_rate"] == 0.5
    assert comparison["challenger_anomaly_rate"] == 0.5
    assert "champion_mean_score" in comparison
    assert "challenger_mean_score" in comparison


def test_build_shadow_comparison_handles_empty_series() -> None:
    comparison = build_shadow_comparison(pd.Series(dtype=float), pd.Series(dtype=float))

    assert comparison["champion_anomaly_rate"] == 0.0
    assert comparison["challenger_anomaly_rate"] == 0.0
