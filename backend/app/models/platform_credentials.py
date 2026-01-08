"""Platform credentials model for storing OAuth tokens and API keys."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Platform(str, Enum):
    """Supported social media platforms."""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"


class ConnectionStatus(str, Enum):
    """Status of platform connection."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    ERROR = "error"


class PlatformCredentials(BaseModel):
    """OAuth credentials for a social media platform."""

    # Identity
    id: str | None = None
    company_id: str
    platform: Platform

    # Connection info
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    connected_at: datetime | None = None
    connected_by: str | None = None  # user_id

    # OAuth tokens
    access_token: str | None = None
    refresh_token: str | None = None
    token_expires_at: datetime | None = None

    # Platform-specific IDs
    platform_user_id: str | None = None  # e.g., Instagram user ID
    platform_username: str | None = None  # e.g., @username
    platform_page_id: str | None = None  # For Facebook pages
    platform_page_name: str | None = None

    # Permissions/scopes
    granted_scopes: list[str] = Field(default_factory=list)

    # Stats
    last_used_at: datetime | None = None
    last_error: str | None = None
    total_posts_published: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PublishResult(BaseModel):
    """Result of publishing content to a platform."""

    success: bool
    platform: Platform
    post_id: str | None = None
    post_url: str | None = None
    error_message: str | None = None
    error_code: str | None = None
    published_at: datetime | None = None
    raw_response: dict[str, Any] | None = None


class PostStats(BaseModel):
    """Statistics for a published post."""

    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    reach: int = 0
    impressions: int = 0
    engagement_rate: float = 0.0
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


# MongoDB collection name
PLATFORM_CREDENTIALS_COLLECTION = "platform_credentials"

# Indexes
PLATFORM_CREDENTIALS_INDEXES = [
    {"keys": [("company_id", 1), ("platform", 1)], "unique": True},
    {"keys": [("status", 1)]},
    {"keys": [("token_expires_at", 1)]},
]
