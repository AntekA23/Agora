from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from app.models.base import MongoBaseModel


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class UserPreferences(BaseModel):
    """User preferences."""

    theme: str = "dark"
    language: str = "pl"


class User(MongoBaseModel):
    """User model."""

    email: EmailStr
    password_hash: str
    name: str
    company_id: str | None = None
    role: UserRole = UserRole.MEMBER
    preferences: UserPreferences = Field(default_factory=UserPreferences)
