"""Schemas for company integrations (OAuth connections)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class OAuthTokens(BaseModel):
    """OAuth token storage."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: str | None = None


class MetaIntegration(BaseModel):
    """Meta (Facebook/Instagram) integration settings."""
    connected: bool = False
    page_id: str | None = None
    page_name: str | None = None
    instagram_account_id: str | None = None
    instagram_username: str | None = None
    tokens: OAuthTokens | None = None
    connected_at: datetime | None = None
    connected_by: str | None = None  # user_id who connected


class GoogleIntegration(BaseModel):
    """Google integration settings."""
    connected: bool = False
    email: str | None = None
    calendar_id: str | None = None
    tokens: OAuthTokens | None = None
    connected_at: datetime | None = None
    connected_by: str | None = None


class CompanyIntegrations(BaseModel):
    """All integrations for a company."""
    meta: MetaIntegration = Field(default_factory=MetaIntegration)
    google: GoogleIntegration = Field(default_factory=GoogleIntegration)


# API Request/Response schemas

class MetaConnectRequest(BaseModel):
    """Request to initiate Meta OAuth flow."""
    redirect_uri: str = Field(..., description="Where to redirect after OAuth")


class MetaCallbackRequest(BaseModel):
    """Callback data from Meta OAuth."""
    code: str
    state: str | None = None
    redirect_uri: str


class GoogleConnectRequest(BaseModel):
    """Request to initiate Google OAuth flow."""
    redirect_uri: str


class GoogleCallbackRequest(BaseModel):
    """Callback data from Google OAuth."""
    code: str
    state: str | None = None
    redirect_uri: str


class IntegrationStatus(BaseModel):
    """Status of a single integration."""
    provider: str
    connected: bool
    account_name: str | None = None
    connected_at: datetime | None = None
    expires_at: datetime | None = None


class AllIntegrationsStatus(BaseModel):
    """Status of all integrations for a company."""
    meta: IntegrationStatus
    google: IntegrationStatus


class DisconnectResponse(BaseModel):
    """Response after disconnecting an integration."""
    provider: str
    disconnected: bool
    message: str
