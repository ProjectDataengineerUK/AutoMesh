from __future__ import annotations

import json
import logging
import os
import time

import requests
from confluent_kafka import Producer

from pipelines.ingestion.common.kafka_config import PRODUCER_CONFIG

logger = logging.getLogger(__name__)

BRAPI_BASE_URL = os.environ.get("BRAPI_BASE_URL", "https://brapi.dev/api/quote")
BRAPI_TOKEN = os.environ.get("BRAPI_TOKEN")
TICKERS = os.environ.get("B3_TICKERS", "PETR4,VALE3,ITUB4").split(",")
TOPIC = "automesh.market.b3_quotes.v1"
MAX_RETRIES = 3


def fetch_quotes(tickers: list[str]) -> list[dict]:
    params = {"token": BRAPI_TOKEN} if BRAPI_TOKEN else {}

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                f"{BRAPI_BASE_URL}/{','.join(tickers)}",
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
        except requests.RequestException as e:
            wait_seconds = 2 ** attempt
            logger.warning("brapi.dev fetch failed (attempt %d): %s — retrying in %ds", attempt, e, wait_seconds)
            time.sleep(wait_seconds)

    logger.error("brapi.dev unreachable after %d retries — skipping this poll cycle", MAX_RETRIES)
    return []


def publish_quotes(quotes: list[dict], producer: Producer | None = None) -> int:
    producer = producer or Producer(PRODUCER_CONFIG)

    def on_delivery(err, msg) -> None:
        if err:
            logger.error("Delivery failed: %s", err)

    published = 0
    for quote in quotes:
        ticker = quote.get("symbol")
        price = quote.get("regularMarketPrice")
        if ticker is None or price is None:
            logger.warning("Skipping malformed quote payload: %s", quote)
            continue

        payload = {
            "ticker": ticker,
            "price": price,
            "volume": quote.get("regularMarketVolume"),
            "quote_timestamp": quote.get("regularMarketTime"),
        }
        producer.produce(
            topic=TOPIC,
            key=ticker.encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
            on_delivery=on_delivery,
        )
        published += 1

    producer.flush()
    return published


def run() -> int:
    return publish_quotes(fetch_quotes(TICKERS))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
