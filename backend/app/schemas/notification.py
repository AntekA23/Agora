"""Pydantic schemas for notifications."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class NotificationAction(BaseModel):
    """Action that can be taken from a notification."""

    label: str
    action_type: Literal["navigate", "approve", "reject", "dismiss"]
    action_url: str | None = None
    action_data: dict[str, Any] | None = None


class NotificationResponse(BaseModel):
    """Response schema for a notification."""

    id: str
    type: str
    priority: str
    title: str
    message: str
    icon: str | None = None
    related_type: str | None = None
    related_id: str | None = None
    action_url: str | None = None
    actions: list[NotificationAction] = Field(default_factory=list)
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Response schema for list of notifications."""

    items: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationCountResponse(BaseModel):
    """Response schema for notification count."""

    unread_count: int


class MarkReadRequest(BaseModel):
    """Request to mark notifications as read."""

    notification_ids: list[str] | None = Field(
        default=None,
        description="List of notification IDs to mark as read. If None, marks all as read.",
    )


class MarkReadResponse(BaseModel):
    """Response from marking notifications as read."""

    marked_count: int


class DismissRequest(BaseModel):
    """Request to dismiss notifications."""

    notification_ids: list[str] | None = Field(
        default=None,
        description="List of notification IDs to dismiss. If None, dismisses all.",
    )


class DismissResponse(BaseModel):
    """Response from dismissing notifications."""

    dismissed_count: int
