from __future__ import annotations

import os

from pipelines.rag.common.vector_index import hybrid_search

RETRIEVAL_CANDIDATES = int(os.environ.get("RAG_RETRIEVAL_CANDIDATES", "10"))
RERANK_TOP_N = int(os.environ.get("RAG_RERANK_TOP_N", "4"))

RERANK_TOOL = {
    "name": "score_relevance",
    "description": "Atribui um score de relevância 0-1 para cada chunk em relação à query, na mesma ordem recebida",
    "input_schema": {
        "type": "object",
        "properties": {"scores": {"type": "array", "items": {"type": "number"}}},
        "required": ["scores"],
    },
}


def rerank(query: str, candidates: list[dict], client=None) -> list[dict]:
    import anthropic

    if not candidates:
        return []

    client = client or anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    numbered = "\n".join(f"{i}: {c['chunk_text'][:500]}" for i, c in enumerate(candidates))
    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        max_tokens=1024,
        tools=[RERANK_TOOL],
        tool_choice={"type": "tool", "name": "score_relevance"},
        messages=[{"role": "user", "content": f"Query: {query}\n\nChunks:\n{numbered}"}],
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    scored = sorted(zip(candidates, tool_use.input["scores"], strict=True), key=lambda pair: pair[1], reverse=True)
    return [chunk for chunk, _ in scored]


def search_and_rerank(query: str, client=None) -> list[dict]:
    candidates = hybrid_search(query, num_results=RETRIEVAL_CANDIDATES)
    return rerank(query, candidates, client=client)[:RERANK_TOP_N]
