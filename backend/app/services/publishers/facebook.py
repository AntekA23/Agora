"""Facebook publisher using Graph API."""

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


class FacebookPublisher(BasePublisher):
    """Publisher for Facebook Pages via Graph API."""

    platform = Platform.FACEBOOK
    BASE_URL = "https://graph.facebook.com/v18.0"

    async def publish(
        self,
        content: dict[str, Any],
        credentials: PlatformCredentials,
        media_urls: list[str] | None = None,
    ) -> PublishResult:
        """
        Publish content to a Facebook Page.

        Supports:
        - Text posts
        - Photo posts (single image)
        - Link posts
        """
        if not credentials.access_token:
            return self._build_error_result("No access token available")

        page_id = credentials.platform_page_id or credentials.platform_user_id
        if not page_id:
            return self._build_error_result("No Facebook Page ID available")

        try:
            async with httpx.AsyncClient() as client:
                message = self._build_message(content)

                if media_urls and len(media_urls) > 0:
                    # Photo post
                    result = await self._publish_photo(
                        client=client,
                        page_id=page_id,
                        access_token=credentials.access_token,
                        photo_url=media_urls[0],
                        message=message,
                    )
                else:
                    # Text post
                    result = await self._publish_text(
                        client=client,
                        page_id=page_id,
                        access_token=credentials.access_token,
                        message=message,
                    )

                if "error" in result:
                    error = result["error"]
                    return self._build_error_result(
                        error_message=error.get("message", "Unknown error"),
                        error_code=str(error.get("code", "")),
                    )

                post_id = result.get("id") or result.get("post_id")
                if not post_id:
                    return self._build_error_result("No post ID in response")

                # Build post URL
                post_url = f"https://www.facebook.com/{post_id}"

                return self._build_success_result(
                    post_id=post_id,
                    post_url=post_url,
                    raw_response=result,
                )

        except httpx.HTTPError as e:
            return self._build_error_result(f"HTTP error: {str(e)}")
        except Exception as e:
            return self._build_error_result(f"Unexpected error: {str(e)}")

    async def _publish_text(
        self,
        client: httpx.AsyncClient,
        page_id: str,
        access_token: str,
        message: str,
    ) -> dict:
        """Publish a text post to Facebook."""
        url = f"{self.BASE_URL}/{page_id}/feed"

        response = await client.post(
            url,
            data={
                "message": message,
                "access_token": access_token,
            },
        )

        return response.json()

    async def _publish_photo(
        self,
        client: httpx.AsyncClient,
        page_id: str,
        access_token: str,
        photo_url: str,
        message: str,
    ) -> dict:
        """Publish a photo post to Facebook."""
        url = f"{self.BASE_URL}/{page_id}/photos"

        response = await client.post(
            url,
            data={
                "url": photo_url,
                "message": message,
                "access_token": access_token,
            },
        )

        return response.json()

    def _build_message(self, content: dict[str, Any]) -> str:
        """Build Facebook message from content."""
        parts = []

        if content.get("text"):
            parts.append(content["text"])
        elif content.get("caption"):
            parts.append(content["caption"])

        # Add hashtags
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
        """Validate Facebook credentials."""
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
        Refresh Facebook access token.

        Facebook Page tokens don't expire if they're long-lived tokens
        obtained through the proper OAuth flow.
        """
        if not credentials.access_token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/oauth/access_token"
                response = await client.get(
                    url,
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": "",  # Would come from settings
                        "client_secret": "",  # Would come from settings
                        "fb_exchange_token": credentials.access_token,
                    },
                )

                data = response.json()

                if "access_token" in data:
                    credentials.access_token = data["access_token"]
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
        """Get engagement statistics for a Facebook post."""
        if not credentials.access_token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/{post_id}"
                response = await client.get(
                    url,
                    params={
                        "fields": "likes.summary(true),comments.summary(true),shares",
                        "access_token": credentials.access_token,
                    },
                )

                data = response.json()

                if "error" in data:
                    return None

                return PostStats(
                    likes=data.get("likes", {}).get("summary", {}).get("total_count", 0),
                    comments=data.get("comments", {}).get("summary", {}).get("total_count", 0),
                    shares=data.get("shares", {}).get("count", 0),
                )

        except Exception:
            return None

    async def delete_post(
        self,
        post_id: str,
        credentials: PlatformCredentials,
    ) -> bool:
        """Delete a Facebook post."""
        if not credentials.access_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/{post_id}"
                response = await client.delete(
                    url,
                    params={"access_token": credentials.access_token},
                )

                data = response.json()
                return data.get("success", False)

        except Exception:
            return False
