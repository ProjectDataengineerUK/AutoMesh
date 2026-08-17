from __future__ import annotations

import os

import msal
import requests

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
REQUEST_TIMEOUT_SECONDS = 30


def _env(name: str) -> str:
    return os.environ[name]


def _access_token() -> str:
    app = msal.ConfidentialClientApplication(
        _env("GRAPH_CLIENT_ID"),
        authority=f"https://login.microsoftonline.com/{_env('GRAPH_TENANT_ID')}",
        client_credential=_env("GRAPH_CLIENT_SECRET"),
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Graph auth failed: {result.get('error_description')}")
    return result["access_token"]


def list_changed_files(delta_link: str | None = None) -> tuple[list[dict], str]:
    next_link = delta_link or (
        f"{GRAPH_API_BASE}/sites/{_env('GRAPH_SITE_ID')}/drives/{_env('GRAPH_DRIVE_ID')}/root/delta"
    )
    headers = {"Authorization": f"Bearer {_access_token()}"}
    items: list[dict] = []
    body: dict = {}

    while next_link:
        resp = requests.get(next_link, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        body = resp.json()
        items.extend(item for item in body.get("value", []) if "file" in item)
        next_link = body.get("@odata.nextLink")

    return items, body.get("@odata.deltaLink", delta_link or "")


def download_file_content(download_url: str) -> bytes:
    resp = requests.get(download_url, timeout=REQUEST_TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.content
