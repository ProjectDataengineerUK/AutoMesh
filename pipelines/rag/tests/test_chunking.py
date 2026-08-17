from __future__ import annotations

from pipelines.rag.common.chunking import chunk_document, chunk_text, extract_text


def test_extract_text_decodes_plain_text() -> None:
    assert extract_text("notes.txt", b"hello world") == "hello world"


def test_extract_text_ignores_undecodable_bytes() -> None:
    result = extract_text("notes.txt", b"valid \xff\xfe bytes")

    assert "valid" in result


def test_chunk_text_splits_long_text_with_overlap() -> None:
    text = "a" * 2500

    chunks = chunk_text(text, chunk_size=1000, overlap=200)

    assert len(chunks) == 4
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_text_returns_single_chunk_for_short_text() -> None:
    chunks = chunk_text("short text", chunk_size=1000, overlap=200)

    assert chunks == ["short text"]


def test_chunk_text_drops_empty_chunks() -> None:
    chunks = chunk_text("", chunk_size=1000, overlap=200)

    assert chunks == []


def test_chunk_document_assigns_sequential_indices() -> None:
    chunks = chunk_document(
        document_id="doc-1",
        source_path="/sites/x/Documents/report.txt",
        filename="report.txt",
        content=b"a" * 2500,
        updated_at="2026-08-10T10:00:00Z",
    )

    assert [c["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert all(c["document_id"] == "doc-1" for c in chunks)
    assert all(c["source_path"] == "/sites/x/Documents/report.txt" for c in chunks)
