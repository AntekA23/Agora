"""External Integrations API endpoints."""

from datetime import datetime
from typing import Any
from urllib.parse import urlencode
import secrets

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.core.config import settings
from app.services.integrations.meta import meta_service, MetaAPIError
from app.services.integrations.google_calendar import calendar_service, GoogleCalendarError

router = APIRouter(prefix="/integrations", tags=["integrations"])


# ============================================================================
# SCHEMAS
# ============================================================================


class IntegrationStatus(BaseModel):
    """Status of an integration."""
    connected: bool
    platform: str
    account_name: str | None = None
    expires_at: str | None = None


class PublishPostRequest(BaseModel):
    """Request to publish a post."""
    platform: str = Field(..., description="Platform: instagram or facebook")
    content: str = Field(..., min_length=1, description="Post content/caption")
    image_url: str = Field(..., description="Public URL of the image")


class PublishPostResponse(BaseModel):
    """Response after publishing."""
    success: bool
    post_id: str | None = None
    platform: str
    error: str | None = None


class SchedulePostRequest(BaseModel):
    """Request to schedule a post."""
    platform: str
    content: str
    image_url: str
    scheduled_time: datetime


class CalendarEventRequest(BaseModel):
    """Request to create calendar event."""
    summary: str = Field(..., min_length=1)
    start_time: datetime
    end_time: datetime | None = None
    description: str = ""


# ============================================================================
# META (INSTAGRAM/FACEBOOK) ENDPOINTS
# ============================================================================


@router.get("/meta/status", response_model=IntegrationStatus)
async def get_meta_status(
    current_user: CurrentUser,
    db: Database,
) -> IntegrationStatus:
    """Check Meta integration status for company."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    integration = await db.integrations.find_one({
        "company_id": current_user.company_id,
        "platform": "meta",
    })

    if not integration or not integration.get("access_token"):
        return IntegrationStatus(connected=False, platform="meta")

    return IntegrationStatus(
        connected=True,
        platform="meta",
        account_name=integration.get("account_name"),
        expires_at=integration.get("expires_at"),
    )


@router.get("/meta/connect")
async def connect_meta(
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Get Meta OAuth URL to connect Instagram/Facebook."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    if not settings.META_APP_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Meta integration not configured",
        )

    # Generate state token for security
    state = secrets.token_urlsafe(32)

    # Store state in DB for verification
    await db.oauth_states.insert_one({
        "state": state,
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "platform": "meta",
        "created_at": datetime.utcnow(),
    })

    redirect_uri = f"{settings.APP_URL}{settings.API_V1_PREFIX}/integrations/meta/callback"

    oauth_url = meta_service.get_oauth_url(
        client_id=settings.META_APP_ID,
        redirect_uri=redirect_uri,
        state=state,
    )

    return {"oauth_url": oauth_url}


@router.get("/meta/callback")
async def meta_callback(
    code: str,
    state: str,
    db: Database,
) -> RedirectResponse:
    """Handle Meta OAuth callback."""
    # Verify state
    oauth_state = await db.oauth_states.find_one_and_delete({"state": state, "platform": "meta"})
    if not oauth_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")

    if not settings.META_APP_ID or not settings.META_APP_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Meta not configured")

    redirect_uri = f"{settings.APP_URL}{settings.API_V1_PREFIX}/integrations/meta/callback"

    try:
        # Exchange code for token
        token_data = await meta_service.exchange_code_for_token(
            client_id=settings.META_APP_ID,
            client_secret=settings.META_APP_SECRET,
            redirect_uri=redirect_uri,
            code=code,
        )

        # Get long-lived token
        long_lived = await meta_service.get_long_lived_token(
            client_id=settings.META_APP_ID,
            client_secret=settings.META_APP_SECRET,
            short_lived_token=token_data["access_token"],
        )

        # Get user's pages
        pages = await meta_service.get_facebook_pages(long_lived["access_token"])

        # Find page with Instagram Business Account
        ig_account = None
        page_data = None
        for page in pages:
            if page.get("instagram_business_account"):
                ig_account = page["instagram_business_account"]
                page_data = page
                break

        # Store integration
        await db.integrations.update_one(
            {"company_id": oauth_state["company_id"], "platform": "meta"},
            {
                "$set": {
                    "access_token": long_lived["access_token"],
                    "expires_in": long_lived.get("expires_in"),
                    "expires_at": datetime.utcnow().isoformat(),
                    "page_id": page_data["id"] if page_data else None,
                    "page_access_token": page_data.get("access_token") if page_data else None,
                    "ig_user_id": ig_account.get("id") if ig_account else None,
                    "account_name": page_data.get("name") if page_data else None,
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

        # Redirect to frontend success page
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/integrations?status=success&platform=meta")

    except Exception as e:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/integrations?status=error&message={str(e)}")


@router.post("/meta/publish", response_model=PublishPostResponse)
async def publish_to_meta(
    data: PublishPostRequest,
    current_user: CurrentUser,
    db: Database,
) -> PublishPostResponse:
    """Publish a post to Instagram or Facebook."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    # Get integration
    integration = await db.integrations.find_one({
        "company_id": current_user.company_id,
        "platform": "meta",
    })

    if not integration or not integration.get("access_token"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meta not connected. Please connect your account first.",
        )

    try:
        if data.platform == "instagram":
            if not integration.get("ig_user_id"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No Instagram Business Account connected",
                )

            result = await meta_service.publish_instagram_post(
                access_token=integration["access_token"],
                ig_user_id=integration["ig_user_id"],
                image_url=data.image_url,
                caption=data.content,
            )

        elif data.platform == "facebook":
            if not integration.get("page_id"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No Facebook Page connected",
                )

            result = await meta_service.publish_facebook_post(
                page_access_token=integration["page_access_token"],
                page_id=integration["page_id"],
                message=data.content,
                photo_url=data.image_url,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Platform must be 'instagram' or 'facebook'",
            )

        # Log publication
        await db.publications.insert_one({
            "company_id": current_user.company_id,
            "user_id": current_user.id,
            "platform": data.platform,
            "post_id": result.get("id"),
            "content": data.content,
            "image_url": data.image_url,
            "published_at": datetime.utcnow(),
        })

        return PublishPostResponse(
            success=True,
            post_id=result.get("id"),
            platform=data.platform,
        )

    except MetaAPIError as e:
        return PublishPostResponse(
            success=False,
            platform=data.platform,
            error=str(e),
        )


@router.get("/meta/insights")
async def get_meta_insights(
    current_user: CurrentUser,
    db: Database,
    platform: str = Query("instagram", description="instagram or facebook"),
) -> dict[str, Any]:
    """Get insights from Instagram or Facebook."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    integration = await db.integrations.find_one({
        "company_id": current_user.company_id,
        "platform": "meta",
    })

    if not integration or not integration.get("access_token"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meta not connected")

    try:
        if platform == "instagram" and integration.get("ig_user_id"):
            profile = await meta_service.get_instagram_profile(
                access_token=integration["access_token"],
                ig_user_id=integration["ig_user_id"],
            )
            insights = await meta_service.get_instagram_insights(
                access_token=integration["access_token"],
                ig_user_id=integration["ig_user_id"],
            )
            return {"profile": profile, "insights": insights}

        elif platform == "facebook" and integration.get("page_id"):
            insights = await meta_service.get_page_insights(
                page_access_token=integration["page_access_token"],
                page_id=integration["page_id"],
            )
            return {"insights": insights}

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No {platform} account connected")

    except MetaAPIError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# GOOGLE CALENDAR ENDPOINTS
# ============================================================================


@router.get("/google/status", response_model=IntegrationStatus)
async def get_google_status(
    current_user: CurrentUser,
    db: Database,
) -> IntegrationStatus:
    """Check Google Calendar integration status."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    integration = await db.integrations.find_one({
        "company_id": current_user.company_id,
        "platform": "google",
    })

    if not integration or not integration.get("access_token"):
        return IntegrationStatus(connected=False, platform="google")

    return IntegrationStatus(
        connected=True,
        platform="google",
        account_name=integration.get("email"),
    )


@router.get("/google/connect")
async def connect_google(
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Get Google OAuth URL to connect Calendar."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google integration not configured",
        )

    state = secrets.token_urlsafe(32)

    await db.oauth_states.insert_one({
        "state": state,
        "company_id": current_user.company_id,
        "user_id": current_user.id,
        "platform": "google",
        "created_at": datetime.utcnow(),
    })

    redirect_uri = f"{settings.APP_URL}{settings.API_V1_PREFIX}/integrations/google/callback"

    oauth_url = calendar_service.get_oauth_url(
        client_id=settings.GOOGLE_CLIENT_ID,
        redirect_uri=redirect_uri,
        state=state,
    )

    return {"oauth_url": oauth_url}


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: Database,
) -> RedirectResponse:
    """Handle Google OAuth callback."""
    oauth_state = await db.oauth_states.find_one_and_delete({"state": state, "platform": "google"})
    if not oauth_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google not configured")

    redirect_uri = f"{settings.APP_URL}{settings.API_V1_PREFIX}/integrations/google/callback"

    try:
        token_data = await calendar_service.exchange_code_for_token(
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            redirect_uri=redirect_uri,
            code=code,
        )

        await db.integrations.update_one(
            {"company_id": oauth_state["company_id"], "platform": "google"},
            {
                "$set": {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in"),
                    "updated_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/integrations?status=success&platform=google")

    except Exception as e:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard/integrations?status=error&message={str(e)}")


@router.get("/google/events")
async def get_calendar_events(
    current_user: CurrentUser,
    db: Database,
    days_ahead: int = Query(7, ge=1, le=30),
) -> list[dict[str, Any]]:
    """Get upcoming calendar events."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    integration = await db.integrations.find_one({
        "company_id": current_user.company_id,
        "platform": "google",
    })

    if not integration or not integration.get("access_token"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google Calendar not connected")

    try:
        events = await calendar_service.get_upcoming_marketing_events(
            access_token=integration["access_token"],
            days_ahead=days_ahead,
        )
        return events

    except GoogleCalendarError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/google/events")
async def create_calendar_event(
    data: CalendarEventRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Create a calendar event."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    integration = await db.integrations.find_one({
        "company_id": current_user.company_id,
        "platform": "google",
    })

    if not integration or not integration.get("access_token"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google Calendar not connected")

    try:
        event = await calendar_service.create_event(
            access_token=integration["access_token"],
            summary=data.summary,
            start_time=data.start_time,
            end_time=data.end_time,
            description=data.description,
        )
        return event

    except GoogleCalendarError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# ALL INTEGRATIONS
# ============================================================================


@router.get("", response_model=list[IntegrationStatus])
async def list_integrations(
    current_user: CurrentUser,
    db: Database,
) -> list[IntegrationStatus]:
    """List all integration statuses for company."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    statuses = []

    # Check Meta
    meta = await db.integrations.find_one({
        "company_id": current_user.company_id,
        "platform": "meta",
    })
    statuses.append(IntegrationStatus(
        connected=bool(meta and meta.get("access_token")),
        platform="meta",
        account_name=meta.get("account_name") if meta else None,
    ))

    # Check Google
    google = await db.integrations.find_one({
        "company_id": current_user.company_id,
        "platform": "google",
    })
    statuses.append(IntegrationStatus(
        connected=bool(google and google.get("access_token")),
        platform="google",
        account_name=google.get("email") if google else None,
    ))

    return statuses


@router.delete("/{platform}")
async def disconnect_integration(
    platform: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Disconnect an integration."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to a company")

    if platform not in ["meta", "google"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid platform")

    result = await db.integrations.delete_one({
        "company_id": current_user.company_id,
        "platform": platform,
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    return {"status": "disconnected", "platform": platform}
