from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pipelines.rag.jobs.retrieval import rerank, search_and_rerank


def _fake_client(scores: list[float]) -> MagicMock:
    tool_use_block = SimpleNamespace(type="tool_use", input={"scores": scores})
    response = SimpleNamespace(content=[tool_use_block])
    client = MagicMock()
    client.messages.create.return_value = response
    return client


def test_rerank_orders_candidates_by_score_descending() -> None:
    candidates = [{"chunk_text": "low"}, {"chunk_text": "high"}, {"chunk_text": "mid"}]
    client = _fake_client([0.2, 0.9, 0.5])

    result = rerank("query", candidates, client=client)

    assert [c["chunk_text"] for c in result] == ["high", "mid", "low"]


def test_rerank_returns_empty_list_for_no_candidates() -> None:
    result = rerank("query", [], client=MagicMock())

    assert result == []


@patch("pipelines.rag.jobs.retrieval.hybrid_search")
def test_search_and_rerank_truncates_to_top_n(mock_hybrid_search) -> None:
    mock_hybrid_search.return_value = [{"chunk_text": f"c{i}"} for i in range(10)]
    client = _fake_client([float(i) for i in range(10)])

    result = search_and_rerank("query", client=client)

    assert len(result) <= 4
    assert result[0]["chunk_text"] == "c9"
