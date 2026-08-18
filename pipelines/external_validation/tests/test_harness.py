from pipelines.external_validation.config import ValidationConfig
from pipelines.external_validation.evidence import build_report
from pipelines.external_validation.gates import run_preflight
from pipelines.external_validation.planner import plan
from pipelines.external_validation.reconcile import reconcile


def test_missing_context_is_explicit_skip():
    result = run_preflight(ValidationConfig())
    assert result[0].status == "SKIP_EXTERNAL"


def test_publish_requires_confirmation():
    assert ValidationConfig("publish").validate() == ["publish requires confirm_publish"]


def test_invalid_host_fails():
    result = run_preflight(ValidationConfig(host="workspace.local"))
    assert result[0].code == "CONFIG_INVALID"


def test_plan_is_idempotent():
    first = plan("main", "gold")
    second = plan("main", "gold", {item["name"] for item in first})
    assert all(item["action"] == "update" for item in second)


def test_reconciliation_respects_tolerance():
    result = reconcile({"revenue": 100.0}, {"revenue": 100.4}, tolerance=0.5)
    assert result[0]["status"] == "PASS"


def test_missing_metric_fails():
    assert reconcile({"revenue": 100.0}, {})[0]["status"] == "FAIL"


def test_report_has_audit_fields():
    report = build_report({}, [], commit="abc")
    assert report["commit"] == "abc"
    assert report["timestamp"]
