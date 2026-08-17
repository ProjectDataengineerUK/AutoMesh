from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from airflow.decorators import dag, task
from deltalake import DeltaTable

from pipelines.self_healing.common import checkpoint as ckpt
from pipelines.self_healing.common import github_pr
from pipelines.self_healing.common.guardrails import evaluate as evaluate_guardrails
from pipelines.self_healing.common.llm_diagnostician import resolve_diagnosis
from pipelines.self_healing.common.rejection_writer import write_rejection

BRONZE_BASE_PATH = os.environ.get("BRONZE_BASE_PATH", "data/bronze")
DLQ_TABLE_PATH = os.environ.get("DLQ_TABLE_PATH", f"{BRONZE_BASE_PATH}/_dlq/bronze_dlq")
EVENTS_TABLE_PATH = os.environ.get("SELF_HEALING_EVENTS_PATH", "data/self_healing/self_healing_events")

RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}


def _table_exists(path: str) -> bool:
    return os.path.isdir(os.path.join(path, "_delta_log"))


def _read_new_rows(table_path: str, since: datetime) -> list[dict]:
    if not _table_exists(table_path):
        return []
    rows = DeltaTable(table_path).to_pyarrow_table().to_pylist()
    return [row for row in rows if row["detected_at"] > since]


@dag(
    dag_id="dag_self_healing_diagnose",
    schedule="*/30 * * * *",
    start_date=datetime(2026, 8, 3, tzinfo=timezone.utc),
    catchup=False,
    default_args=RETRY_ARGS,
    tags=["self-healing", "fase2"],
)
def dag_self_healing_diagnose():
    @task
    def collect_contract_failures() -> list[dict]:
        since = ckpt.get_checkpoint("bronze_dlq")
        rows = _read_new_rows(DLQ_TABLE_PATH, since)
        return [
            {
                "event_id": f"dlq-{row['source']}-{row['detected_at'].isoformat()}",
                "source_failure_type": "contract",
                "source": row["source"],
                "detail": row.get("_failure_reason", "unknown"),
                "code_context": f"contracts/{row['source']}.contract.yaml",
                "detected_at": row["detected_at"].isoformat(),
            }
            for row in rows
        ]

    @task
    def collect_execution_failures() -> list[dict]:
        since = ckpt.get_checkpoint("self_healing_events")
        rows = _read_new_rows(EVENTS_TABLE_PATH, since)
        return [
            {
                "event_id": row["event_id"],
                "source_failure_type": row["source_failure_type"],
                "source": row["source"],
                "detail": row["detail"],
                "code_context": "",
                "detected_at": row["detected_at"].isoformat(),
            }
            for row in rows
        ]

    @task
    def merge_events(contract_events: list[dict], execution_events: list[dict]) -> list[dict]:
        return contract_events + execution_events

    @task
    def diagnose_and_act(event: dict) -> dict:
        diagnosis = resolve_diagnosis(event)
        rejection_reason = evaluate_guardrails(diagnosis.target_file, diagnosis.diff)

        if rejection_reason:
            write_rejection(
                source_failure_type=event["source_failure_type"],
                rejection_reason=rejection_reason,
                proposed_diff=diagnosis.diff,
            )
            return {
                "status": "rejected",
                "reason": rejection_reason,
                "event": event,
            }

        pr_url = github_pr.propose_fix_as_pr(
            diagnosis=diagnosis,
            event_id=event["event_id"],
            log_link=f"event_id={event['event_id']} detected_at={event['detected_at']}",
        )
        return {
            "status": "pr_opened",
            "pr_url": pr_url,
            "event": event,
            "diagnosis": {
                "root_cause": diagnosis.root_cause,
                "target_file": diagnosis.target_file,
                "explanation": diagnosis.explanation,
            },
        }

    @task
    def enqueue_delivery(result: dict) -> str:
        if result.get("status") != "pr_opened":
            return "skipped:no_pr"

        recipient = os.environ.get("DELIVERY_REVIEW_RECIPIENT")
        if not recipient:
            return "skipped:no_recipient"

        from pipelines.delivery.common.runtime import get_store
        from pipelines.delivery.jobs.source_adapters import enqueue_pr_result

        notification, created = enqueue_pr_result(get_store(), result, recipient)
        return f"{'created' if created else 'existing'}:{notification.notification_id}"

    @task
    def advance_checkpoints(contract_events: list[dict], execution_events: list[dict]) -> None:
        if contract_events:
            ckpt.set_checkpoint(
                "bronze_dlq",
                ckpt.latest_timestamp(contract_events, "detected_at"),
            )
        if execution_events:
            ckpt.set_checkpoint(
                "self_healing_events",
                ckpt.latest_timestamp(execution_events, "detected_at"),
            )

    contract_events = collect_contract_failures()
    execution_events = collect_execution_failures()
    merged = merge_events(contract_events, execution_events)
    results = diagnose_and_act.expand(event=merged)
    delivery_results = enqueue_delivery.expand(result=results)
    checkpoints_task = advance_checkpoints(contract_events, execution_events)
    delivery_results >> checkpoints_task


dag_self_healing_diagnose()
