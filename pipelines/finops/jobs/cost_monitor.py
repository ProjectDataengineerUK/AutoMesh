from __future__ import annotations

import logging
import os

import pandas as pd

from pipelines.self_healing.common.failure_capture import write_event

logger = logging.getLogger(__name__)

ANOMALY_THRESHOLD_STDDEV = float(os.environ.get("FINOPS_ANOMALY_THRESHOLD_STDDEV", "2.0"))


def detect_anomalies(
    current: pd.DataFrame, history: pd.DataFrame, threshold_stddev: float = ANOMALY_THRESHOLD_STDDEV
) -> pd.DataFrame:
    """current/history: columns ['job_name', 'consumption']. Returns rows from current flagged as anomalous."""
    stats = history.groupby("job_name")["consumption"].agg(["mean", "std"]).fillna(0)
    merged = current.merge(stats, on="job_name", how="left").fillna({"mean": 0.0, "std": 0.0})
    merged["threshold"] = merged["mean"] + threshold_stddev * merged["std"]
    return merged[(merged["std"] > 0) & (merged["consumption"] > merged["threshold"])]


def fetch_billing_usage(lookback_hours: int = 1) -> pd.DataFrame:
    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient()
    statement = f"""
        SELECT usage_metadata.job_name AS job_name, SUM(usage_quantity) AS consumption
        FROM system.billing.usage
        WHERE usage_date >= current_date() - INTERVAL {lookback_hours} HOURS
        GROUP BY 1
    """
    result = client.statement_execution.execute_statement(
        statement=statement, warehouse_id=os.environ["DATABRICKS_SQL_WAREHOUSE_ID"]
    )
    rows = result.result.data_array or []
    return pd.DataFrame(rows, columns=["job_name", "consumption"]).astype({"consumption": float})


def fetch_airflow_fallback(lookback_hours: int = 1) -> pd.DataFrame:
    from airflow.models import DagRun
    from airflow.utils.session import create_session

    cutoff = pd.Timestamp.utcnow() - pd.Timedelta(hours=lookback_hours)
    with create_session() as session:
        runs = session.query(DagRun).filter(DagRun.start_date >= cutoff).all()
        records = [
            {"job_name": run.dag_id, "consumption": (run.end_date - run.start_date).total_seconds()}
            for run in runs
            if run.end_date and run.start_date
        ]

    return pd.DataFrame(records, columns=["job_name", "consumption"])


def fetch_usage(lookback_hours: int = 1) -> pd.DataFrame:
    try:
        return fetch_billing_usage(lookback_hours)
    except Exception as e:  # noqa: BLE001 — deliberate fallback when system.billing.usage is unavailable
        logger.warning("system.billing.usage unavailable (%s) — falling back to Airflow dag_run.duration", e)
        return fetch_airflow_fallback(lookback_hours)


def run(lookback_hours: int = 1, history_lookback_hours: int = 168) -> int:
    current = fetch_usage(lookback_hours)
    history = fetch_usage(history_lookback_hours)
    anomalies = detect_anomalies(current, history)

    for _, row in anomalies.iterrows():
        write_event(
            source=row["job_name"],
            detail=f"consumption={row['consumption']:.2f} threshold={row['threshold']:.2f}",
            source_failure_type="cost_anomaly",
        )

    return len(anomalies)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    anomaly_count = run()
    print(f"Detected {anomaly_count} cost anomalies")
