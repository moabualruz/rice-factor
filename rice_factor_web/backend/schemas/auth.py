"""Pydantic schemas for authentication API endpoints.

These schemas define the request and response models for OAuth2 and session management.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """Current user information."""

    id: str = Field(..., description="User identifier")
    username: str = Field(..., description="Username")
    email: str | None = Field(None, description="Email address")
    name: str | None = Field(None, description="Display name")
    avatar_url: str | None = Field(None, description="Avatar URL")
    provider: str = Field(..., description="OAuth provider (github, google)")
    authenticated_at: datetime = Field(..., description="Authentication timestamp")


class AuthStatusResponse(BaseModel):
    """Response for authentication status check."""

    authenticated: bool = Field(..., description="Whether user is authenticated")
    user: UserInfo | None = Field(None, description="User info if authenticated")


class OAuthProviderInfo(BaseModel):
    """Information about an OAuth provider."""

    name: str = Field(..., description="Provider name (github, google)")
    enabled: bool = Field(..., description="Whether provider is configured")
    auth_url: str | None = Field(None, description="OAuth authorization URL")


class OAuthProvidersResponse(BaseModel):
    """Response listing available OAuth providers."""

    providers: list[OAuthProviderInfo] = Field(
        default_factory=list,
        description="Available OAuth providers",
    )


class LogoutResponse(BaseModel):
    """Response after logout."""

    logged_out: bool = Field(True, description="Logout status")
    message: str = Field("Successfully logged out", description="Status message")
