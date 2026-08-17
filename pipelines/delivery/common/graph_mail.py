from __future__ import annotations

import os

import requests

REQUEST_TIMEOUT_SECONDS = 15


def _access_token() -> str:
    import msal

    app = msal.ConfidentialClientApplication(
        os.environ["GRAPH_CLIENT_ID"],
        authority=f"https://login.microsoftonline.com/{os.environ['GRAPH_TENANT_ID']}",
        client_credential=os.environ["GRAPH_CLIENT_SECRET"],
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Graph auth failed: {result.get('error_description')}")
    return result["access_token"]


def send_fallback(recipient: str, subject: str, body: str) -> None:
    sender = os.environ["GRAPH_SENDER_MAILBOX"]
    response = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail",
        headers={"Authorization": f"Bearer {_access_token()}"},
        json={
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": recipient}}],
            }
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
