from pipelines.gold.jobs.publish_databricks import publish_lakeview


def test_missing_external_configuration_skips() -> None:
    result = publish_lakeview(True, {}, "test-target", "test-target")
    assert result.status == "SKIP_WITH_REASON"
    assert result.reason_code == "MISSING_CREDENTIAL"


def test_external_disabled_skips_without_mutation() -> None:
    result = publish_lakeview(False, {}, "test-target", "test-target")
    assert result.reason_code == "EXTERNAL_DISABLED"


def test_allowlisted_configured_target_is_ready() -> None:
    inventory = {"DATABRICKS_HOST": "host", "DATABRICKS_TOKEN": "token", "DATABRICKS_SQL_WAREHOUSE_ID": "warehouse"}
    result = publish_lakeview(True, inventory, "test-target", "test-target")
    assert result.status == "PASS"
