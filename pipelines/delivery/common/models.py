from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotificationType(StrEnum):
    PR_REVIEW = "pr_review"
    MODEL_PROMOTION = "model_promotion"
    FINOPS = "finops"
    REPORT = "report"


class Channel(StrEnum):
    TEAMS = "teams"
    OUTLOOK = "outlook"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    DELIVERING = "delivering"
    DELIVERED = "delivered"
    RETRYABLE = "retryable"
    FAILED = "failed"


class DecisionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ActionType(StrEnum):
    REVIEW_PR = "review_pr"
    PROMOTE_MODEL = "promote_model"
    ACK_FINOPS = "ack_finops"


class ApplicationStatus(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    STALE_PRECONDITION = "stale_precondition"


@dataclass
class Notification:
    correlation_id: str
    notification_type: NotificationType
    recipient_ref: str
    channel: Channel
    payload: dict[str, Any]
    idempotency_key: str
    decision_id: str | None = None
    notification_id: str = field(default_factory=lambda: str(uuid4()))
    status: NotificationStatus = NotificationStatus.PENDING
    attempt_count: int = 0
    external_message_id: str | None = None
    lease_owner: str | None = None
    lease_until: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class Decision:
    correlation_id: str
    action_type: ActionType
    resource_ref: str
    expected_state: dict[str, Any]
    expires_at: datetime
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    actor_id: str | None = None
    status: DecisionStatus = DecisionStatus.PENDING
    reason: str | None = None
    decided_at: datetime | None = None
    application_status: ApplicationStatus = ApplicationStatus.NOT_APPLICABLE
    revision: int = 0


@dataclass
class Application:
    decision_id: str
    action_type: ActionType
    resource_ref: str
    expected_state: dict[str, Any]
    application_id: str = field(default_factory=lambda: str(uuid4()))
    status: ApplicationStatus = ApplicationStatus.PENDING
    result_detail: str | None = None
    attempt_count: int = 0
