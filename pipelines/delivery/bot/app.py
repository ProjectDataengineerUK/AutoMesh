"""Framework adapter boundary.

Production must invoke ``handle_execute`` only after the official Teams authentication
middleware has validated the activity and supplied verified actor claims.
"""

from __future__ import annotations

from pipelines.delivery.bot.handler import handle_execute

__all__ = ["handle_execute"]
