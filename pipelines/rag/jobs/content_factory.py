from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from deltalake import DeltaTable

from pipelines.rag.common.nemo_rails import check_output
from pipelines.rag.jobs.retrieval import search_and_rerank
from pipelines.self_healing.common import checkpoint as ckpt
from pipelines.self_healing.common.failure_capture import write_event
from pipelines.self_healing.common.rejection_writer import write_rejection

logger = logging.getLogger(__name__)

# `anthropic`, `ragas`, `datasets` and `langchain_anthropic` are imported lazily inside
# the functions that need them, not at module level — same DagBag import-timeout risk
# documented in llm_diagnostician.py (Fase 2) and train_outlier_model.py (Fase 3).
GOLD_INSIGHTS_PATH = os.environ.get("GOLD_INSIGHTS_PATH", "data/gold/market_insights")
RAGAS_FAITHFULNESS_THRESHOLD = float(os.environ.get("RAGAS_FAITHFULNESS_THRESHOLD", "0.7"))
RAGAS_RELEVANCY_THRESHOLD = float(os.environ.get("RAGAS_ANSWER_RELEVANCY_THRESHOLD", "0.7"))

CHECKPOINT_SOURCE = "rag_content_factory"


def _table_exists(path: str) -> bool:
    return os.path.isdir(os.path.join(path, "_delta_log"))


def _read_recent_outliers(since: datetime) -> list[dict]:
    if not _table_exists(GOLD_INSIGHTS_PATH):
        return []
    rows = DeltaTable(GOLD_INSIGHTS_PATH).to_pyarrow_table().to_pylist()
    return [row for row in rows if row["generated_at"] > since]


def _draft_report(outlier: dict, chunks: list[dict], client=None) -> str:
    import anthropic

    client = client or anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    context = "\n\n".join(f"[{c['source_path']}] {c['chunk_text']}" for c in chunks)
    prompt = (
        "Escreva um rascunho de relatório executivo cruzando o outlier de mercado abaixo "
        "com o contexto documental do SharePoint. Cite a fonte de cada afirmação.\n\n"
        f"Outlier: {json.dumps(outlier, default=str)}\n\nContexto:\n{context}"
    )
    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def evaluate_ragas(question: str, answer: str, contexts: list[str]) -> dict:
    from datasets import Dataset
    from langchain_anthropic import ChatAnthropic
    from ragas import evaluate
    from ragas.embeddings import HuggingfaceEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, faithfulness

    evaluator_llm = LangchainLLMWrapper(ChatAnthropic(model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")))
    evaluator_embeddings = HuggingfaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    dataset = Dataset.from_dict({"question": [question], "answer": [answer], "contexts": [contexts]})
    scores = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )
    return {"faithfulness": float(scores["faithfulness"]), "answer_relevancy": float(scores["answer_relevancy"])}


def process_outlier(outlier: dict) -> str:
    query = f"{outlier.get('source_ticker', '')} anomaly_score={outlier.get('anomaly_score', '')}"
    chunks = search_and_rerank(query)

    draft = _draft_report(outlier, chunks)
    draft = check_output(draft, context={"retrieved_chunks": chunks})

    ragas_scores = evaluate_ragas(question=query, answer=draft, contexts=[c["chunk_text"] for c in chunks])
    passed = (
        ragas_scores["faithfulness"] >= RAGAS_FAITHFULNESS_THRESHOLD
        and ragas_scores["answer_relevancy"] >= RAGAS_RELEVANCY_THRESHOLD
    )

    if not passed:
        write_rejection(
            source_failure_type="content_generation",
            rejection_reason="low_ragas_score",
            proposed_diff=draft,
        )
        return "rejected:low_ragas_score"

    report_id = f"{outlier['insight_id']}-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
    payload = {
        "root_cause": "content_generation",
        "target_file": f"pipelines/rag/reports/{report_id}.md",
        "diff": draft,
        "explanation": (
            f"Relatório gerado cruzando outlier {outlier['insight_id']} com {len(chunks)} documento(s) "
            f"do SharePoint. RAGAS: faithfulness={ragas_scores['faithfulness']:.2f}, "
            f"answer_relevancy={ragas_scores['answer_relevancy']:.2f} "
            f"(limiares: {RAGAS_FAITHFULNESS_THRESHOLD}/{RAGAS_RELEVANCY_THRESHOLD})."
        ),
    }
    event_id = write_event(
        source="dag_generate_content",
        detail=json.dumps(payload),
        source_failure_type="content_generation",
    )
    return f"queued:{event_id}"


def run() -> list[str]:
    since = ckpt.get_checkpoint(CHECKPOINT_SOURCE)
    outliers = _read_recent_outliers(since)

    results = []
    for outlier in outliers:
        try:
            results.append(process_outlier(outlier))
        except Exception:
            logger.exception("Failed to process outlier %s", outlier.get("insight_id"))
            raise

    if outliers:
        ckpt.set_checkpoint(
            CHECKPOINT_SOURCE,
            ckpt.latest_timestamp(outliers, "generated_at"),
        )

    return results


if __name__ == "__main__":
    print(run())
