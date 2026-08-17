"""Scoped correlation metadata based on context variables."""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_context: ContextVar[dict[str, str] | None] = ContextVar("automesh_observability_context", default=None)


def current_context() -> dict[str, str]:
    return dict(_context.get() or {})


@contextmanager
def bind_context(**values: str) -> Iterator[dict[str, str]]:
    normalized = {key: str(value) for key, value in values.items() if value is not None}
    token = _context.set({**current_context(), **normalized})
    try:
        yield current_context()
    finally:
        _context.reset(token)
