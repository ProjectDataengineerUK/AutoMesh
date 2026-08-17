from __future__ import annotations

import pandas as pd

from pipelines.finops.jobs.cost_monitor import detect_anomalies


def test_detect_anomalies_flags_job_above_threshold() -> None:
    current = pd.DataFrame({"job_name": ["dag_a", "dag_b"], "consumption": [100.0, 10.0]})
    history = pd.DataFrame(
        {
            "job_name": ["dag_a"] * 5 + ["dag_b"] * 5,
            "consumption": [10.0, 12.0, 9.0, 11.0, 10.0, 10.0, 11.0, 9.0, 10.5, 9.5],
        }
    )

    anomalies = detect_anomalies(current, history, threshold_stddev=2.0)

    assert list(anomalies["job_name"]) == ["dag_a"]


def test_detect_anomalies_empty_when_within_normal_range() -> None:
    current = pd.DataFrame({"job_name": ["dag_a"], "consumption": [10.5]})
    history = pd.DataFrame({"job_name": ["dag_a"] * 5, "consumption": [10.0, 11.0, 9.0, 10.5, 9.5]})

    anomalies = detect_anomalies(current, history, threshold_stddev=2.0)

    assert anomalies.empty


def test_detect_anomalies_ignores_jobs_with_no_history() -> None:
    current = pd.DataFrame({"job_name": ["new_dag"], "consumption": [1000.0]})
    history = pd.DataFrame({"job_name": [], "consumption": []})

    anomalies = detect_anomalies(current, history, threshold_stddev=2.0)

    assert anomalies.empty
