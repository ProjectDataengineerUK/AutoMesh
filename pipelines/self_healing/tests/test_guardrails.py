from __future__ import annotations

from pipelines.self_healing.common.guardrails import (
    check_allowlist,
    check_content,
    evaluate,
)


def test_allowed_path_passes() -> None:
    assert check_allowlist("pipelines/ingestion/contracts/b3_quotes.contract.yaml") is None


def test_path_outside_allowlist_is_rejected() -> None:
    reason = check_allowlist(".github/workflows/deploy.yml")
    assert reason is not None
    assert reason.startswith("out_of_scope_path:")


def test_path_traversal_is_rejected() -> None:
    reason = check_allowlist("pipelines/rag/../../.github/workflows/deploy.yml")
    assert reason is not None
    assert reason.startswith("invalid_path:")


def test_windows_path_is_rejected() -> None:
    reason = check_allowlist(r"pipelines\rag\reports\report.md")
    assert reason is not None
    assert reason.startswith("invalid_path:")


def test_content_without_dangerous_pattern_passes() -> None:
    assert check_content("schema:\n  columns:\n    - name: ticker\n") is None


def test_os_system_is_blocked() -> None:
    reason = check_content('os.system("rm -rf /")')
    assert reason is not None
    assert "dangerous_pattern" in reason


def test_hardcoded_secret_is_blocked() -> None:
    reason = check_content('api_key = "sk-abcdef123456"')
    assert reason is not None


def test_drop_table_is_blocked() -> None:
    reason = check_content("DROP TABLE silver.b3_quotes;")
    assert reason is not None


def test_evaluate_returns_allowlist_reason_first() -> None:
    reason = evaluate(".github/workflows/deploy.yml", 'os.system("evil")')
    assert reason is not None
    assert reason.startswith("out_of_scope_path:")


def test_evaluate_returns_none_for_safe_change() -> None:
    reason = evaluate(
        "pipelines/ingestion/contracts/b3_quotes.contract.yaml",
        "schema:\n  columns:\n    - name: volume\n      required: false\n",
    )
    assert reason is None


def test_insights_path_is_allowed() -> None:
    assert check_allowlist("pipelines/insights/model_registry_state.yaml") is None


def test_finops_path_is_allowed() -> None:
    assert check_allowlist("pipelines/finops/dags/dag_finops_monitor.py") is None


def test_self_healing_path_is_allowed() -> None:
    assert check_allowlist("pipelines/self_healing/common/guardrails.py") is None


def test_rag_path_is_allowed() -> None:
    assert check_allowlist("pipelines/rag/reports/insight-1-20260810T100000.md") is None
