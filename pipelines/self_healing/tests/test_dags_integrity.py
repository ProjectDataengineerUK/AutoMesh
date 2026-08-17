from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip(
    "airflow",
    reason="apache-airflow is a heavy optional dependency, not installed in this dev environment; "
    "this test runs once Airflow is provisioned (see DESIGN Technical Context / IaC Impact).",
)

SELF_HEALING_DAGS_DIR = Path(__file__).resolve().parent.parent / "dags"
PROCESSING_DAGS_DIR = SELF_HEALING_DAGS_DIR.parent.parent / "processing" / "dags"

EXPECTED_DAG_IDS = {
    "dag_process_bronze_to_silver",
    "dag_self_healing_diagnose",
}


def test_all_dags_import_without_errors() -> None:
    from airflow.models import DagBag

    dag_bag = DagBag(dag_folder=str(SELF_HEALING_DAGS_DIR), include_examples=False)
    dag_bag.collect_dags(dag_folder=str(PROCESSING_DAGS_DIR))

    assert dag_bag.import_errors == {}


def test_expected_dag_ids_are_present() -> None:
    from airflow.models import DagBag

    dag_bag = DagBag(dag_folder=str(SELF_HEALING_DAGS_DIR), include_examples=False)
    dag_bag.collect_dags(dag_folder=str(PROCESSING_DAGS_DIR))

    assert EXPECTED_DAG_IDS.issubset(dag_bag.dags.keys())
