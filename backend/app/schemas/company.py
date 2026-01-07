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
    TargetAudience,
    BrandIdentity,
    CommunicationStyle,
    ContentPreferences,
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


# ============================================================================
# BRAND WIZARD SCHEMAS
# ============================================================================


class WebsiteAnalyzeRequest(BaseModel):
    """Request to analyze company website."""

    url: str = Field(..., min_length=5)


class WebsiteAnalyzeResponse(BaseModel):
    """Response from website analysis."""

    success: bool
    data: dict = Field(default_factory=dict)
    error: str | None = None


class BrandWizardStep1(BaseModel):
    """Step 1: Basic company info."""

    company_description: str = ""
    founded_year: int | None = None
    location: str = ""
    website: str = ""


class BrandWizardStep2(BaseModel):
    """Step 2: Brand identity."""

    mission: str = ""
    vision: str = ""
    values: list[str] = Field(default_factory=list)
    personality_traits: list[str] = Field(default_factory=list)
    unique_value_proposition: str = ""


class BrandWizardStep3(BaseModel):
    """Step 3: Target audience."""

    description: str = ""
    age_from: int | None = None
    age_to: int | None = None
    gender: str = "all"
    locations: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    where_they_are: list[str] = Field(default_factory=list)


class BrandWizardStep4(BaseModel):
    """Step 4: Products and services."""

    products: list[ProductInput] = Field(default_factory=list)
    services: list[ServiceInput] = Field(default_factory=list)
    price_positioning: str = "mid_range"


class BrandWizardStep5(BaseModel):
    """Step 5: Competition."""

    competitors: list[CompetitorInput] = Field(default_factory=list)
    market_position: str = ""
    key_differentiators: list[str] = Field(default_factory=list)


class BrandWizardStep6(BaseModel):
    """Step 6: Communication style."""

    formality_level: int = 3
    emoji_usage: str = "moderate"
    words_to_use: list[str] = Field(default_factory=list)
    words_to_avoid: list[str] = Field(default_factory=list)
    example_phrases: list[str] = Field(default_factory=list)


class BrandWizardStep7(BaseModel):
    """Step 7: Content preferences."""

    themes: list[str] = Field(default_factory=list)
    hashtag_style: str = "mixed"
    branded_hashtags: list[str] = Field(default_factory=list)
    post_frequency: str = ""
    preferred_formats: list[str] = Field(default_factory=list)
    content_goals: list[str] = Field(default_factory=list)


class BrandWizardComplete(BaseModel):
    """Complete brand wizard data - all steps combined."""

    step1: BrandWizardStep1 = Field(default_factory=BrandWizardStep1)
    step2: BrandWizardStep2 = Field(default_factory=BrandWizardStep2)
    step3: BrandWizardStep3 = Field(default_factory=BrandWizardStep3)
    step4: BrandWizardStep4 = Field(default_factory=BrandWizardStep4)
    step5: BrandWizardStep5 = Field(default_factory=BrandWizardStep5)
    step6: BrandWizardStep6 = Field(default_factory=BrandWizardStep6)
    step7: BrandWizardStep7 = Field(default_factory=BrandWizardStep7)
