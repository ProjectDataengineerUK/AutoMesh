from __future__ import annotations

import hashlib


def notification_key(kind: str, resource: str, version: str, recipient: str, channel: str) -> str:
    canonical = "|".join((kind, resource, version, recipient, channel))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
