from datetime import datetime

from pydantic import BaseModel, Field

from app.models.company import (
    CompanySettings,
    CompanySize,
    SubscriptionPlan,
    CompanyKnowledge,
    Product,
    Service,
    Competitor,
    BrandGuidelines,
)


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


# ============================================================================
# KNOWLEDGE BASE SCHEMAS
# ============================================================================


class KnowledgeResponse(BaseModel):
    """Full knowledge base response."""

    knowledge: CompanyKnowledge


class KnowledgeUpdate(BaseModel):
    """Update knowledge base - partial update supported."""

    company_description: str | None = None
    mission: str | None = None
    vision: str | None = None
    unique_value_proposition: str | None = None
    target_segments: list[str] | None = None
    founded_year: int | None = None
    achievements: list[str] | None = None
    case_studies: list[str] | None = None
    website: str | None = None
    social_media: dict[str, str] | None = None
    custom_facts: list[str] | None = None


class ProductInput(BaseModel):
    """Input for adding/updating a product."""

    name: str = Field(..., min_length=1)
    description: str = ""
    price: float | None = None
    category: str = ""
    features: list[str] = Field(default_factory=list)
    unique_selling_points: list[str] = Field(default_factory=list)


class ServiceInput(BaseModel):
    """Input for adding/updating a service."""

    name: str = Field(..., min_length=1)
    description: str = ""
    price_from: float | None = None
    price_to: float | None = None
    duration: str = ""
    benefits: list[str] = Field(default_factory=list)


class CompetitorInput(BaseModel):
    """Input for adding/updating a competitor."""

    name: str = Field(..., min_length=1)
    website: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    notes: str = ""


class BrandGuidelinesInput(BaseModel):
    """Input for updating brand guidelines."""

    tone_of_voice: str | None = None
    key_messages: list[str] | None = None
    words_to_use: list[str] | None = None
    words_to_avoid: list[str] | None = None
    example_posts: list[str] | None = None
    color_palette: list[str] | None = None
    hashtags_always: list[str] | None = None
