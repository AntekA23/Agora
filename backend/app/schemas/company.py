from datetime import datetime

from pydantic import BaseModel, Field

from app.models.company import CompanySettings, CompanySize, SubscriptionPlan


class CompanyCreate(BaseModel):
    """Create company request."""

    name: str = Field(..., min_length=2)
    industry: str = ""
    size: CompanySize = CompanySize.SMALL


class CompanyUpdate(BaseModel):
    """Update company request."""

    name: str | None = None
    industry: str | None = None
    size: CompanySize | None = None
    settings: CompanySettings | None = None
    enabled_agents: list[str] | None = None


class CompanyResponse(BaseModel):
    """Company data response."""

    id: str
    name: str
    slug: str
    industry: str
    size: CompanySize
    settings: CompanySettings
    enabled_agents: list[str]
    subscription_plan: SubscriptionPlan
    subscription_valid_until: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
