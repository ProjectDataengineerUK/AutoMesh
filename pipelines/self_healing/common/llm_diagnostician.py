from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import anthropic

# `anthropic` is imported lazily inside diagnose(), not at module level: it pulls in a
# large pydantic type tree that alone can exceed Airflow's DagBag import timeout
# (default 30s) when this module is imported transitively at DAG-parse time.
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

DIAGNOSIS_TOOL = {
    "name": "propose_fix",
    "description": "Propõe uma correção estruturada para a falha do pipeline",
    "input_schema": {
        "type": "object",
        "properties": {
            "root_cause": {"type": "string"},
            "fix_type": {"type": "string", "enum": ["contract", "code"]},
            "target_file": {"type": "string"},
            "diff": {"type": "string"},
            "explanation": {"type": "string"},
        },
        "required": ["root_cause", "fix_type", "target_file", "diff", "explanation"],
    },
}


@dataclass
class Diagnosis:
    root_cause: str
    fix_type: str
    target_file: str
    diff: str
    explanation: str


def _build_prompt(failure_context: dict) -> str:
    return (
        "Diagnostique a falha do pipeline abaixo e proponha uma correção.\n\n"
        f"Tipo de falha: {failure_context['source_failure_type']}\n"
        f"Fonte: {failure_context['source']}\n"
        f"Detalhes: {failure_context['detail']}\n"
        f"Contexto de código/contrato relevante:\n{failure_context.get('code_context', '')}"
    )


def diagnose(failure_context: dict, client: anthropic.Anthropic | None = None) -> Diagnosis:
    import anthropic

    client = client or anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        tools=[DIAGNOSIS_TOOL],
        tool_choice={"type": "tool", "name": "propose_fix"},
        messages=[{"role": "user", "content": _build_prompt(failure_context)}],
    )

    tool_use = next(block for block in response.content if block.type == "tool_use")
    return Diagnosis(**tool_use.input)


def resolve_diagnosis(event: dict, client: anthropic.Anthropic | None = None) -> Diagnosis:
    """Events that already carry a pre-built diagnosis (e.g. content_generation, already
    approved by the RAGAS gate) skip the LLM call entirely, so the PR body matches
    byte-for-byte what was already evaluated. See DESIGN_FASE4_RAG_CONTEUDO.md, Decision 1.
    """
    if event.get("source_failure_type") == "content_generation":
        payload = json.loads(event["detail"])
        return Diagnosis(fix_type="content", **payload)
    return diagnose(event, client)
