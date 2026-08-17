from __future__ import annotations

import io

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return content.decode("utf-8", errors="ignore")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


def chunk_document(document_id: str, source_path: str, filename: str, content: bytes, updated_at: str) -> list[dict]:
    text = extract_text(filename, content)
    return [
        {
            "document_id": document_id,
            "source_path": source_path,
            "chunk_index": i,
            "chunk_text": chunk,
            "updated_at": updated_at,
        }
        for i, chunk in enumerate(chunk_text(text))
    ]
