from __future__ import annotations

from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


@dag(
    dag_id="dag_build_gold",
    schedule="@hourly",
    start_date=datetime(2026, 8, 17, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["gold", "bi", "fase7"],
)
def dag_build_gold():
    @task
    def load_contracts() -> str:
        return "gold-contracts-loaded"

    @task
    def build_products(contract_status: str) -> str:
        return f"gold-products-built:{contract_status}"

    @task
    def publish_views(build_status: str) -> str:
        return f"semantic-views-ready:{build_status}"

    publish_views(build_products(load_contracts()))


dag_build_gold()
