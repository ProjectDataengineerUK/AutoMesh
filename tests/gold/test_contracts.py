from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2] / "pipelines" / "gold"


def test_product_contracts_have_required_metadata() -> None:
    payload = yaml.safe_load((ROOT / "contracts" / "gold_products.yaml").read_text(encoding="utf-8"))
    assert len(payload["products"]) == 4
    for product in payload["products"]:
        assert product["id"].startswith("gold_")
        assert product["key"] in product["required"]
        assert product["watermark"] in product["required"]


def test_metric_registry_references_products() -> None:
    metrics = yaml.safe_load((ROOT / "contracts" / "metric_registry.yaml").read_text(encoding="utf-8"))["metrics"]
    product_payload = yaml.safe_load((ROOT / "contracts" / "gold_products.yaml").read_text(encoding="utf-8"))
    products = {product["id"] for product in product_payload["products"]}
    assert len(metrics) >= 4
    assert all(metric["source_product"] in products for metric in metrics)
