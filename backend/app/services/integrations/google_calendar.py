"""Google Calendar Integration.

Umożliwia:
- Pobieranie wydarzeń z kalendarza
- Tworzenie wydarzeń dla zaplanowanych postów
- Synchronizację z kalendarzem marketingowym
"""

from datetime import datetime, timedelta
from typing import Any

import httpx


class GoogleCalendarError(Exception):
    """Error from Google Calendar API."""
    pass


class GoogleCalendarService:
    """Service for Google Calendar API integration."""

    BASE_URL = "https://www.googleapis.com/calendar/v3"
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]

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
        """Make authenticated request to Google Calendar API."""
        client = await self._get_client()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            if method == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()

            if response.status_code == 204:
                return {}
            return response.json()

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            raise GoogleCalendarError(f"Google Calendar API Error: {error_msg}")
        except Exception as e:
            raise GoogleCalendarError(f"Request failed: {e}")

    # =========================================================================
    # CALENDARS
    # =========================================================================

    async def list_calendars(
        self,
        access_token: str,
    ) -> list[dict[str, Any]]:
        """List user's calendars."""
        result = await self._make_request(
            method="GET",
            endpoint="users/me/calendarList",
            access_token=access_token,
        )
        return result.get("items", [])

    async def get_calendar(
        self,
        access_token: str,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Get calendar details."""
        return await self._make_request(
            method="GET",
            endpoint=f"calendars/{calendar_id}",
            access_token=access_token,
        )

    # =========================================================================
    # EVENTS
    # =========================================================================

    async def list_events(
        self,
        access_token: str,
        calendar_id: str = "primary",
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 50,
        query: str | None = None,
    ) -> list[dict[str, Any]]:
        """List events from calendar.

        Args:
            access_token: OAuth access token
            calendar_id: Calendar ID (default: primary)
            time_min: Start of time range
            time_max: End of time range
            max_results: Maximum events to return
            query: Free text search query
        """
        params = {
            "maxResults": max_results,
            "singleEvents": "true",
            "orderBy": "startTime",
        }

        if time_min:
            params["timeMin"] = time_min.isoformat() + "Z"
        if time_max:
            params["timeMax"] = time_max.isoformat() + "Z"
        if query:
            params["q"] = query

        result = await self._make_request(
            method="GET",
            endpoint=f"calendars/{calendar_id}/events",
            access_token=access_token,
            params=params,
        )
        return result.get("items", [])

    async def get_event(
        self,
        access_token: str,
        event_id: str,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Get a specific event."""
        return await self._make_request(
            method="GET",
            endpoint=f"calendars/{calendar_id}/events/{event_id}",
            access_token=access_token,
        )

    async def create_event(
        self,
        access_token: str,
        summary: str,
        start_time: datetime,
        end_time: datetime | None = None,
        description: str = "",
        calendar_id: str = "primary",
        color_id: str | None = None,
        reminders: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Create a new calendar event.

        Args:
            access_token: OAuth access token
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime (default: start + 1 hour)
            description: Event description
            calendar_id: Calendar ID
            color_id: Google Calendar color ID (1-11)
            reminders: Custom reminders
        """
        if end_time is None:
            end_time = start_time + timedelta(hours=1)

        event_data = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "Europe/Warsaw",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "Europe/Warsaw",
            },
        }

        if color_id:
            event_data["colorId"] = color_id

        if reminders:
            event_data["reminders"] = {
                "useDefault": False,
                "overrides": reminders,
            }
        else:
            event_data["reminders"] = {"useDefault": True}

        return await self._make_request(
            method="POST",
            endpoint=f"calendars/{calendar_id}/events",
            access_token=access_token,
            data=event_data,
        )

    async def update_event(
        self,
        access_token: str,
        event_id: str,
        updates: dict[str, Any],
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Update an existing event."""
        return await self._make_request(
            method="PUT",
            endpoint=f"calendars/{calendar_id}/events/{event_id}",
            access_token=access_token,
            data=updates,
        )

    async def delete_event(
        self,
        access_token: str,
        event_id: str,
        calendar_id: str = "primary",
    ) -> None:
        """Delete an event."""
        await self._make_request(
            method="DELETE",
            endpoint=f"calendars/{calendar_id}/events/{event_id}",
            access_token=access_token,
        )

    # =========================================================================
    # MARKETING CALENDAR HELPERS
    # =========================================================================

    async def create_post_event(
        self,
        access_token: str,
        platform: str,
        post_title: str,
        scheduled_time: datetime,
        post_content: str = "",
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        """Create calendar event for scheduled social media post.

        Args:
            access_token: OAuth access token
            platform: Social media platform (instagram, facebook, etc.)
            post_title: Short title for the post
            scheduled_time: When to publish
            post_content: Full post content for description
            calendar_id: Calendar to use
        """
        # Color codes for different platforms
        platform_colors = {
            "instagram": "6",   # Orange
            "facebook": "9",    # Blue
            "linkedin": "10",   # Green
            "twitter": "7",     # Cyan
        }

        summary = f"📱 {platform.upper()}: {post_title}"
        description = f"""Zaplanowany post na {platform}

TREŚĆ:
{post_content}

---
Utworzono przez Agora AI"""

        return await self.create_event(
            access_token=access_token,
            summary=summary,
            start_time=scheduled_time,
            end_time=scheduled_time + timedelta(minutes=15),
            description=description,
            calendar_id=calendar_id,
            color_id=platform_colors.get(platform.lower(), "1"),
            reminders=[
                {"method": "popup", "minutes": 60},  # 1h before
                {"method": "popup", "minutes": 15},  # 15min before
            ],
        )

    async def create_campaign_events(
        self,
        access_token: str,
        campaign_name: str,
        posts: list[dict[str, Any]],
        calendar_id: str = "primary",
    ) -> list[dict[str, Any]]:
        """Create calendar events for all posts in a campaign.

        Args:
            access_token: OAuth access token
            campaign_name: Name of the campaign
            posts: List of posts with platform, title, scheduled_time, content
            calendar_id: Calendar to use
        """
        created_events = []

        for post in posts:
            try:
                event = await self.create_post_event(
                    access_token=access_token,
                    platform=post.get("platform", "instagram"),
                    post_title=f"{campaign_name} - {post.get('title', 'Post')}",
                    scheduled_time=post["scheduled_time"],
                    post_content=post.get("content", ""),
                    calendar_id=calendar_id,
                )
                created_events.append({
                    "success": True,
                    "event_id": event.get("id"),
                    "platform": post.get("platform"),
                })
            except Exception as e:
                created_events.append({
                    "success": False,
                    "error": str(e),
                    "platform": post.get("platform"),
                })

        return created_events

    async def get_upcoming_marketing_events(
        self,
        access_token: str,
        days_ahead: int = 7,
        calendar_id: str = "primary",
    ) -> list[dict[str, Any]]:
        """Get upcoming marketing events from calendar.

        Searches for events with social media indicators (📱 prefix, platform names).
        """
        time_min = datetime.utcnow()
        time_max = time_min + timedelta(days=days_ahead)

        events = await self.list_events(
            access_token=access_token,
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
        )

        # Filter marketing events
        marketing_events = []
        marketing_indicators = ["📱", "instagram", "facebook", "linkedin", "post", "kampania"]

        for event in events:
            summary = event.get("summary", "").lower()
            if any(ind.lower() in summary for ind in marketing_indicators):
                marketing_events.append(event)

        return marketing_events

    # =========================================================================
    # OAUTH
    # =========================================================================

    def get_oauth_url(
        self,
        client_id: str,
        redirect_uri: str,
        state: str,
    ) -> str:
        """Generate OAuth URL for Google login."""
        scope = " ".join(self.SCOPES)

        return (
            f"{self.AUTH_URL}?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope={scope}&"
            f"state={state}&"
            f"access_type=offline&"
            f"prompt=consent"
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

        response = await client.post(
            self.TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()

    async def refresh_token(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        """Refresh access token using refresh token."""
        client = await self._get_client()

        response = await client.post(
            self.TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        response.raise_for_status()
        return response.json()


# Singleton instance
calendar_service = GoogleCalendarService()
