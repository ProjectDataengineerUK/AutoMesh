from __future__ import annotations

import os

from pipelines.delivery.common.sqlite_storage import SQLiteDeliveryStore


def get_store() -> SQLiteDeliveryStore:
    return SQLiteDeliveryStore(os.environ.get("DELIVERY_STATE_PATH", "data/delivery/delivery.db"))
