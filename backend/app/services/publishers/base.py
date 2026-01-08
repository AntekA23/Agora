"""Base publisher class for social media platforms."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.models.platform_credentials import (
    Platform,
    PlatformCredentials,
    PublishResult,
    PostStats,
)


class BasePublisher(ABC):
    """Abstract base class for social media publishers."""

    platform: Platform

    @abstractmethod
    async def publish(
        self,
        content: dict[str, Any],
        credentials: PlatformCredentials,
        media_urls: list[str] | None = None,
    ) -> PublishResult:
        """
        Publish content to the platform.

        Args:
            content: Content to publish (text, hashtags, etc.)
            credentials: OAuth credentials for the platform
            media_urls: Optional list of media URLs to include

        Returns:
            PublishResult with success status and post details
        """
        pass

    @abstractmethod
    async def validate_credentials(
        self,
        credentials: PlatformCredentials,
    ) -> bool:
        """
        Validate that credentials are still valid.

        Args:
            credentials: OAuth credentials to validate

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

    @abstractmethod
    async def refresh_token(
        self,
        credentials: PlatformCredentials,
    ) -> PlatformCredentials | None:
        """
        Refresh expired OAuth tokens.

        Args:
            credentials: Credentials with refresh token

        Returns:
            Updated credentials with new access token, or None if refresh failed
        """
        pass

    @abstractmethod
    async def get_post_stats(
        self,
        post_id: str,
        credentials: PlatformCredentials,
    ) -> PostStats | None:
        """
        Get engagement statistics for a published post.

        Args:
            post_id: Platform-specific post ID
            credentials: OAuth credentials

        Returns:
            PostStats with engagement metrics, or None if unavailable
        """
        pass

    @abstractmethod
    async def delete_post(
        self,
        post_id: str,
        credentials: PlatformCredentials,
    ) -> bool:
        """
        Delete a published post.

        Args:
            post_id: Platform-specific post ID
            credentials: OAuth credentials

        Returns:
            True if deletion was successful
        """
        pass

    def _build_error_result(
        self,
        error_message: str,
        error_code: str | None = None,
    ) -> PublishResult:
        """Build a failed PublishResult."""
        return PublishResult(
            success=False,
            platform=self.platform,
            error_message=error_message,
            error_code=error_code,
        )

    def _build_success_result(
        self,
        post_id: str,
        post_url: str | None = None,
        raw_response: dict[str, Any] | None = None,
    ) -> PublishResult:
        """Build a successful PublishResult."""
        return PublishResult(
            success=True,
            platform=self.platform,
            post_id=post_id,
            post_url=post_url,
            published_at=datetime.utcnow(),
            raw_response=raw_response,
        )
