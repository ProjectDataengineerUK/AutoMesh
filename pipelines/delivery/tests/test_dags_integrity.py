from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("airflow", reason="Airflow is optional on the host and validated in the container stack")

DAGS_DIR = Path(__file__).resolve().parent.parent / "dags"
EXPECTED = {
    "dag_delivery_collect",
    "dag_delivery_dispatch",
    "dag_delivery_apply",
    "dag_delivery_reconcile",
}


def test_delivery_dags_import_and_have_expected_ids() -> None:
    from airflow.models import DagBag

    bag = DagBag(dag_folder=str(DAGS_DIR), include_examples=False)
    assert bag.import_errors == {}
    assert EXPECTED.issubset(bag.dags)
