from __future__ import annotations

from pathlib import Path

# `nemoguardrails` is imported lazily inside each function, not at module level —
# same DagBag import-timeout risk documented in llm_diagnostician.py (Fase 2).
RAILS_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "guardrails"


def _rails():
    from nemoguardrails import LLMRails, RailsConfig

    config = RailsConfig.from_path(str(RAILS_CONFIG_DIR))
    return LLMRails(config)


def check_input(query: str) -> str:
    response = _rails().generate(messages=[{"role": "user", "content": query}])
    return response["content"]


def check_output(draft: str, context: dict) -> str:
    response = _rails().generate(
        messages=[
            {"role": "context", "content": context},
            {"role": "assistant", "content": draft},
        ]
    )
    return response.get("content", draft)
