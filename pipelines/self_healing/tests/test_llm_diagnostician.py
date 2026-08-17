from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from pipelines.self_healing.common.llm_diagnostician import (
    Diagnosis,
    diagnose,
    resolve_diagnosis,
)


def _fake_client(tool_input: dict) -> MagicMock:
    tool_use_block = SimpleNamespace(type="tool_use", input=tool_input)
    response = SimpleNamespace(content=[tool_use_block])
    client = MagicMock()
    client.messages.create.return_value = response
    return client


def test_diagnose_parses_structured_response() -> None:
    tool_input = {
        "root_cause": "Campo ticker chegou nulo",
        "fix_type": "contract",
        "target_file": "pipelines/ingestion/contracts/b3_quotes.contract.yaml",
        "diff": "schema:\n  columns: []\n",
        "explanation": "brapi.dev retornou payload incompleto",
    }
    client = _fake_client(tool_input)

    result = diagnose(
        {"source_failure_type": "contract", "source": "b3_quotes", "detail": "null_violation:ticker"},
        client=client,
    )

    assert isinstance(result, Diagnosis)
    assert result.fix_type == "contract"
    assert result.target_file == tool_input["target_file"]
    client.messages.create.assert_called_once()


def test_diagnose_uses_tool_choice_propose_fix() -> None:
    tool_input = {
        "root_cause": "x",
        "fix_type": "code",
        "target_file": "pipelines/processing/jobs/bronze_to_silver.py",
        "diff": "...",
        "explanation": "...",
    }
    client = _fake_client(tool_input)

    diagnose({"source_failure_type": "execution", "source": "x", "detail": "y"}, client=client)

    _, kwargs = client.messages.create.call_args
    assert kwargs["tool_choice"] == {"type": "tool", "name": "propose_fix"}


def test_diagnose_includes_failure_detail_in_prompt() -> None:
    tool_input = {
        "root_cause": "x",
        "fix_type": "code",
        "target_file": "pipelines/processing/jobs/bronze_to_silver.py",
        "diff": "...",
        "explanation": "...",
    }
    client = _fake_client(tool_input)

    diagnose(
        {
            "source_failure_type": "execution",
            "source": "dag_process_bronze_to_silver",
            "detail": "TimeoutError: connection reset",
        },
        client=client,
    )

    _, kwargs = client.messages.create.call_args
    prompt = kwargs["messages"][0]["content"]
    assert "TimeoutError" in prompt
    assert "dag_process_bronze_to_silver" in prompt


def test_resolve_diagnosis_bypasses_llm_for_content_generation() -> None:
    payload = {
        "root_cause": "content_generation",
        "target_file": "pipelines/rag/reports/insight-1-20260810T100000.md",
        "diff": "# Relatório\n\nRAGAS: faithfulness=0.9",
        "explanation": "Aprovado pelo gate RAGAS",
    }
    event = {"source_failure_type": "content_generation", "detail": json.dumps(payload)}
    client = MagicMock()

    result = resolve_diagnosis(event, client=client)

    assert isinstance(result, Diagnosis)
    assert result.fix_type == "content"
    assert result.diff == payload["diff"]
    assert result.target_file == payload["target_file"]
    client.messages.create.assert_not_called()


def test_resolve_diagnosis_calls_llm_for_other_failure_types() -> None:
    tool_input = {
        "root_cause": "x",
        "fix_type": "contract",
        "target_file": "pipelines/ingestion/contracts/b3_quotes.contract.yaml",
        "diff": "...",
        "explanation": "...",
    }
    tool_use_block = SimpleNamespace(type="tool_use", input=tool_input)
    client = MagicMock()
    client.messages.create.return_value = SimpleNamespace(content=[tool_use_block])
    event = {"source_failure_type": "contract", "source": "b3_quotes", "detail": "null_violation:ticker"}

    result = resolve_diagnosis(event, client=client)

    assert result.target_file == tool_input["target_file"]
    client.messages.create.assert_called_once()
