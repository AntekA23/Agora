"""Notification model for in-app notifications."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Types of notifications."""

    # Content approval
    PENDING_APPROVAL = "pending_approval"
    CONTENT_APPROVED = "content_approved"
    CONTENT_REJECTED = "content_rejected"
    CONTENT_PUBLISHED = "content_published"
    CONTENT_FAILED = "content_failed"

    # Schedule rules
    RULE_GENERATED = "rule_generated"
    RULE_ERROR = "rule_error"

    # Batch
    BATCH_COMPLETED = "batch_completed"
    BATCH_FAILED = "batch_failed"

    # System
    SYSTEM_INFO = "system_info"
    SYSTEM_WARNING = "system_warning"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationAction(BaseModel):
    """Action that can be taken from a notification."""

    label: str
    action_type: str  # "navigate", "approve", "reject", "dismiss"
    action_url: str | None = None
    action_data: dict[str, Any] | None = None


class Notification(BaseModel):
    """In-app notification model."""

    # Identity
    id: str | None = None
    company_id: str
    user_id: str  # Target user

    # Content
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    message: str
    icon: str | None = None  # Lucide icon name

    # Related entity
    related_type: str | None = None  # "scheduled_content", "schedule_rule", etc.
    related_id: str | None = None

    # Actions
    actions: list[NotificationAction] = Field(default_factory=list)
    action_url: str | None = None  # Primary action URL

    # Status
    is_read: bool = False
    read_at: datetime | None = None
    is_dismissed: bool = False
    dismissed_at: datetime | None = None

    # Expiration
    expires_at: datetime | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)


# MongoDB document structure
NOTIFICATION_COLLECTION = "notifications"

NOTIFICATION_INDEXES = [
    {"keys": [("user_id", 1), ("is_read", 1), ("created_at", -1)]},
    {"keys": [("company_id", 1), ("created_at", -1)]},
    {"keys": [("expires_at", 1)], "expireAfterSeconds": 0},  # TTL index
]
