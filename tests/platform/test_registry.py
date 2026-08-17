from pathlib import Path
from platform.validation.registry import load_reason_codes, load_registry
from unittest.mock import patch

import pytest


def test_registry_contains_all_capabilities() -> None:
    registry = load_registry()
    assert [item.capability_id for item in registry] == [f"CAP-{index:02d}" for index in range(1, 11)]


def test_registry_rejects_incomplete_sequence() -> None:
    with patch.object(Path, "read_text", return_value="capabilities: []\n"):
        with pytest.raises(ValueError, match="CAP-01"):
            load_registry(Path("invalid.yaml"))


def test_reason_codes_include_missing_credential() -> None:
    assert "MISSING_CREDENTIAL" in load_reason_codes()
