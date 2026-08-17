from __future__ import annotations

import os

# `databricks.vector_search` is imported lazily inside each function, not at module
# level: same DagBag import-timeout risk documented in llm_diagnostician.py (Fase 2)
# and train_outlier_model.py (Fase 3) for other heavy SDKs.
VECTOR_SEARCH_ENDPOINT = os.environ.get("VECTOR_SEARCH_ENDPOINT", "automesh-rag-endpoint")
VECTOR_SEARCH_INDEX = os.environ.get("VECTOR_SEARCH_INDEX", "main.rag.sharepoint_documents_index")
SOURCE_TABLE = os.environ.get("SHAREPOINT_DOCUMENTS_TABLE", "main.rag.sharepoint_documents")
EMBEDDING_MODEL = os.environ.get("VECTOR_SEARCH_EMBEDDING_MODEL", "databricks-bge-large-en")


def ensure_index_exists() -> None:
    from databricks.vector_search.client import VectorSearchClient

    client = VectorSearchClient()
    existing = {idx["name"] for idx in client.list_indexes(VECTOR_SEARCH_ENDPOINT).get("vector_indexes", [])}
    if VECTOR_SEARCH_INDEX in existing:
        return

    client.create_delta_sync_index(
        endpoint_name=VECTOR_SEARCH_ENDPOINT,
        index_name=VECTOR_SEARCH_INDEX,
        primary_key="document_id",
        delta_sync_index_config={
            "data_objects": [
                {
                    "table_name": SOURCE_TABLE,
                    "text_search_config": {"field_name": "chunk_text", "chunk_template": "{{chunk_text}}"},
                    "embedding_source_columns": ["chunk_text"],
                    "embedding_model": EMBEDDING_MODEL,
                }
            ]
        },
    )


def hybrid_search(query_text: str, num_results: int = 10) -> list[dict]:
    from databricks.vector_search.client import VectorSearchClient

    client = VectorSearchClient()
    index = client.get_index(VECTOR_SEARCH_ENDPOINT, VECTOR_SEARCH_INDEX)
    results = index.similarity_search(
        query_text=query_text,
        columns=["document_id", "source_path", "chunk_text"],
        num_results=num_results,
        query_type="HYBRID",
    )
    columns = [c["name"] for c in results["manifest"]["columns"]]
    return [dict(zip(columns, row, strict=True)) for row in results["result"]["data_array"]]
