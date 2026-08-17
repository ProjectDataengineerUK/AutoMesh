from __future__ import annotations

import logging
from pathlib import Path

from pipelines.ingestion.common.bronze_writer import write_bronze, write_dlq
from pipelines.ingestion.common.contract_validator import validate_batch
from pipelines.rag.common import delta_cursor, graph_client
from pipelines.rag.common.chunking import chunk_document
from pipelines.rag.common.vector_index import ensure_index_exists

logger = logging.getLogger(__name__)

RAG_CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"
SOURCE = "sharepoint_documents"


def _download_and_chunk(item: dict) -> list[dict]:
    try:
        content = graph_client.download_file_content(item["@microsoft.graph.downloadUrl"])
    except Exception:
        logger.exception("Failed to download SharePoint item %s", item.get("id"))
        raise

    return chunk_document(
        document_id=item["id"],
        source_path=f"{item['parentReference']['path']}/{item['name']}",
        filename=item["name"],
        content=content,
        updated_at=item["lastModifiedDateTime"],
    )


def run() -> dict:
    delta_link = delta_cursor.get_delta_link(SOURCE)
    changed_files, new_delta_link = graph_client.list_changed_files(delta_link)

    all_chunks: list[dict] = []
    for item in changed_files:
        all_chunks.extend(_download_and_chunk(item))

    valid, invalid = validate_batch(SOURCE, all_chunks, contracts_dir=RAG_CONTRACTS_DIR)
    written = write_bronze(SOURCE, valid)
    write_dlq(SOURCE, invalid)

    if written:
        ensure_index_exists()

    delta_cursor.set_delta_link(SOURCE, new_delta_link)

    return {"files_processed": len(changed_files), "chunks_written": written, "chunks_rejected": len(invalid)}


if __name__ == "__main__":
    print(run())
