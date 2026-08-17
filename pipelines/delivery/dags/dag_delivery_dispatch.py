from __future__ import annotations

import os
from datetime import datetime, timezone

from airflow.decorators import dag, task

from pipelines.delivery.common.graph_mail import send_fallback
from pipelines.delivery.common.runtime import get_store
from pipelines.delivery.common.teams_client import TeamsClient
from pipelines.delivery.jobs.dispatcher import run


@dag(
    dag_id="dag_delivery_dispatch",
    schedule="*/5 * * * *",
    start_date=datetime(2026, 8, 14, tzinfo=timezone.utc),
    catchup=False,
    tags=["delivery", "teams", "fase5"],
)
def dag_delivery_dispatch():
    @task
    def dispatch() -> int:
        client = TeamsClient(lambda: os.environ["TEAMS_BOT_ACCESS_TOKEN"])

        def send(card: dict) -> str:
            return client.send_card(
                os.environ["TEAMS_SERVICE_URL"],
                os.environ["TEAMS_CONVERSATION_ID"],
                card,
            )

        return len(run(get_store(), send, send_fallback))

    dispatch()


dag_delivery_dispatch()
