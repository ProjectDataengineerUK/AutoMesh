from __future__ import annotations

import os

import pandas as pd
from deltalake import DeltaTable

# `mlflow` is imported lazily inside train(), not at module level: it pulls in a
# large dependency tree (Flask, SQLAlchemy, Alembic, ...) that alone can exceed
# Airflow's DagBag import timeout (default 30s) when this module is imported
# transitively at DAG-parse time. Same class of bug as the Fase 2 `anthropic` fix.

SILVER_BASE_PATH = os.environ.get("SILVER_BASE_PATH", "data/silver")
MLFLOW_MODEL_NAME = os.environ.get("MLFLOW_MODEL_NAME", "main.insights.market_outlier_detector")
CONTAMINATION = float(os.environ.get("ISOLATION_FOREST_CONTAMINATION", "0.05"))

FEATURE_COLUMNS = ["price_change_pct", "volume_zscore", "lost_sales_value_zscore"]


def read_silver_table(source: str) -> pd.DataFrame:
    table_path = f"{SILVER_BASE_PATH}/{source}"
    return DeltaTable(table_path).to_pandas()


def build_features(b3_df: pd.DataFrame, crm_df: pd.DataFrame) -> pd.DataFrame:
    b3 = b3_df.copy()
    b3["price_change_pct"] = b3.groupby("ticker")["price"].pct_change().fillna(0)
    volume_std = b3["volume"].std()
    b3["volume_zscore"] = 0.0 if not volume_std else (b3["volume"] - b3["volume"].mean()) / volume_std

    crm = crm_df.copy()
    value_std = crm["estimated_value"].std()
    crm["lost_sales_value_zscore"] = (
        0.0 if not value_std else (crm["estimated_value"] - crm["estimated_value"].mean()) / value_std
    )

    n = min(len(b3), len(crm)) or 1
    combined = pd.concat(
        [
            b3[["price_change_pct", "volume_zscore"]].iloc[:n].reset_index(drop=True),
            crm[["lost_sales_value_zscore"]].iloc[:n].reset_index(drop=True),
        ],
        axis=1,
    )
    return combined.fillna(0)


def train(features: pd.DataFrame) -> tuple[str, int]:
    import mlflow
    import mlflow.sklearn
    from sklearn.ensemble import IsolationForest

    with mlflow.start_run() as run:
        model = IsolationForest(contamination=CONTAMINATION, random_state=42)
        model.fit(features[FEATURE_COLUMNS])

        mlflow.log_param("contamination", CONTAMINATION)
        mlflow.log_param("n_features", len(FEATURE_COLUMNS))
        mlflow.log_param("n_samples", len(features))

        model_info = mlflow.sklearn.log_model(model, artifact_path="model", registered_model_name=MLFLOW_MODEL_NAME)

        client = mlflow.MlflowClient()
        client.set_registered_model_alias(MLFLOW_MODEL_NAME, "challenger", model_info.registered_model_version)

        return run.info.run_id, model_info.registered_model_version


def run() -> tuple[str, int]:
    b3_df = read_silver_table("b3_quotes")
    crm_df = read_silver_table("crm_lost_sales")
    features = build_features(b3_df, crm_df)
    return train(features)


if __name__ == "__main__":
    trained_run_id, trained_version = run()
    print(f"Trained model run_id={trained_run_id} version={trained_version}")
