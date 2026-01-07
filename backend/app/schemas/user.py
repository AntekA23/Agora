from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserPreferences, UserRole


class UserUpdate(BaseModel):
    """Update user request."""

    name: str | None = Field(default=None, min_length=2)
    preferences: UserPreferences | None = None


class UserResponse(BaseModel):
    """User data response."""

    id: str
    email: EmailStr
    name: str
    company_id: str | None
    role: UserRole
    preferences: UserPreferences

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    current_password: str
    new_password: str = Field(..., min_length=8)
