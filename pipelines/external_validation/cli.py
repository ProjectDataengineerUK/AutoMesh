"""Command-line entry point for the external validation harness."""

from __future__ import annotations

import argparse
import json

from .config import ValidationConfig
from .evidence import build_report, write_json
from .gates import run_preflight
from .planner import plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight", "dry-run", "publish"), default=None)
    parser.add_argument("--confirm-publish", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    config = ValidationConfig.from_env(args.mode, args.confirm_publish)
    gates = run_preflight(config)
    objects = []
    if config.catalog and config.schema and all(g.status == "PASS" for g in gates):
        objects = plan(config.catalog, config.schema)
    report = build_report(config.redacted(), [g.__dict__ for g in gates], objects)
    if args.report:
        write_json(report, args.report)
    print(json.dumps(report, indent=2, sort_keys=True))
    statuses = {g.status for g in gates}
    return 1 if "FAIL" in statuses else 0


if __name__ == "__main__":
    raise SystemExit(main())
