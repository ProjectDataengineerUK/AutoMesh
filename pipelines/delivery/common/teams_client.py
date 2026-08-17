from __future__ import annotations

from collections.abc import Callable

import requests

REQUEST_TIMEOUT_SECONDS = 15


class TeamsDeliveryError(RuntimeError):
    def __init__(self, message: str, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


class TeamsClient:
    def __init__(self, token_provider: Callable[[], str]) -> None:
        self._token_provider = token_provider

    def send_card(self, service_url: str, conversation_id: str, card: dict) -> str:
        url = f"{service_url.rstrip('/')}/v3/conversations/{conversation_id}/activities"
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {self._token_provider()}"},
            json={
                "type": "message",
                "attachments": [
                    {"contentType": "application/vnd.microsoft.card.adaptive", "content": card}
                ],
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code >= 400:
            raise TeamsDeliveryError(
                f"Teams delivery failed with status {response.status_code}",
                retryable=response.status_code in {408, 429} or response.status_code >= 500,
            )
        return response.json()["id"]
