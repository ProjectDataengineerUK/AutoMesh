from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipelines.rag.common.graph_client import download_file_content, list_changed_files


@pytest.fixture(autouse=True)
def _graph_env(monkeypatch) -> None:
    monkeypatch.setenv("GRAPH_TENANT_ID", "tenant")
    monkeypatch.setenv("GRAPH_CLIENT_ID", "client")
    monkeypatch.setenv("GRAPH_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GRAPH_SITE_ID", "site")
    monkeypatch.setenv("GRAPH_DRIVE_ID", "drive")


@patch("pipelines.rag.common.graph_client.requests")
@patch("pipelines.rag.common.graph_client.msal")
def test_list_changed_files_filters_to_file_items(mock_msal, mock_requests) -> None:
    mock_msal.ConfidentialClientApplication.return_value.acquire_token_for_client.return_value = {
        "access_token": "token"
    }
    mock_requests.get.return_value = MagicMock(
        json=lambda: {
            "value": [{"id": "1", "file": {}}, {"id": "2", "folder": {}}],
            "@odata.deltaLink": "https://graph.microsoft.com/v1.0/delta?token=abc",
        }
    )

    items, new_delta_link = list_changed_files()

    assert [item["id"] for item in items] == ["1"]
    assert new_delta_link == "https://graph.microsoft.com/v1.0/delta?token=abc"


@patch("pipelines.rag.common.graph_client.requests")
@patch("pipelines.rag.common.graph_client.msal")
def test_list_changed_files_follows_next_link(mock_msal, mock_requests) -> None:
    mock_msal.ConfidentialClientApplication.return_value.acquire_token_for_client.return_value = {
        "access_token": "token"
    }
    page1 = MagicMock(json=lambda: {"value": [{"id": "1", "file": {}}], "@odata.nextLink": "https://next"})
    page2 = MagicMock(json=lambda: {"value": [{"id": "2", "file": {}}], "@odata.deltaLink": "https://delta"})
    mock_requests.get.side_effect = [page1, page2]

    items, new_delta_link = list_changed_files()

    assert [item["id"] for item in items] == ["1", "2"]
    assert new_delta_link == "https://delta"


@patch("pipelines.rag.common.graph_client.msal")
def test_access_token_raises_on_auth_failure(mock_msal) -> None:
    from pipelines.rag.common.graph_client import _access_token

    mock_msal.ConfidentialClientApplication.return_value.acquire_token_for_client.return_value = {
        "error_description": "invalid client secret"
    }

    with pytest.raises(RuntimeError, match="invalid client secret"):
        _access_token()


@patch("pipelines.rag.common.graph_client.requests")
def test_download_file_content_returns_bytes(mock_requests) -> None:
    mock_requests.get.return_value = MagicMock(content=b"file bytes")

    result = download_file_content("https://download")

    assert result == b"file bytes"
