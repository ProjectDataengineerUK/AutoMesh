from __future__ import annotations

import json
from unittest.mock import patch

from pipelines.rag.jobs.content_factory import process_outlier


def _outlier() -> dict:
    return {"insight_id": "insight-1", "source_ticker": "PETR4", "anomaly_score": -0.3}


@patch("pipelines.rag.jobs.content_factory.write_event")
@patch("pipelines.rag.jobs.content_factory.write_rejection")
@patch("pipelines.rag.jobs.content_factory.evaluate_ragas")
@patch("pipelines.rag.jobs.content_factory.check_output")
@patch("pipelines.rag.jobs.content_factory._draft_report")
@patch("pipelines.rag.jobs.content_factory.search_and_rerank")
def test_approved_draft_writes_self_healing_event(
    mock_search, mock_draft, mock_check_output, mock_ragas, mock_write_rejection, mock_write_event
) -> None:
    mock_search.return_value = [{"source_path": "/doc.txt", "chunk_text": "context"}]
    mock_draft.return_value = "rascunho aprovado"
    mock_check_output.return_value = "rascunho aprovado"
    mock_ragas.return_value = {"faithfulness": 0.9, "answer_relevancy": 0.85}
    mock_write_event.return_value = "event-123"

    result = process_outlier(_outlier())

    assert result == "queued:event-123"
    mock_write_rejection.assert_not_called()
    mock_write_event.assert_called_once()

    kwargs = mock_write_event.call_args.kwargs
    assert kwargs["source_failure_type"] == "content_generation"
    payload = json.loads(kwargs["detail"])
    assert payload["diff"] == "rascunho aprovado"
    assert payload["target_file"].startswith("pipelines/rag/reports/insight-1")
    assert "faithfulness=0.90" in payload["explanation"]


@patch("pipelines.rag.jobs.content_factory.write_event")
@patch("pipelines.rag.jobs.content_factory.write_rejection")
@patch("pipelines.rag.jobs.content_factory.evaluate_ragas")
@patch("pipelines.rag.jobs.content_factory.check_output")
@patch("pipelines.rag.jobs.content_factory._draft_report")
@patch("pipelines.rag.jobs.content_factory.search_and_rerank")
def test_low_ragas_score_writes_rejection_not_event(
    mock_search, mock_draft, mock_check_output, mock_ragas, mock_write_rejection, mock_write_event
) -> None:
    mock_search.return_value = []
    mock_draft.return_value = "rascunho fraco"
    mock_check_output.return_value = "rascunho fraco"
    mock_ragas.return_value = {"faithfulness": 0.3, "answer_relevancy": 0.4}

    result = process_outlier(_outlier())

    assert result == "rejected:low_ragas_score"
    mock_write_event.assert_not_called()
    mock_write_rejection.assert_called_once_with(
        source_failure_type="content_generation",
        rejection_reason="low_ragas_score",
        proposed_diff="rascunho fraco",
    )
