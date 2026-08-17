"""AutoMesh platform services with compatibility for Python's platform module."""

import os
from pathlib import Path

_stdlib_platform = Path(os.__file__).resolve().with_name("platform.py")
exec(compile(_stdlib_platform.read_bytes(), str(_stdlib_platform), "exec"), globals(), globals())
