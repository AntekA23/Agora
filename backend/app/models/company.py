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
    wizard_completed: bool = False  # Whether brand wizard was completed
    wizard_reminder_dismissed_at: datetime | None = None  # When user dismissed reminder
    wizard_reminder_snooze_until: datetime | None = None  # Snooze reminder until this date


class TargetAudience(BaseModel):
    """Detailed target audience information."""

    description: str = ""  # Ogolny opis
    age_from: int | None = None
    age_to: int | None = None
    gender: str = "all"  # all, female, male
    locations: list[str] = Field(default_factory=list)  # np. ["Warszawa", "Krakow"]
    interests: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)  # Problemy/bolaczki
    goals: list[str] = Field(default_factory=list)  # Cele klientow
    where_they_are: list[str] = Field(default_factory=list)  # Gdzie sie znajduja (Instagram, LinkedIn, etc.)


class BrandIdentity(BaseModel):
    """Brand identity and personality."""

    mission: str = ""
    vision: str = ""
    values: list[str] = Field(default_factory=list)  # np. ["jakosc", "innowacyjnosc"]
    personality_traits: list[str] = Field(default_factory=list)  # np. ["profesjonalna", "przyjazna"]
    unique_value_proposition: str = ""


class CommunicationStyle(BaseModel):
    """Communication preferences."""

    formality_level: int = 3  # 1-5: 1=bardzo formalny, 5=bardzo swobodny
    emoji_usage: str = "moderate"  # none, minimal, moderate, frequent
    words_to_use: list[str] = Field(default_factory=list)
    words_to_avoid: list[str] = Field(default_factory=list)
    example_phrases: list[str] = Field(default_factory=list)  # Przyklady dobrego stylu
    languages: list[str] = Field(default_factory=lambda: ["pl"])


class ContentPreferences(BaseModel):
    """Content creation preferences."""

    themes: list[str] = Field(default_factory=list)  # Filary tresci
    hashtag_style: str = "mixed"  # branded, trending, mixed, minimal
    branded_hashtags: list[str] = Field(default_factory=list)
    post_frequency: str = ""  # np. "3-4 razy w tygodniu"
    preferred_formats: list[str] = Field(default_factory=list)  # np. ["karuzela", "reels", "stories"]
    content_goals: list[str] = Field(default_factory=list)  # np. ["budowanie swiadomosci", "sprzedaz"]


class PricePositioning(str, Enum):
    BUDGET = "budget"
    MID_RANGE = "mid_range"
    PREMIUM = "premium"
    LUXURY = "luxury"


class InvoiceSettings(BaseModel):
    """Company invoice/billing settings."""

    # Dane sprzedawcy (wymagane do faktur)
    seller_name: str = ""  # Nazwa firmy do faktury
    seller_address: str = ""  # Adres siedziby
    seller_nip: str = ""  # NIP
    seller_email: str = ""  # Email kontaktowy
    seller_phone: str = ""  # Telefon

    # Dane bankowe
    bank_name: str = ""
    bank_account: str = ""  # Numer konta IBAN

    # Ustawienia faktur
    invoice_prefix: str = "FV"  # Prefix numeracji (np. FV, FA)
    invoice_numbering: str = "yearly"  # yearly (FV/1/2024) lub monthly (FV/1/01/2024)
    default_vat_rate: int = 23  # Domyslna stawka VAT
    default_payment_days: int = 14  # Domyslny termin platnosci

    # Ostatni numer faktury w danym okresie
    last_invoice_number: int = 0
    last_invoice_year: int = 0
    last_invoice_month: int = 0

    # Dodatkowe
    invoice_notes: str = ""  # Domyslne uwagi na fakturze
    invoice_footer: str = ""  # Stopka faktury


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
    founded_year: int | None = None
    location: str = ""
    website: str = ""
    social_media: dict[str, str] = Field(default_factory=dict)  # {"instagram": "@firma", ...}

    # Brand Identity (new structured)
    brand_identity: BrandIdentity = Field(default_factory=BrandIdentity)

    # Legacy fields (kept for compatibility)
    mission: str = ""
    vision: str = ""
    unique_value_proposition: str = ""

    # Target Audience (new structured)
    target_audience: TargetAudience = Field(default_factory=TargetAudience)
    target_segments: list[str] = Field(default_factory=list)  # Segmenty klientow (legacy)

    # Products & Services
    products: list[Product] = Field(default_factory=list)
    services: list[Service] = Field(default_factory=list)
    price_positioning: str = "mid_range"  # budget, mid_range, premium, luxury

    # Market position
    competitors: list[Competitor] = Field(default_factory=list)
    market_position: str = ""  # Opis pozycji na rynku

    # Communication (new structured)
    communication_style: CommunicationStyle = Field(default_factory=CommunicationStyle)

    # Content preferences (new)
    content_preferences: ContentPreferences = Field(default_factory=ContentPreferences)

    # Brand guidelines (legacy - kept for compatibility)
    brand_guidelines: BrandGuidelines = Field(default_factory=BrandGuidelines)

    # History & achievements
    achievements: list[str] = Field(default_factory=list)
    case_studies: list[str] = Field(default_factory=list)

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

    # Invoice settings
    invoice_settings: InvoiceSettings = Field(default_factory=InvoiceSettings)
