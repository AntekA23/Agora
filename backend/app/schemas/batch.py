"""Pydantic schemas for batch content generation."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """Date range for batch scheduling."""

    start: str = Field(..., description="Start date in ISO format")
    end: str = Field(..., description="End date in ISO format")


class BatchGenerationRequest(BaseModel):
    """Request to generate a batch of content."""

    content_type: str = Field(
        default="instagram_post",
        description="Type of content to generate",
    )
    platform: str = Field(
        default="instagram",
        description="Target platform",
    )
    count: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of content pieces to generate (1-30)",
    )
    theme: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Main theme/topic for the batch",
    )
    variety: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Content variety level",
    )
    date_range: DateRange | None = Field(
        default=None,
        description="Date range for scheduling (optional)",
    )
    auto_schedule: bool = Field(
        default=True,
        description="Whether to automatically schedule content",
    )
    require_approval: bool = Field(
        default=False,
        description="Whether content requires approval before publishing",
    )


class GeneratedItemContent(BaseModel):
    """Content of a generated item."""

    text: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    error: str | None = None


class GeneratedItem(BaseModel):
    """A single generated item in the batch."""

    index: int
    prompt: str
    content: GeneratedItemContent | None = None
    status: Literal["success", "failed"]
    error: str | None = None


class ScheduledItem(BaseModel):
    """A scheduled item from the batch."""

    id: str
    title: str
    scheduled_for: str | None = None
    status: str


class BatchGenerationResponse(BaseModel):
    """Response from batch generation."""

    total_requested: int
    total_generated: int
    total_failed: int
    total_scheduled: int
    generated_items: list[GeneratedItem]
    scheduled_items: list[ScheduledItem]


class BatchPreviewItem(BaseModel):
    """Preview item for batch confirmation."""

    index: int
    title: str
    content_preview: str = Field(..., description="First 200 chars of content")
    scheduled_for: str | None = None
    platform: str
    status: str


class BatchPreviewResponse(BaseModel):
    """Preview response for batch before final confirmation."""

    batch_id: str
    items: list[BatchPreviewItem]
    total_count: int
    date_range_start: str | None = None
    date_range_end: str | None = None


class BatchConfirmRequest(BaseModel):
    """Request to confirm a batch generation."""

    batch_id: str
    include_items: list[int] | None = Field(
        default=None,
        description="List of item indices to include (None = include all)",
    )
    exclude_items: list[int] | None = Field(
        default=None,
        description="List of item indices to exclude",
    )


class BatchConfirmResponse(BaseModel):
    """Response from batch confirmation."""

    confirmed: int
    excluded: int
    scheduled_items: list[ScheduledItem]


class BatchStatsResponse(BaseModel):
    """Statistics about batch generation usage."""

    total_batches: int
    total_items_generated: int
    total_items_scheduled: int
    total_items_published: int
    average_batch_size: float
    most_used_platform: str | None = None
