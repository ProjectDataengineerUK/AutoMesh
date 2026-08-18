"""Desired-state planning with deterministic, idempotent object names."""

from __future__ import annotations

PRODUCTS = ("market_insights", "lost_sales", "finops_costs", "platform_health")


def desired_objects(catalog: str, schema: str) -> list[dict[str, str]]:
    prefix = f"{catalog}.{schema}"
    return [{"kind": "table", "name": f"{prefix}.{product}"} for product in PRODUCTS] + [
        {"kind": "view", "name": f"{prefix}.executive"},
        {"kind": "view", "name": f"{prefix}.operational"},
    ]


def plan(catalog: str | None, schema: str | None, existing: set[str] | None = None) -> list[dict[str, str]]:
    if not catalog or not schema:
        raise ValueError("catalog and schema are required to build a plan")
    existing = existing or set()
    return [
        {**obj, "action": "update" if obj["name"] in existing else "create"}
        for obj in desired_objects(catalog, schema)
    ]
