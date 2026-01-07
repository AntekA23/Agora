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


class Company(MongoBaseModel):
    """Company model."""

    name: str
    slug: str
    industry: str = ""
    size: CompanySize = CompanySize.SMALL
    settings: CompanySettings = Field(default_factory=CompanySettings)
    enabled_agents: list[str] = Field(default_factory=lambda: ["marketing"])
    subscription: Subscription = Field(default_factory=Subscription)
