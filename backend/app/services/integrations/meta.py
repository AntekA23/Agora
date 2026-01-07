"""Meta (Facebook/Instagram) Graph API Integration.

Umożliwia:
- Publikowanie postów na Instagram/Facebook
- Pobieranie statystyk konta
- Planowanie publikacji
"""

from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings


class MetaAPIError(Exception):
    """Error from Meta Graph API."""
    pass


class MetaService:
    """Service for Meta Graph API integration."""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self):
        self.http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        data: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        """Make authenticated request to Meta Graph API."""
        client = await self._get_client()

        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        params["access_token"] = access_token

        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, params=params, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            raise MetaAPIError(f"Meta API Error: {error_msg}")
        except Exception as e:
            raise MetaAPIError(f"Request failed: {e}")

    # =========================================================================
    # INSTAGRAM BUSINESS ACCOUNT
    # =========================================================================

    async def get_instagram_account(
        self,
        access_token: str,
        page_id: str,
    ) -> dict[str, Any]:
        """Get Instagram Business Account linked to Facebook Page."""
        result = await self._make_request(
            method="GET",
            endpoint=f"{page_id}",
            access_token=access_token,
            params={"fields": "instagram_business_account"},
        )
        return result.get("instagram_business_account", {})

    async def get_instagram_profile(
        self,
        access_token: str,
        ig_user_id: str,
    ) -> dict[str, Any]:
        """Get Instagram profile information."""
        return await self._make_request(
            method="GET",
            endpoint=ig_user_id,
            access_token=access_token,
            params={
                "fields": "id,username,name,biography,followers_count,follows_count,media_count,profile_picture_url"
            },
        )

    async def get_instagram_insights(
        self,
        access_token: str,
        ig_user_id: str,
        metrics: list[str] | None = None,
        period: str = "day",
    ) -> dict[str, Any]:
        """Get Instagram account insights.

        Args:
            access_token: User access token
            ig_user_id: Instagram Business Account ID
            metrics: List of metrics to fetch
            period: Time period (day, week, days_28, lifetime)
        """
        metrics = metrics or [
            "impressions",
            "reach",
            "profile_views",
            "follower_count",
        ]

        return await self._make_request(
            method="GET",
            endpoint=f"{ig_user_id}/insights",
            access_token=access_token,
            params={
                "metric": ",".join(metrics),
                "period": period,
            },
        )

    async def publish_instagram_post(
        self,
        access_token: str,
        ig_user_id: str,
        image_url: str,
        caption: str,
    ) -> dict[str, Any]:
        """Publish a photo post to Instagram.

        Two-step process:
        1. Create media container
        2. Publish the container

        Args:
            access_token: User access token
            ig_user_id: Instagram Business Account ID
            image_url: Public URL of the image
            caption: Post caption with hashtags
        """
        # Step 1: Create media container
        container = await self._make_request(
            method="POST",
            endpoint=f"{ig_user_id}/media",
            access_token=access_token,
            params={
                "image_url": image_url,
                "caption": caption,
            },
        )

        container_id = container.get("id")
        if not container_id:
            raise MetaAPIError("Failed to create media container")

        # Step 2: Publish the container
        result = await self._make_request(
            method="POST",
            endpoint=f"{ig_user_id}/media_publish",
            access_token=access_token,
            params={"creation_id": container_id},
        )

        return {
            "id": result.get("id"),
            "container_id": container_id,
            "status": "published",
        }

    async def publish_instagram_carousel(
        self,
        access_token: str,
        ig_user_id: str,
        image_urls: list[str],
        caption: str,
    ) -> dict[str, Any]:
        """Publish a carousel post to Instagram.

        Args:
            access_token: User access token
            ig_user_id: Instagram Business Account ID
            image_urls: List of public image URLs (2-10)
            caption: Post caption
        """
        if len(image_urls) < 2 or len(image_urls) > 10:
            raise MetaAPIError("Carousel requires 2-10 images")

        # Create containers for each image
        children_ids = []
        for url in image_urls:
            container = await self._make_request(
                method="POST",
                endpoint=f"{ig_user_id}/media",
                access_token=access_token,
                params={
                    "image_url": url,
                    "is_carousel_item": "true",
                },
            )
            children_ids.append(container["id"])

        # Create carousel container
        carousel = await self._make_request(
            method="POST",
            endpoint=f"{ig_user_id}/media",
            access_token=access_token,
            params={
                "media_type": "CAROUSEL",
                "children": ",".join(children_ids),
                "caption": caption,
            },
        )

        # Publish
        result = await self._make_request(
            method="POST",
            endpoint=f"{ig_user_id}/media_publish",
            access_token=access_token,
            params={"creation_id": carousel["id"]},
        )

        return {
            "id": result.get("id"),
            "carousel_id": carousel["id"],
            "children_count": len(children_ids),
            "status": "published",
        }

    # =========================================================================
    # FACEBOOK PAGE
    # =========================================================================

    async def get_facebook_pages(
        self,
        access_token: str,
    ) -> list[dict[str, Any]]:
        """Get Facebook Pages managed by user."""
        result = await self._make_request(
            method="GET",
            endpoint="me/accounts",
            access_token=access_token,
            params={"fields": "id,name,access_token,instagram_business_account"},
        )
        return result.get("data", [])

    async def publish_facebook_post(
        self,
        page_access_token: str,
        page_id: str,
        message: str,
        link: str | None = None,
        photo_url: str | None = None,
    ) -> dict[str, Any]:
        """Publish a post to Facebook Page.

        Args:
            page_access_token: Page access token
            page_id: Facebook Page ID
            message: Post text
            link: Optional URL to share
            photo_url: Optional photo URL
        """
        params = {"message": message}

        if photo_url:
            # Photo post
            endpoint = f"{page_id}/photos"
            params["url"] = photo_url
        elif link:
            # Link post
            endpoint = f"{page_id}/feed"
            params["link"] = link
        else:
            # Text post
            endpoint = f"{page_id}/feed"

        return await self._make_request(
            method="POST",
            endpoint=endpoint,
            access_token=page_access_token,
            params=params,
        )

    async def get_page_insights(
        self,
        page_access_token: str,
        page_id: str,
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get Facebook Page insights."""
        metrics = metrics or [
            "page_impressions",
            "page_engaged_users",
            "page_fan_adds",
            "page_views_total",
        ]

        return await self._make_request(
            method="GET",
            endpoint=f"{page_id}/insights",
            access_token=page_access_token,
            params={
                "metric": ",".join(metrics),
                "period": "day",
            },
        )

    # =========================================================================
    # SCHEDULED POSTS
    # =========================================================================

    async def schedule_instagram_post(
        self,
        access_token: str,
        ig_user_id: str,
        image_url: str,
        caption: str,
        publish_time: datetime,
    ) -> dict[str, Any]:
        """Schedule an Instagram post for future publication.

        Note: Instagram API doesn't support native scheduling.
        This creates a draft that our system will publish at the scheduled time.
        """
        # Create container but don't publish
        container = await self._make_request(
            method="POST",
            endpoint=f"{ig_user_id}/media",
            access_token=access_token,
            params={
                "image_url": image_url,
                "caption": caption,
            },
        )

        return {
            "container_id": container.get("id"),
            "scheduled_time": publish_time.isoformat(),
            "status": "scheduled",
            "platform": "instagram",
        }

    async def schedule_facebook_post(
        self,
        page_access_token: str,
        page_id: str,
        message: str,
        publish_time: datetime,
        photo_url: str | None = None,
    ) -> dict[str, Any]:
        """Schedule a Facebook post for future publication.

        Facebook supports native scheduling via published=false + scheduled_publish_time
        """
        params = {
            "message": message,
            "published": "false",
            "scheduled_publish_time": int(publish_time.timestamp()),
        }

        if photo_url:
            endpoint = f"{page_id}/photos"
            params["url"] = photo_url
        else:
            endpoint = f"{page_id}/feed"

        result = await self._make_request(
            method="POST",
            endpoint=endpoint,
            access_token=page_access_token,
            params=params,
        )

        return {
            "post_id": result.get("id"),
            "scheduled_time": publish_time.isoformat(),
            "status": "scheduled",
            "platform": "facebook",
        }

    # =========================================================================
    # OAUTH
    # =========================================================================

    def get_oauth_url(
        self,
        client_id: str,
        redirect_uri: str,
        state: str,
    ) -> str:
        """Generate OAuth URL for Meta login."""
        scopes = [
            "instagram_basic",
            "instagram_content_publish",
            "instagram_manage_insights",
            "pages_show_list",
            "pages_read_engagement",
            "pages_manage_posts",
        ]

        return (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}&"
            f"scope={','.join(scopes)}"
        )

    async def exchange_code_for_token(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        code: str,
    ) -> dict[str, Any]:
        """Exchange OAuth code for access token."""
        client = await self._get_client()

        response = await client.get(
            f"{self.BASE_URL}/oauth/access_token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_long_lived_token(
        self,
        client_id: str,
        client_secret: str,
        short_lived_token: str,
    ) -> dict[str, Any]:
        """Exchange short-lived token for long-lived token (60 days)."""
        client = await self._get_client()

        response = await client.get(
            f"{self.BASE_URL}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "fb_exchange_token": short_lived_token,
            },
        )
        response.raise_for_status()
        return response.json()


# Singleton instance
meta_service = MetaService()
