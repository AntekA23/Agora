from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.base import MongoBaseModel


class CompanySize(str, Enum):
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"


class SubscriptionPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class CompanySettings(BaseModel):
    """Company-specific settings for AI agents."""

    brand_voice: str = "profesjonalny"
    target_audience: str = ""
    language: str = "pl"


class Subscription(BaseModel):
    """Subscription information."""

    plan: SubscriptionPlan = SubscriptionPlan.FREE
    valid_until: datetime | None = None


# ============================================================================
# COMPANY KNOWLEDGE BASE
# ============================================================================


class Product(BaseModel):
    """Product in company catalog."""

    name: str
    description: str = ""
    price: float | None = None
    category: str = ""
    features: list[str] = Field(default_factory=list)
    unique_selling_points: list[str] = Field(default_factory=list)


class Service(BaseModel):
    """Service offered by company."""

    name: str
    description: str = ""
    price_from: float | None = None
    price_to: float | None = None
    duration: str = ""  # np. "1 godzina", "2-3 dni"
    benefits: list[str] = Field(default_factory=list)


class Competitor(BaseModel):
    """Competitor information."""

    name: str
    website: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    notes: str = ""


class BrandGuidelines(BaseModel):
    """Brand guidelines for consistent communication."""

    tone_of_voice: str = ""  # Szczegolowy opis tonu komunikacji
    key_messages: list[str] = Field(default_factory=list)  # Kluczowe przekazy
    words_to_use: list[str] = Field(default_factory=list)  # Preferowane slowa
    words_to_avoid: list[str] = Field(default_factory=list)  # Slowa do unikania
    example_posts: list[str] = Field(default_factory=list)  # Przyklady dobrych postow
    color_palette: list[str] = Field(default_factory=list)  # Kolory marki (hex)
    hashtags_always: list[str] = Field(default_factory=list)  # Hashtagi firmowe


class CompanyKnowledge(BaseModel):
    """Complete knowledge base about the company for AI agents."""

    # Basic info
    company_description: str = ""
    mission: str = ""
    vision: str = ""
    unique_value_proposition: str = ""

    # Products & Services
    products: list[Product] = Field(default_factory=list)
    services: list[Service] = Field(default_factory=list)

    # Market position
    competitors: list[Competitor] = Field(default_factory=list)
    target_segments: list[str] = Field(default_factory=list)  # Segmenty klientow

    # Brand
    brand_guidelines: BrandGuidelines = Field(default_factory=BrandGuidelines)

    # History & achievements
    founded_year: int | None = None
    achievements: list[str] = Field(default_factory=list)
    case_studies: list[str] = Field(default_factory=list)

    # Contact & social
    website: str = ""
    social_media: dict[str, str] = Field(default_factory=dict)  # {"instagram": "@firma", ...}

    # Custom data
    custom_facts: list[str] = Field(default_factory=list)  # Dodatkowe fakty o firmie


class Company(MongoBaseModel):
    """Company model."""

    name: str
    slug: str
    industry: str = ""
    size: CompanySize = CompanySize.SMALL
    settings: CompanySettings = Field(default_factory=CompanySettings)
    enabled_agents: list[str] = Field(default_factory=lambda: ["marketing"])
    subscription: Subscription = Field(default_factory=Subscription)

    # Knowledge base for AI agents
    knowledge: CompanyKnowledge = Field(default_factory=CompanyKnowledge)
