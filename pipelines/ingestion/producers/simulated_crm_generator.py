from __future__ import annotations

import json
import logging
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

RAW_BASE_PATH = Path("data/raw/crm_lost_sales")
LOST_REASONS = ["price", "competitor", "timing", "feature_gap", "no_budget"]
ACCOUNT_NAMES = ["Acme Corp", "Globex", "Initech", "Umbrella Ltda", "Wayne Enterprises"]


def generate_lost_sales_batch(count: int = 15) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "opportunity_id": f"opp-{uuid.uuid4().hex[:10]}",
            "account_name": random.choice(ACCOUNT_NAMES),
            "lost_reason": random.choice(LOST_REASONS),
            "estimated_value": round(random.uniform(5_000, 250_000), 2),
            "lost_at": now,
        }
        for _ in range(count)
    ]


def write_batch(records: list[dict], execution_date: str, base_path: Path = RAW_BASE_PATH) -> Path:
    target_dir = base_path / execution_date
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "lost_sales.json"

    with target_file.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    return target_file


def run(execution_date: str | None = None) -> Path:
    execution_date = execution_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return write_batch(generate_lost_sales_batch(), execution_date)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    output_path = run()
    logger.info("CRM Lost Sales batch written to %s", output_path)
