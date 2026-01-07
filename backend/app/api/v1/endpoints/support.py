"""Customer Support Department API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.support import (
    handle_ticket,
    suggest_response,
    categorize_tickets,
    generate_faq_from_tickets,
    generate_help_article,
    analyze_sentiment,
    analyze_feedback_batch,
    generate_sentiment_report,
)

router = APIRouter(prefix="/support", tags=["support"])


# ============================================================================
# SCHEMAS
# ============================================================================


class HandleTicketRequest(BaseModel):
    """Request for handling a support ticket."""
    ticket_subject: str = Field(..., min_length=3)
    ticket_content: str = Field(..., min_length=10)
    customer_name: str = ""
    customer_history: list[dict] | None = None
    product_context: str = ""
    tone: str = "professional"
    include_next_steps: bool = True


class SuggestResponseRequest(BaseModel):
    """Request for quick response suggestion."""
    ticket_content: str = Field(..., min_length=10)
    response_type: str = "standard"
    tone: str = "professional"
    max_length: int = Field(default=500, ge=100, le=2000)


class TicketData(BaseModel):
    """Single ticket for categorization."""
    id: str
    subject: str
    content: str


class CategorizeTicketsRequest(BaseModel):
    """Request for ticket categorization."""
    tickets: list[TicketData] = Field(..., min_length=1, max_length=50)
    custom_categories: list[str] | None = None


class TicketForFAQ(BaseModel):
    """Ticket data for FAQ generation."""
    subject: str
    content: str
    resolution: str = ""


class GenerateFAQRequest(BaseModel):
    """Request for FAQ generation from tickets."""
    tickets: list[TicketForFAQ] = Field(..., min_length=3, max_length=100)
    product_name: str = ""
    existing_faq: list[dict] | None = None
    max_questions: int = Field(default=10, ge=3, le=30)
    target_audience: str = "general"


class HelpArticleRequest(BaseModel):
    """Request for help article generation."""
    topic: str = Field(..., min_length=5)
    target_audience: str = "general"
    article_type: str = "how_to"
    product_context: str = ""
    include_screenshots_placeholders: bool = True
    include_video_suggestions: bool = False


class SentimentAnalysisRequest(BaseModel):
    """Request for sentiment analysis."""
    text: str = Field(..., min_length=10)
    context: str = ""
    include_emotions: bool = True
    include_intent: bool = True


class FeedbackItem(BaseModel):
    """Single feedback item for batch analysis."""
    id: str
    text: str
    source: str = ""


class BatchSentimentRequest(BaseModel):
    """Request for batch sentiment analysis."""
    feedback_items: list[FeedbackItem] = Field(..., min_length=1, max_length=100)
    group_by: str = "sentiment"


class SentimentReportRequest(BaseModel):
    """Request for sentiment report generation."""
    period: str = Field(..., min_length=3)
    feedback_summary: dict = Field(...)
    comparison_period: dict | None = None


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/ticket/handle")
async def handle_ticket_endpoint(
    data: HandleTicketRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Handle a support ticket and generate response."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": current_user.company_id})
    company_name = company.get("name", "") if company else ""

    result = await handle_ticket(
        ticket_subject=data.ticket_subject,
        ticket_content=data.ticket_content,
        customer_name=data.customer_name,
        customer_history=data.customer_history,
        product_context=data.product_context,
        company_name=company_name,
        tone=data.tone,
        include_next_steps=data.include_next_steps,
    )

    return result


@router.post("/ticket/suggest-response")
async def suggest_response_endpoint(
    data: SuggestResponseRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Get quick response suggestions for a ticket."""
    result = await suggest_response(
        ticket_content=data.ticket_content,
        response_type=data.response_type,
        tone=data.tone,
        max_length=data.max_length,
    )

    return result


@router.post("/tickets/categorize")
async def categorize_tickets_endpoint(
    data: CategorizeTicketsRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Categorize multiple tickets."""
    tickets_data = [t.model_dump() for t in data.tickets]

    result = await categorize_tickets(
        tickets=tickets_data,
        custom_categories=data.custom_categories,
    )

    return result


@router.post("/faq/generate")
async def generate_faq_endpoint(
    data: GenerateFAQRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate FAQ from support tickets."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": current_user.company_id})
    product_name = data.product_name or (company.get("name", "") if company else "")

    tickets_data = [t.model_dump() for t in data.tickets]

    result = await generate_faq_from_tickets(
        tickets=tickets_data,
        product_name=product_name,
        existing_faq=data.existing_faq,
        max_questions=data.max_questions,
        target_audience=data.target_audience,
    )

    return result


@router.post("/help-article")
async def generate_help_article_endpoint(
    data: HelpArticleRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Generate a help article."""
    result = await generate_help_article(
        topic=data.topic,
        target_audience=data.target_audience,
        article_type=data.article_type,
        product_context=data.product_context,
        include_screenshots_placeholders=data.include_screenshots_placeholders,
        include_video_suggestions=data.include_video_suggestions,
    )

    return result


@router.post("/sentiment/analyze")
async def analyze_sentiment_endpoint(
    data: SentimentAnalysisRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Analyze sentiment of a text."""
    result = await analyze_sentiment(
        text=data.text,
        context=data.context,
        include_emotions=data.include_emotions,
        include_intent=data.include_intent,
    )

    return result


@router.post("/sentiment/batch")
async def batch_sentiment_endpoint(
    data: BatchSentimentRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Analyze sentiment of multiple feedback items."""
    feedback_data = [f.model_dump() for f in data.feedback_items]

    result = await analyze_feedback_batch(
        feedback_items=feedback_data,
        group_by=data.group_by,
    )

    return result


@router.post("/sentiment/report")
async def sentiment_report_endpoint(
    data: SentimentReportRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Generate a sentiment report."""
    result = await generate_sentiment_report(
        period=data.period,
        feedback_summary=data.feedback_summary,
        comparison_period=data.comparison_period,
    )

    return result
