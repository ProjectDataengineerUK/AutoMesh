from __future__ import annotations

from unittest.mock import patch

import pytest

from pipelines.rag.jobs.ingest_sharepoint import run


@patch("pipelines.rag.jobs.ingest_sharepoint.delta_cursor")
@patch("pipelines.rag.jobs.ingest_sharepoint.graph_client")
def test_download_failure_does_not_advance_cursor_or_write(mock_graph, mock_cursor) -> None:
    mock_graph.list_changed_files.return_value = (
        [
            {
                "id": "document-1",
                "@microsoft.graph.downloadUrl": "https://download",
                "parentReference": {"path": "/drive/root:"},
                "name": "report.pdf",
                "lastModifiedDateTime": "2026-08-14T10:00:00Z",
            }
        ],
        "https://delta/new",
    )
    mock_graph.download_file_content.side_effect = RuntimeError("download failed")

    with pytest.raises(RuntimeError, match="download failed"):
        run()

    mock_cursor.set_delta_link.assert_not_called()
