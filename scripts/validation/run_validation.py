"""AutoMesh validation CLI entrypoint."""

import importlib
import os
import sys


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, root)
    module = importlib.import_module("platform.validation.cli")
    return module.main()

if __name__ == "__main__":
    raise SystemExit(main())
