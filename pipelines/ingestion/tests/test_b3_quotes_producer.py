from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

from pipelines.ingestion.producers.b3_quotes_producer import (
    fetch_quotes,
    publish_quotes,
)


class FakeProducer:
    def __init__(self) -> None:
        self.produced: list[dict] = []
        self.flushed = False

    def produce(self, topic: str, key: bytes, value: bytes, on_delivery) -> None:
        self.produced.append({"topic": topic, "key": key, "value": value})

    def flush(self) -> None:
        self.flushed = True


@patch("pipelines.ingestion.producers.b3_quotes_producer.time.sleep")
@patch("pipelines.ingestion.producers.b3_quotes_producer.requests.get")
def test_fetch_quotes_retries_and_returns_empty_on_persistent_network_failure(mock_get, mock_sleep) -> None:
    mock_get.side_effect = requests.exceptions.ConnectionError("brapi.dev unreachable")

    result = fetch_quotes(["PETR4"])

    assert result == []
    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 3


@patch("pipelines.ingestion.producers.b3_quotes_producer.time.sleep")
@patch("pipelines.ingestion.producers.b3_quotes_producer.requests.get")
def test_fetch_quotes_retries_on_timeout_then_succeeds(mock_get, mock_sleep) -> None:
    success_response = MagicMock()
    success_response.json.return_value = {"results": [{"symbol": "PETR4", "regularMarketPrice": 38.5}]}
    mock_get.side_effect = [requests.exceptions.Timeout("timed out"), success_response]

    result = fetch_quotes(["PETR4"])

    assert result == [{"symbol": "PETR4", "regularMarketPrice": 38.5}]
    assert mock_get.call_count == 2
    assert mock_sleep.call_count == 1


@patch("pipelines.ingestion.producers.b3_quotes_producer.requests.get")
def test_fetch_quotes_happy_path_parses_results(mock_get) -> None:
    response = MagicMock()
    response.json.return_value = {"results": [{"symbol": "VALE3", "regularMarketPrice": 65.2}]}
    mock_get.return_value = response

    result = fetch_quotes(["VALE3"])

    assert result == [{"symbol": "VALE3", "regularMarketPrice": 65.2}]
    response.raise_for_status.assert_called_once()


@patch("pipelines.ingestion.producers.b3_quotes_producer.time.sleep")
@patch("pipelines.ingestion.producers.b3_quotes_producer.requests.get")
def test_fetch_quotes_does_not_raise_after_exhausting_retries(mock_get, mock_sleep) -> None:
    mock_get.side_effect = requests.exceptions.ConnectionError("network down")

    result = fetch_quotes(["PETR4", "VALE3"])

    assert result == []


def test_publish_quotes_skips_malformed_and_publishes_valid() -> None:
    quotes = [
        {"symbol": "PETR4", "regularMarketPrice": 38.5, "regularMarketVolume": 1000, "regularMarketTime": "t1"},
        {"symbol": None, "regularMarketPrice": 10.0},
        {"regularMarketPrice": 10.0},
    ]
    fake_producer = FakeProducer()

    published = publish_quotes(quotes, producer=fake_producer)

    assert published == 1
    assert len(fake_producer.produced) == 1
    assert fake_producer.flushed is True


def test_publish_quotes_empty_batch_still_flushes() -> None:
    fake_producer = FakeProducer()

    published = publish_quotes([], producer=fake_producer)

    assert published == 0
    assert fake_producer.flushed is True
