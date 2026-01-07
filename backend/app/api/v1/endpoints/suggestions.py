"""Proactive Suggestions API endpoints."""

from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.suggestions import suggestions_service

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


# ============================================================================
# SCHEMAS
# ============================================================================


class SuggestionSummary(BaseModel):
    """Summary of suggestions."""
    total_suggestions: int
    high_priority: int
    upcoming_events: int


class ContentIdea(BaseModel):
    """Content idea suggestion."""
    suggestion_type: str
    title: str
    event_name: str | None = None
    event_date: str | None = None
    days_until: int | None = None
    marketing_tip: str | None = None
    priority: str
    suggested_actions: list[str] = Field(default_factory=list)
    industry_angle: str | None = None


class CalendarEvent(BaseModel):
    """Upcoming calendar event."""
    date: str
    date_full: str
    name: str
    type: str
    marketing_tip: str
    days_until: int
    suggestion_type: str


class TrendSuggestion(BaseModel):
    """Trend-based suggestion."""
    suggestion_type: str
    title: str
    content: str
    action: str
    priority: str


class SuggestionsResponse(BaseModel):
    """Full suggestions response."""
    generated_at: str
    company_id: str
    summary: SuggestionSummary
    urgent: list[ContentIdea]
    upcoming: list[ContentIdea]
    planned: list[ContentIdea]
    trends: list[TrendSuggestion]
    calendar_events: list[CalendarEvent]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("", response_model=SuggestionsResponse)
async def get_suggestions(
    current_user: CurrentUser,
    db: Database,
    days_ahead: int = Query(14, ge=1, le=60, description="Dni do przodu dla wydarzeń"),
    include_trends: bool = Query(True, description="Czy uwzględniać trendy branżowe"),
) -> SuggestionsResponse:
    """Get proactive suggestions for the current user's company.

    Returns personalized suggestions based on:
    - Upcoming calendar events (holidays, commercial dates)
    - Industry trends (if enabled)
    - Company brand voice and industry
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get company data
    company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Get company settings
    settings = company.get("settings", {})
    industry = company.get("industry", "")
    brand_voice = settings.get("brand_voice", "profesjonalny")

    # Generate suggestions
    result = await suggestions_service.get_all_suggestions(
        company_id=current_user.company_id,
        industry=industry if include_trends else "",
        brand_voice=brand_voice,
        days_ahead=days_ahead,
    )

    return SuggestionsResponse(**result)


@router.get("/calendar")
async def get_calendar_events(
    current_user: CurrentUser,
    days_ahead: int = Query(30, ge=1, le=90, description="Dni do przodu"),
) -> list[CalendarEvent]:
    """Get upcoming calendar events for marketing planning."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    events = suggestions_service.get_upcoming_events(days_ahead)
    return [CalendarEvent(**event) for event in events]


@router.get("/trends")
async def get_trend_suggestions(
    current_user: CurrentUser,
    db: Database,
    industry: str | None = Query(None, description="Branża (domyślnie z profilu firmy)"),
) -> list[TrendSuggestion]:
    """Get trend-based content suggestions.

    Uses Tavily to find current trends in your industry.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Get industry from company if not provided
    if not industry:
        company = await db.companies.find_one({"_id": ObjectId(current_user.company_id)})
        if company:
            industry = company.get("industry", "")

    if not industry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Industry not specified. Set it in company profile or provide as parameter.",
        )

    suggestions = await suggestions_service.get_trend_suggestions(industry)
    return [TrendSuggestion(**s) for s in suggestions]


@router.post("/dismiss/{suggestion_id}")
async def dismiss_suggestion(
    suggestion_id: str,
    current_user: CurrentUser,
    db: Database,
) -> dict:
    """Dismiss a suggestion (won't show again).

    Stores dismissed suggestion IDs so they won't be shown again.
    """
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    # Store dismissed suggestion
    await db.dismissed_suggestions.update_one(
        {
            "company_id": current_user.company_id,
            "suggestion_id": suggestion_id,
        },
        {
            "$set": {
                "dismissed_at": datetime.utcnow(),
                "dismissed_by": current_user.id,
            }
        },
        upsert=True,
    )

    return {"status": "dismissed", "suggestion_id": suggestion_id}
