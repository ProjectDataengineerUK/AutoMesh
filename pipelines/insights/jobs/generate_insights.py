from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

import pandas as pd
import pyarrow as pa
from deltalake import write_deltalake

from pipelines.insights.jobs.train_outlier_model import (
    FEATURE_COLUMNS,
    MLFLOW_MODEL_NAME,
    build_features,
    read_silver_table,
)

logger = logging.getLogger(__name__)

# `mlflow` is imported lazily (see train_outlier_model.py for why), not at module level.
GOLD_INSIGHTS_PATH = os.environ.get("GOLD_INSIGHTS_PATH", "data/gold/market_insights")


def load_model_by_alias(alias: str):
    import mlflow.sklearn

    return mlflow.sklearn.load_model(f"models:/{MLFLOW_MODEL_NAME}@{alias}")


def score(model, features: pd.DataFrame) -> pd.Series:
    return pd.Series(model.decision_function(features[FEATURE_COLUMNS]), index=features.index)


def write_insights(scores: pd.Series, model_version: str) -> int:
    generated_at = datetime.now(timezone.utc)
    records = [
        {
            "insight_id": str(uuid.uuid4()),
            "source_ticker": None,
            "anomaly_score": float(value),
            "model_version": str(model_version),
            "generated_at": generated_at,
        }
        for value in scores
        if value < 0  # negative decision_function score = flagged anomaly
    ]
    if not records:
        return 0

    table = pa.Table.from_pylist(records)
    write_deltalake(GOLD_INSIGHTS_PATH, table, mode="append")
    return len(records)


def run() -> int:
    import mlflow

    b3_df = read_silver_table("b3_quotes")
    crm_df = read_silver_table("crm_lost_sales")
    features = build_features(b3_df, crm_df)

    try:
        model = load_model_by_alias("champion")
    except mlflow.exceptions.MlflowException:
        logger.warning("No @champion model registered yet — skipping inference until the first promotion")
        return 0

    scores = score(model, features)
    model_version = mlflow.MlflowClient().get_model_version_by_alias(MLFLOW_MODEL_NAME, "champion").version

    return write_insights(scores, model_version)


if __name__ == "__main__":
    written = run()
    print(f"Wrote {written} insights")
