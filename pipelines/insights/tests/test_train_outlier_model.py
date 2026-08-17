from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pandas as pd

from pipelines.insights.jobs.train_outlier_model import (
    FEATURE_COLUMNS,
    build_features,
    train,
)


def test_build_features_computes_price_change_and_zscores() -> None:
    b3_df = pd.DataFrame(
        {
            "ticker": ["PETR4", "PETR4", "VALE3"],
            "price": [30.0, 33.0, 60.0],
            "volume": [1000, 2000, 1500],
        }
    )
    crm_df = pd.DataFrame({"estimated_value": [10000.0, 20000.0, 15000.0]})

    features = build_features(b3_df, crm_df)

    assert list(features.columns) == FEATURE_COLUMNS
    assert len(features) == 3
    assert features.isnull().sum().sum() == 0


def test_build_features_handles_empty_inputs() -> None:
    b3_df = pd.DataFrame({"ticker": [], "price": [], "volume": []})
    crm_df = pd.DataFrame({"estimated_value": []})

    features = build_features(b3_df, crm_df)

    assert len(features) <= 1


def test_train_registers_model_and_sets_challenger_alias() -> None:
    features = pd.DataFrame(
        {
            "price_change_pct": [0.01, -0.02, 0.03, 0.0],
            "volume_zscore": [0.5, -0.5, 1.0, 0.0],
            "lost_sales_value_zscore": [0.2, -0.1, 0.4, 0.0],
        }
    )

    mock_mlflow = MagicMock()
    mock_run_context = MagicMock()
    mock_run_context.__enter__.return_value.info.run_id = "run-123"
    mock_mlflow.start_run.return_value = mock_run_context

    mock_model_info = MagicMock(registered_model_version="7")
    mock_mlflow.sklearn.log_model.return_value = mock_model_info

    mock_client = MagicMock()
    mock_mlflow.MlflowClient.return_value = mock_client

    # `train()` does `import mlflow` / `import mlflow.sklearn` locally (lazy import,
    # see train_outlier_model.py), so the mock must be injected via sys.modules
    # rather than patched as a module-level attribute.
    with patch.dict(sys.modules, {"mlflow": mock_mlflow, "mlflow.sklearn": mock_mlflow.sklearn}):
        run_id, version = train(features)

    assert run_id == "run-123"
    assert version == "7"
    mock_client.set_registered_model_alias.assert_called_once()
