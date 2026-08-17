"""Command line interface for validation, inventory and reporting."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from platform.validation.inventory import collect_inventory
from platform.validation.models import Evidence
from platform.validation.registry import load_registry
from platform.validation.report import build_report, write_report


def current_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        check=False,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNVERSIONED"


def load_evidence(directory: Path) -> tuple[Evidence, ...]:
    if not directory.exists():
        return ()
    return tuple(
        Evidence.from_dict(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(directory.glob("*.json"))
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="automesh-validation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    inventory_parser = subparsers.add_parser("inventory")
    inventory_parser.add_argument("--environment", default="local")
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--evidence-dir", type=Path, default=Path("artifacts/validation/evidence"))
    report_parser.add_argument("--output-dir", type=Path, default=Path("artifacts/validation/latest"))
    arguments = parser.parse_args(argv)
    capabilities = load_registry()
    if arguments.command == "inventory":
        inventory = collect_inventory(capabilities, arguments.environment)
        print(json.dumps(inventory.to_dict(), indent=2))
        return 0
    evidence = load_evidence(arguments.evidence_dir)
    report = build_report(capabilities, evidence, datetime.now(timezone.utc), current_commit())
    json_path, markdown_path = write_report(report, arguments.output_dir)
    print(f"wrote {json_path} and {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
