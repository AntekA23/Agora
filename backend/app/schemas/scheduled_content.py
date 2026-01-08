"""Pydantic schemas for scheduled content API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.scheduled_content import ContentPlatform, ContentStatus, ContentType


class ScheduledContentCreate(BaseModel):
    """Create new scheduled content."""

    title: str = Field(..., min_length=1, max_length=200)
    content_type: ContentType
    platform: ContentPlatform
    content: dict[str, Any] = Field(default_factory=dict)
    media_urls: list[str] = Field(default_factory=list)

    # Optional scheduling
    scheduled_for: datetime | None = None
    timezone: str = "Europe/Warsaw"

    # Source tracking (optional)
    source_task_id: str | None = None
    source_conversation_id: str | None = None

    # Approval settings
    requires_approval: bool = False


class ScheduledContentUpdate(BaseModel):
    """Update scheduled content."""

    title: str | None = None
    content: dict[str, Any] | None = None
    media_urls: list[str] | None = None
    scheduled_for: datetime | None = None
    timezone: str | None = None
    status: ContentStatus | None = None
    requires_approval: bool | None = None


class ScheduledContentResponse(BaseModel):
    """Scheduled content response."""

    id: str
    company_id: str
    created_by: str

    title: str
    content_type: ContentType
    platform: ContentPlatform
    content: dict[str, Any]
    media_urls: list[str]

    status: ContentStatus
    scheduled_for: datetime | None
    timezone: str
    published_at: datetime | None

    source_task_id: str | None
    source_conversation_id: str | None
    source_rule_id: str | None

    platform_post_id: str | None
    platform_post_url: str | None
    engagement_stats: dict[str, Any] | None

    error_message: str | None
    retry_count: int

    requires_approval: bool
    approved_by: str | None
    approved_at: datetime | None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduledContentListResponse(BaseModel):
    """List of scheduled content response."""

    items: list[ScheduledContentResponse]
    total: int
    page: int
    per_page: int


class ScheduledContentStats(BaseModel):
    """Statistics for scheduled content."""

    total: int
    by_status: dict[str, int]
    by_platform: dict[str, int]
    scheduled_this_week: int
    published_this_week: int


class QueueFilters(BaseModel):
    """Filters for queue listing."""

    status: list[ContentStatus] | None = None
    platform: list[ContentPlatform] | None = None
    content_type: list[ContentType] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = None


class BulkActionRequest(BaseModel):
    """Request for bulk actions on multiple items."""

    ids: list[str] = Field(..., min_length=1)
    action: str = Field(..., description="approve, reject, delete, reschedule")
    # For reschedule action
    new_scheduled_for: datetime | None = None


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""

    success_count: int
    failed_count: int
    failed_ids: list[str] = Field(default_factory=list)
    errors: dict[str, str] = Field(default_factory=dict)


class ApproveContentRequest(BaseModel):
    """Request to approve content for publishing."""

    # Optional: reschedule while approving
    scheduled_for: datetime | None = None


class PublishNowRequest(BaseModel):
    """Request to publish content immediately."""

    pass  # No additional fields needed
