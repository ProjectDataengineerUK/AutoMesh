from pipelines.ingestion.common.contract_validator import validate_batch


def test_poison_record_does_not_stop_valid_records() -> None:
    valid, rejected = validate_batch("infra_telemetry", [{"invalid": True}, {"invalid": False}])
    assert len(valid) + len(rejected) == 2
    assert rejected
