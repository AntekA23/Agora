"""Sales Department API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, Database
from app.services.agents.sales import (
    generate_sales_proposal,
    score_lead,
    analyze_leads_batch,
    analyze_customer_data,
    suggest_next_actions,
    generate_followup_email,
)

router = APIRouter(prefix="/sales", tags=["sales"])


# ============================================================================
# SCHEMAS
# ============================================================================


class ProductService(BaseModel):
    """Product/service in a proposal."""
    name: str
    description: str = ""
    price: str = ""
    benefits: list[str] = []


class ProposalRequest(BaseModel):
    """Request for generating a sales proposal."""
    client_name: str = Field(..., min_length=2)
    client_industry: str = Field(..., min_length=2)
    client_needs: list[str] = Field(..., min_length=1)
    products_services: list[ProductService] = Field(..., min_length=1)
    proposal_type: str = "standard"
    budget_range: str = ""
    timeline: str = ""
    competitive_advantages: list[str] | None = None
    use_web_search: bool = True


class LeadScoreRequest(BaseModel):
    """Request for scoring a lead."""
    company_name: str = Field(..., min_length=2)
    contact_name: str = ""
    contact_title: str = ""
    company_size: str = ""
    industry: str = ""
    budget: str = ""
    timeline: str = ""
    pain_points: list[str] | None = None
    interaction_history: list[dict] | None = None
    source: str = ""
    use_web_search: bool = True


class LeadData(BaseModel):
    """Single lead data for batch analysis."""
    company_name: str
    contact_name: str = ""
    industry: str = ""
    company_size: str = ""
    budget: str = ""
    timeline: str = ""
    source: str = ""


class LeadsBatchRequest(BaseModel):
    """Request for batch lead analysis."""
    leads: list[LeadData] = Field(..., min_length=1, max_length=50)


class CustomerAnalysisRequest(BaseModel):
    """Request for customer data analysis."""
    customer_name: str = Field(..., min_length=2)
    customer_data: dict = Field(...)
    interaction_history: list[dict] | None = None
    purchases: list[dict] | None = None
    support_tickets: list[dict] | None = None


class NextActionsRequest(BaseModel):
    """Request for next action suggestions."""
    customer_name: str = Field(..., min_length=2)
    last_interaction: dict | None = None
    customer_stage: str = "active"
    days_since_contact: int = 0
    open_opportunities: list[dict] | None = None


class FollowupEmailRequest(BaseModel):
    """Request for follow-up email generation."""
    customer_name: str = Field(..., min_length=2)
    contact_name: str = Field(..., min_length=2)
    context: str = Field(..., min_length=10)
    email_purpose: str = "followup"
    previous_conversation: str = ""
    tone: str = "professional"
    include_cta: bool = True


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/proposal")
async def create_proposal(
    data: ProposalRequest,
    current_user: CurrentUser,
    db: Database,
) -> dict[str, Any]:
    """Generate a sales proposal."""
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a company",
        )

    company = await db.companies.find_one({"_id": current_user.company_id})
    company_name = company.get("name", "") if company else ""
    company_description = company.get("description", "") if company else ""

    # Get company's USPs if available
    knowledge = company.get("knowledge", {}) if company else {}
    advantages = data.competitive_advantages or knowledge.get("unique_selling_points", [])

    result = await generate_sales_proposal(
        client_name=data.client_name,
        client_industry=data.client_industry,
        client_needs=data.client_needs,
        products_services=[p.model_dump() for p in data.products_services],
        company_name=company_name,
        company_description=company_description,
        proposal_type=data.proposal_type,
        budget_range=data.budget_range,
        timeline=data.timeline,
        competitive_advantages=advantages,
        use_web_search=data.use_web_search,
    )

    return result


@router.post("/lead/score")
async def score_single_lead(
    data: LeadScoreRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Score a single sales lead."""
    result = await score_lead(
        company_name=data.company_name,
        contact_name=data.contact_name,
        contact_title=data.contact_title,
        company_size=data.company_size,
        industry=data.industry,
        budget=data.budget,
        timeline=data.timeline,
        pain_points=data.pain_points,
        interaction_history=data.interaction_history,
        source=data.source,
        use_web_search=data.use_web_search,
    )

    return result


@router.post("/leads/analyze")
async def analyze_leads(
    data: LeadsBatchRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Analyze and prioritize multiple leads."""
    leads_data = [lead.model_dump() for lead in data.leads]

    result = await analyze_leads_batch(leads=leads_data)

    return result


@router.post("/customer/analyze")
async def analyze_customer(
    data: CustomerAnalysisRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Analyze customer data and provide insights."""
    result = await analyze_customer_data(
        customer_name=data.customer_name,
        customer_data=data.customer_data,
        interaction_history=data.interaction_history,
        purchases=data.purchases,
        support_tickets=data.support_tickets,
    )

    return result


@router.post("/customer/next-actions")
async def get_next_actions(
    data: NextActionsRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Get suggested next actions for a customer."""
    result = await suggest_next_actions(
        customer_name=data.customer_name,
        last_interaction=data.last_interaction,
        customer_stage=data.customer_stage,
        days_since_contact=data.days_since_contact,
        open_opportunities=data.open_opportunities,
    )

    return result


@router.post("/email/followup")
async def create_followup_email(
    data: FollowupEmailRequest,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Generate a follow-up email."""
    result = await generate_followup_email(
        customer_name=data.customer_name,
        contact_name=data.contact_name,
        context=data.context,
        email_purpose=data.email_purpose,
        previous_conversation=data.previous_conversation,
        tone=data.tone,
        include_cta=data.include_cta,
    )

    return result
