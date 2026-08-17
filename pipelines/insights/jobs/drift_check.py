from __future__ import annotations

import json
import os

import pandas as pd
from scipy.stats import ks_2samp

from pipelines.insights.jobs.generate_insights import load_model_by_alias, score
from pipelines.insights.jobs.train_outlier_model import (
    MLFLOW_MODEL_NAME,
    build_features,
    read_silver_table,
)
from pipelines.self_healing.common.failure_capture import write_event

# `mlflow` is imported lazily (see train_outlier_model.py for why), not at module level.
DRIFT_P_VALUE_THRESHOLD = float(os.environ.get("DRIFT_P_VALUE_THRESHOLD", "0.05"))


def has_drifted(baseline: pd.Series, current: pd.Series) -> bool:
    if len(baseline) < 2 or len(current) < 2:
        return False
    _, p_value = ks_2samp(baseline, current)
    return bool(p_value < DRIFT_P_VALUE_THRESHOLD)


def build_shadow_comparison(champion_scores: pd.Series, challenger_scores: pd.Series) -> dict:
    return {
        "champion_anomaly_rate": float((champion_scores < 0).mean()) if len(champion_scores) else 0.0,
        "challenger_anomaly_rate": float((challenger_scores < 0).mean()) if len(challenger_scores) else 0.0,
        "champion_mean_score": float(champion_scores.mean()) if len(champion_scores) else 0.0,
        "challenger_mean_score": float(challenger_scores.mean()) if len(challenger_scores) else 0.0,
    }


def get_model_alias_version(alias: str) -> str | None:
    import mlflow

    try:
        return mlflow.MlflowClient().get_model_version_by_alias(MLFLOW_MODEL_NAME, alias).version
    except mlflow.exceptions.MlflowException:
        return None


def check_and_emit(baseline_features: pd.DataFrame, current_features: pd.DataFrame) -> dict:
    result = {"drifted": False, "promotion_candidate": False}

    for column in current_features.columns:
        if has_drifted(baseline_features[column], current_features[column]):
            result["drifted"] = True
            break

    challenger_version = get_model_alias_version("challenger")
    champion_version = get_model_alias_version("champion")

    if challenger_version is not None and challenger_version != champion_version:
        if champion_version is None:
            comparison = {"note": "no champion yet — first deployment, no shadow comparison possible"}
        elif current_features.empty:
            comparison = {"note": "no current data available for shadow comparison"}
        else:
            champion_model = load_model_by_alias("champion")
            challenger_model = load_model_by_alias("challenger")
            comparison = build_shadow_comparison(
                score(champion_model, current_features), score(challenger_model, current_features)
            )

        write_event(
            source="dag_generate_insights",
            detail=(
                f"model={MLFLOW_MODEL_NAME} challenger_version={challenger_version} "
                f"comparison={json.dumps(comparison)}"
            ),
            source_failure_type="model_promotion",
        )
        result["promotion_candidate"] = True

    return result


def run() -> dict:
    b3_df = read_silver_table("b3_quotes")
    crm_df = read_silver_table("crm_lost_sales")
    current_features = build_features(b3_df, crm_df)

    # Baseline: same feature engineering over the full available history (MVP — no separate stored baseline yet).
    baseline_features = current_features

    return check_and_emit(baseline_features, current_features)


if __name__ == "__main__":
    print(run())
