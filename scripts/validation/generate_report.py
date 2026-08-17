"""Compatibility entrypoint for consolidated report generation."""

import importlib
import os
import sys


def main(arguments: list[str]) -> int:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, root)
    module = importlib.import_module("platform.validation.cli")
    return module.main(["report", *arguments])

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
