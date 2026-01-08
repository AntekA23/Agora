"""LinkedIn publisher using LinkedIn Marketing API."""

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


class LinkedInPublisher(BasePublisher):
    """Publisher for LinkedIn via Marketing API."""

    platform = Platform.LINKEDIN
    BASE_URL = "https://api.linkedin.com/v2"

    async def publish(
        self,
        content: dict[str, Any],
        credentials: PlatformCredentials,
        media_urls: list[str] | None = None,
    ) -> PublishResult:
        """
        Publish content to LinkedIn.

        Supports:
        - Text posts (shares)
        - Article shares with images
        """
        if not credentials.access_token:
            return self._build_error_result("No access token available")

        if not credentials.platform_user_id:
            return self._build_error_result("No LinkedIn user/organization ID available")

        try:
            async with httpx.AsyncClient() as client:
                # Build the share content
                share_content = self._build_share_content(
                    content=content,
                    author_urn=credentials.platform_user_id,
                    media_urls=media_urls,
                )

                # Post to LinkedIn
                url = f"{self.BASE_URL}/ugcPosts"

                response = await client.post(
                    url,
                    json=share_content,
                    headers={
                        "Authorization": f"Bearer {credentials.access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0",
                    },
                )

                if response.status_code not in (200, 201):
                    error_data = response.json() if response.text else {}
                    return self._build_error_result(
                        error_message=error_data.get("message", f"HTTP {response.status_code}"),
                        error_code=str(response.status_code),
                    )

                # LinkedIn returns the post ID in the header
                post_id = response.headers.get("x-restli-id", "")

                if not post_id:
                    # Try to get from response body
                    data = response.json() if response.text else {}
                    post_id = data.get("id", "")

                if not post_id:
                    return self._build_error_result("No post ID in response")

                # Build post URL
                post_url = f"https://www.linkedin.com/feed/update/{post_id}"

                return self._build_success_result(
                    post_id=post_id,
                    post_url=post_url,
                    raw_response={"status_code": response.status_code},
                )

        except httpx.HTTPError as e:
            return self._build_error_result(f"HTTP error: {str(e)}")
        except Exception as e:
            return self._build_error_result(f"Unexpected error: {str(e)}")

    def _build_share_content(
        self,
        content: dict[str, Any],
        author_urn: str,
        media_urls: list[str] | None = None,
    ) -> dict:
        """Build LinkedIn share content structure."""
        text = content.get("text") or content.get("caption") or ""

        # Add hashtags
        if content.get("hashtags"):
            hashtags = content["hashtags"]
            if isinstance(hashtags, list):
                text += "\n\n" + " ".join(hashtags)
            elif isinstance(hashtags, str):
                text += "\n\n" + hashtags

        # Ensure author URN is properly formatted
        if not author_urn.startswith("urn:li:"):
            author_urn = f"urn:li:person:{author_urn}"

        share_content = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # Add media if provided
        if media_urls and len(media_urls) > 0:
            share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            share_content["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "originalUrl": media_urls[0],
                }
            ]

        return share_content

    async def validate_credentials(
        self,
        credentials: PlatformCredentials,
    ) -> bool:
        """Validate LinkedIn credentials."""
        if not credentials.access_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/me"
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {credentials.access_token}"},
                )

                return response.status_code == 200

        except Exception:
            return False

    async def refresh_token(
        self,
        credentials: PlatformCredentials,
    ) -> PlatformCredentials | None:
        """
        Refresh LinkedIn access token.

        LinkedIn access tokens expire after 60 days.
        Refresh tokens can be used to get new access tokens.
        """
        if not credentials.refresh_token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                url = "https://www.linkedin.com/oauth/v2/accessToken"
                response = await client.post(
                    url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": credentials.refresh_token,
                        "client_id": "",  # Would come from settings
                        "client_secret": "",  # Would come from settings
                    },
                )

                data = response.json()

                if "access_token" in data:
                    credentials.access_token = data["access_token"]
                    if "refresh_token" in data:
                        credentials.refresh_token = data["refresh_token"]
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
        """Get engagement statistics for a LinkedIn post."""
        if not credentials.access_token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                # LinkedIn uses a different endpoint for social actions
                url = f"{self.BASE_URL}/socialActions/{post_id}"
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {credentials.access_token}"},
                )

                if response.status_code != 200:
                    return None

                data = response.json()

                return PostStats(
                    likes=data.get("likesSummary", {}).get("totalLikes", 0),
                    comments=data.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
                )

        except Exception:
            return None

    async def delete_post(
        self,
        post_id: str,
        credentials: PlatformCredentials,
    ) -> bool:
        """Delete a LinkedIn post."""
        if not credentials.access_token:
            return False

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.BASE_URL}/ugcPosts/{post_id}"
                response = await client.delete(
                    url,
                    headers={"Authorization": f"Bearer {credentials.access_token}"},
                )

                return response.status_code in (200, 204)

        except Exception:
            return False
