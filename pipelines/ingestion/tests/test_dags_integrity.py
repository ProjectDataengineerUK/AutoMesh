from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip(
    "airflow",
    reason="apache-airflow is a heavy optional dependency, not installed in this dev environment; "
    "this test runs once Airflow is provisioned (see DESIGN Technical Context / IaC Impact).",
)

DAGS_DIR = Path(__file__).resolve().parent.parent / "dags"

EXPECTED_DAG_IDS = {
    "dag_ingest_kafka_market",
    "dag_ingest_kafka_infra",
    "dag_ingest_batch_crm",
}


def test_all_dags_import_without_errors() -> None:
    from airflow.models import DagBag

    dag_bag = DagBag(dag_folder=str(DAGS_DIR), include_examples=False)

    assert dag_bag.import_errors == {}


def test_expected_dag_ids_are_present() -> None:
    from airflow.models import DagBag

    dag_bag = DagBag(dag_folder=str(DAGS_DIR), include_examples=False)

    assert EXPECTED_DAG_IDS.issubset(dag_bag.dags.keys())


def test_no_dag_has_zero_tasks() -> None:
    from airflow.models import DagBag

    dag_bag = DagBag(dag_folder=str(DAGS_DIR), include_examples=False)

    for dag_id in EXPECTED_DAG_IDS:
        assert len(dag_bag.dags[dag_id].tasks) > 0, f"{dag_id} has no tasks"
