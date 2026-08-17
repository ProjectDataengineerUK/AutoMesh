"""Run the repository DagBag validator with a bounded subprocess timeout."""

import subprocess
import sys
from pathlib import Path


def validate(dags_path: Path, timeout_seconds: int = 300) -> int:
    result = subprocess.run(
        [sys.executable, "scripts/validate_dagbag.py", str(dags_path)],
        check=False,
        timeout=timeout_seconds,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(validate(Path(sys.argv[1])))
