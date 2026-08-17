from __future__ import annotations

from pathlib import Path

from pipelines.ingestion.common.contract_validator import validate_batch


def test_valid_b3_quote_passes() -> None:
    records = [{"ticker": "PETR4", "price": 38.5, "volume": 1000, "quote_timestamp": "2026-07-31T10:00:00Z"}]

    valid, invalid = validate_batch("b3_quotes", records)

    assert valid == records
    assert invalid == []


def test_null_required_field_routes_to_invalid() -> None:
    records = [{"ticker": None, "price": 38.5, "volume": 1000, "quote_timestamp": "2026-07-31T10:00:00Z"}]

    valid, invalid = validate_batch("b3_quotes", records)

    assert valid == []
    assert len(invalid) == 1
    assert invalid[0]["_failure_reason"] == "null_violation:ticker"


def test_type_mismatch_routes_to_invalid() -> None:
    records = [{"ticker": "PETR4", "price": "not-a-number", "volume": 1000, "quote_timestamp": "2026-07-31T10:00:00Z"}]

    valid, invalid = validate_batch("b3_quotes", records)

    assert valid == []
    assert invalid[0]["_failure_reason"] == "type_mismatch:price"


def test_optional_field_missing_is_valid() -> None:
    records = [{"ticker": "VALE3", "price": 65.2, "quote_timestamp": "2026-07-31T10:00:00Z"}]

    valid, invalid = validate_batch("b3_quotes", records)

    assert valid == records
    assert invalid == []


def test_negative_price_violates_minimum_constraint() -> None:
    records = [{"ticker": "ITUB4", "price": -1.0, "quote_timestamp": "2026-07-31T10:00:00Z"}]

    valid, invalid = validate_batch("b3_quotes", records)

    assert valid == []
    assert invalid[0]["_failure_reason"] == "constraint_violation:price"


def test_mixed_batch_splits_valid_and_invalid() -> None:
    records = [
        {"ticker": "PETR4", "price": 38.5, "quote_timestamp": "2026-07-31T10:00:00Z"},
        {"ticker": None, "price": 38.5, "quote_timestamp": "2026-07-31T10:00:00Z"},
    ]

    valid, invalid = validate_batch("b3_quotes", records)

    assert len(valid) == 1
    assert len(invalid) == 1


def test_crm_lost_sales_contract() -> None:
    records = [
        {
            "opportunity_id": "opp-1",
            "account_name": "Acme Corp",
            "lost_reason": "price",
            "estimated_value": 12000.0,
            "lost_at": "2026-07-31T10:00:00Z",
        }
    ]

    valid, invalid = validate_batch("crm_lost_sales", records)

    assert valid == records
    assert invalid == []


def test_custom_contracts_dir_is_used_when_provided() -> None:
    rag_contracts_dir = Path(__file__).resolve().parent.parent.parent / "rag" / "contracts"
    records = [
        {
            "document_id": "doc-1",
            "source_path": "/sites/x/report.txt",
            "chunk_index": 0,
            "chunk_text": "conteúdo",
            "updated_at": "2026-08-10T10:00:00Z",
        }
    ]

    valid, invalid = validate_batch("sharepoint_documents", records, contracts_dir=rag_contracts_dir)

    assert valid == records
    assert invalid == []


def test_custom_contracts_dir_still_routes_invalid_records() -> None:
    rag_contracts_dir = Path(__file__).resolve().parent.parent.parent / "rag" / "contracts"
    records = [{"document_id": None, "source_path": "/x", "chunk_index": 0, "chunk_text": "y", "updated_at": "z"}]

    valid, invalid = validate_batch("sharepoint_documents", records, contracts_dir=rag_contracts_dir)

    assert valid == []
    assert invalid[0]["_failure_reason"] == "null_violation:document_id"
