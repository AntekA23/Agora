"""Instagram publisher using Meta Graph API."""

import httpx
from datetime import datetime
from typing import Any

from app.models.platform_credentials import (
    Platform,
    PlatformCredentials,
    PublishResult,
    PostStats,
)
from app.services.publishers.base import BasePublisher


class InstagramPublisher(BasePublisher):
    """Publisher for Instagram via Meta Graph API."""

    platform = Platform.INSTAGRAM
    BASE_URL = "https://graph.facebook.com/v18.0"

    async def publish(
        self,
        content: dict[str, Any],
        credentials: PlatformCredentials,
        media_urls: list[str] | None = None,
    ) -> PublishResult:
        """
        Publish content to Instagram.

        For Instagram, the flow is:
        1. Create a media container with image/video URL
        2. Publish the container

        Note: Instagram requires a Business/Creator account connected to a Facebook Page.
        """
        if not credentials.access_token:
            return self._build_error_result("No access token available")

        if not credentials.platform_user_id:
            return self._build_error_result("No Instagram account ID available")

        try:
            async with httpx.AsyncClient() as client:
                # Build caption from content
                caption = self._build_caption(content)

                # If we have media, create a media container first
                if media_urls and len(media_urls) > 0:
                    # Step 1: Create media container
                    container_result = await self._create_media_container(
                        client=client,
                        ig_user_id=credentials.platform_user_id,
                        access_token=credentials.access_token,
                        image_url=media_urls[0],
                        caption=caption,
                    )

                    if not container_result.get("id"):
                        return self._build_error_result(
                            f"Failed to create media container: {container_result.get('error', 'Unknown error')}"
                        )

                    container_id = container_result["id"]

                    # Step 2: Publish the container
                    publish_result = await self._publish_container(
                        client=client,
                        ig_user_id=credentials.platform_user_id,
                        access_token=credentials.access_token,
                        container_id=container_id,
                    )

                    if not publish_result.get("id"):
                        return self._build_error_result(
                            f"Failed to publish container: {publish_result.get('error', 'Unknown error')}"
                        )

                    post_id = publish_result["id"]

                else:
                    # Text-only posts are not supported on Instagram
                    # We need at least one image
                    return self._build_error_result(
                        "Instagram requires at least one image. Text-only posts are not supported."
                    )

                # Build post URL
                post_url = f"https://www.instagram.com/p/{post_id}/"

                return self._build_success_result(
                    post_id=post_id,
                    post_url=post_url,
                    raw_response=publish_result,
                )

        except httpx.HTTPError as e:
            return self._build_error_result(f"HTTP error: {str(e)}")
        except Exception as e:
            return self._build_error_result(f"Unexpected error: {str(e)}")

    async def _create_media_container(
        self,
        client: httpx.AsyncClient,
        ig_user_id: str,
        access_token: str,
        image_url: str,
        caption: str,
    ) -> dict:
        """Create a media container for Instagram."""
        url = f"{self.BASE_URL}/{ig_user_id}/media"

        response = await client.post(
            url,
            params={
                "image_url": image_url,
                "caption": caption,
                "access_token": access_token,
            },
        )

        return response.json()

    async def _publish_container(
        self,
        client: httpx.AsyncClient,
        ig_user_id: str,
        access_token: str,
        container_id: str,
    ) -> dict:
        """Publish a media container to Instagram."""
        url = f"{self.BASE_URL}/{ig_user_id}/media_publish"

        response = await client.post(
            url,
            params={
                "creation_id": container_id,
                "access_token": access_token,
            },
        )

        return response.json()

    def _build_caption(self, content: dict[str, Any]) -> str:
        """Build Instagram caption from content."""
        parts = []

        # Main text
        if content.get("text"):
            parts.append(content["text"])
        elif content.get("caption"):
            parts.append(content["caption"])

        # Hashtags
        if content.get("hashtags"):
            hashtags = content["hashtags"]
            if isinstance(hashtags, list):
                parts.append("\n\n" + " ".join(hashtags))
            elif isinstance(hashtags, str):
                parts.append("\n\n" + hashtags)

        return "".join(parts)

    async def validate_credentials(
        self,
        credentials: PlatformCredentials,
    ) -> bool:
        """Validate Instagram credentials."""
        if not credentials.access_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/me"
                response = await client.get(
                    url,
                    params={"access_token": credentials.access_token},
                )

                data = response.json()
                return "error" not in data

        except Exception:
            return False

    async def refresh_token(
        self,
        credentials: PlatformCredentials,
    ) -> PlatformCredentials | None:
        """
        Refresh Instagram access token.

        Instagram long-lived tokens are valid for 60 days and can be refreshed.
        """
        if not credentials.access_token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/oauth/access_token"
                response = await client.get(
                    url,
                    params={
                        "grant_type": "ig_refresh_token",
                        "access_token": credentials.access_token,
                    },
                )

                data = response.json()

                if "access_token" in data:
                    credentials.access_token = data["access_token"]
                    credentials.token_expires_at = datetime.utcnow()  # + 60 days
                    credentials.updated_at = datetime.utcnow()
                    return credentials

                return None

        except Exception:
            return None

    async def get_post_stats(
        self,
        post_id: str,
        credentials: PlatformCredentials,
    ) -> PostStats | None:
        """Get engagement statistics for an Instagram post."""
        if not credentials.access_token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/{post_id}"
                response = await client.get(
                    url,
                    params={
                        "fields": "like_count,comments_count,impressions,reach,saved",
                        "access_token": credentials.access_token,
                    },
                )

                data = response.json()

                if "error" in data:
                    return None

                return PostStats(
                    likes=data.get("like_count", 0),
                    comments=data.get("comments_count", 0),
                    saves=data.get("saved", 0),
                    reach=data.get("reach", 0),
                    impressions=data.get("impressions", 0),
                )

        except Exception:
            return None

    async def delete_post(
        self,
        post_id: str,
        credentials: PlatformCredentials,
    ) -> bool:
        """Delete an Instagram post."""
        # Note: Instagram API doesn't support deleting posts via API
        # This would need to be done manually
        return False
