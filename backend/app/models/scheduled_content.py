"""Scheduled content model for content queue and publishing."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.models.base import MongoBaseModel


class ContentStatus(str, Enum):
    """Status of scheduled content."""

    DRAFT = "draft"  # Saved but not scheduled
    QUEUED = "queued"  # In queue, no specific time
    SCHEDULED = "scheduled"  # Scheduled for specific time
    PENDING_APPROVAL = "pending_approval"  # Waiting for user approval
    PUBLISHING = "publishing"  # Currently being published
    PUBLISHED = "published"  # Successfully published
    FAILED = "failed"  # Publication failed


class ContentPlatform(str, Enum):
    """Target platform for content."""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    EMAIL = "email"


class ContentType(str, Enum):
    """Type of content."""

    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_REEL = "instagram_reel"
    FACEBOOK_POST = "facebook_post"
    LINKEDIN_POST = "linkedin_post"
    TWITTER_POST = "twitter_post"
    EMAIL_NEWSLETTER = "email_newsletter"


class ScheduledContent(MongoBaseModel):
    """Content scheduled for publication."""

    # Identification
    company_id: str
    created_by: str  # user_id

    # Content details
    title: str  # Working title for the user
    content_type: ContentType
    platform: ContentPlatform
    content: dict[str, Any] = Field(default_factory=dict)
    # Content structure example:
    # {
    #     "text": "Post text...",
    #     "hashtags": ["#tag1", "#tag2"],
    #     "caption": "...",
    #     "cta": "Link in bio!"
    # }

    # Media
    media_urls: list[str] = Field(default_factory=list)  # URLs to images/videos

    # Status
    status: ContentStatus = ContentStatus.DRAFT

    # Scheduling
    scheduled_for: datetime | None = None  # When to publish
    timezone: str = "Europe/Warsaw"  # User's timezone
    published_at: datetime | None = None  # When actually published

    # Source tracking
    source_task_id: str | None = None  # Task that generated this content
    source_conversation_id: str | None = None  # Conversation that generated this
    source_rule_id: str | None = None  # Automation rule that generated this

    # Publication metadata
    platform_post_id: str | None = None  # ID of post on platform after publishing
    platform_post_url: str | None = None  # URL to the published post

    # Engagement stats (populated after publishing)
    engagement_stats: dict[str, Any] | None = None
    # Example: {"likes": 24, "comments": 3, "shares": 1, "reach": 500}

    # Error handling
    error_message: str | None = None  # Error if failed
    retry_count: int = 0  # Number of retry attempts
    max_retries: int = 3  # Maximum retry attempts

    # Approval settings
    requires_approval: bool = False
    approved_by: str | None = None  # user_id who approved
    approved_at: datetime | None = None
