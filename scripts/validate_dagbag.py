from __future__ import annotations

import os

from airflow.models import DagBag

dag_folder = os.environ.get("DAG_VALIDATION_FOLDER", "/opt/airflow/dags")
bag = DagBag(dag_folder=dag_folder, include_examples=False)
print(f"DAGS={sorted(bag.dags)}")
print(f"ERRORS={bag.import_errors}")
raise SystemExit(1 if bag.import_errors else 0)
