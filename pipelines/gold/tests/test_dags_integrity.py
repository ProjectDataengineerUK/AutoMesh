from pathlib import Path

import pytest

pytest.importorskip("airflow", reason="Airflow is required for the isolated DagBag gate")


def test_gold_dag_imports_without_errors() -> None:
    from airflow.models import DagBag

    dag_bag = DagBag(dag_folder=str(Path(__file__).resolve().parent.parent / "dags"), include_examples=False)
    assert dag_bag.import_errors == {}
    assert "dag_build_gold" in dag_bag.dags
