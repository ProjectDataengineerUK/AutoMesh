from __future__ import annotations

import re
from pathlib import PurePosixPath

ALLOWED_PATH_PREFIXES = (
    "pipelines/ingestion/contracts/",
    "pipelines/ingestion/producers/",
    "pipelines/ingestion/dags/",
    "pipelines/ingestion/common/",
    "pipelines/processing/",
    "pipelines/insights/",
    "pipelines/finops/",
    "pipelines/self_healing/",
    "pipelines/rag/",
)

DANGEROUS_PATTERNS = [
    re.compile(r"os\.system\("),
    re.compile(r"subprocess\."),
    re.compile(r"\beval\("),
    re.compile(r"\bexec\("),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM\s+\w+\s*;", re.IGNORECASE),
    re.compile(r"(?i)(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]+['\"]"),
]


def check_allowlist(target_file: str) -> str | None:
    if "\\" in target_file:
        return f"invalid_path:{target_file}"

    path = PurePosixPath(target_file)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        return f"invalid_path:{target_file}"

    normalized = path.as_posix()
    if not any(normalized.startswith(prefix) for prefix in ALLOWED_PATH_PREFIXES):
        return f"out_of_scope_path:{target_file}"
    return None


def check_content(diff: str) -> str | None:
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(diff):
            return f"dangerous_pattern:{pattern.pattern}"
    return None


def evaluate(target_file: str, diff: str) -> str | None:
    return check_allowlist(target_file) or check_content(diff)
