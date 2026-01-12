"""Authentication API routes.

Provides endpoints for OAuth2 authentication and session management.
Authentication is optional by default - enable by configuring OAuth credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from rice_factor_web.backend.config import get_settings
from rice_factor_web.backend.deps import CurrentUser
from rice_factor_web.backend.schemas.auth import (
    AuthStatusResponse,
    LogoutResponse,
    OAuthProviderInfo,
    OAuthProvidersResponse,
    UserInfo,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _is_auth_enabled() -> bool:
    """Check if any OAuth provider is configured."""
    settings = get_settings()
    return bool(settings.github_client_id or settings.google_client_id)


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    user: CurrentUser,
) -> AuthStatusResponse:
    """Get current authentication status.

    Returns authenticated user info if logged in,
    or authenticated=True with anonymous user if auth is disabled.

    Args:
        user: Current user from session (may be None).

    Returns:
        Authentication status and user info.
    """
    if not _is_auth_enabled():
        # Auth disabled - return anonymous user
        return AuthStatusResponse(
            authenticated=True,
            user=UserInfo(
                id="anonymous",
                username="anonymous",
                email=None,
                name="Anonymous User",
                avatar_url=None,
                provider="local",
                authenticated_at=datetime.now(timezone.utc),
            ),
        )

    if user:
        return AuthStatusResponse(
            authenticated=True,
            user=UserInfo(
                id=user.get("id", "unknown"),
                username=user.get("username", "unknown"),
                email=user.get("email"),
                name=user.get("name"),
                avatar_url=user.get("avatar_url"),
                provider=user.get("provider", "unknown"),
                authenticated_at=datetime.fromisoformat(user["authenticated_at"])
                if "authenticated_at" in user
                else datetime.now(timezone.utc),
            ),
        )

    return AuthStatusResponse(authenticated=False, user=None)


@router.get("/providers", response_model=OAuthProvidersResponse)
async def list_providers() -> OAuthProvidersResponse:
    """List available OAuth providers.

    Returns which providers are configured and their auth URLs.

    Returns:
        List of available OAuth providers.
    """
    settings = get_settings()
    providers: list[OAuthProviderInfo] = []

    if settings.github_client_id:
        providers.append(
            OAuthProviderInfo(
                name="github",
                enabled=True,
                auth_url="/api/v1/auth/github/login",
            )
        )
    else:
        providers.append(
            OAuthProviderInfo(
                name="github",
                enabled=False,
                auth_url=None,
            )
        )

    if settings.google_client_id:
        providers.append(
            OAuthProviderInfo(
                name="google",
                enabled=True,
                auth_url="/api/v1/auth/google/login",
            )
        )
    else:
        providers.append(
            OAuthProviderInfo(
                name="google",
                enabled=False,
                auth_url=None,
            )
        )

    return OAuthProvidersResponse(providers=providers)


@router.get("/github/login")
async def github_login(request: Request) -> RedirectResponse:
    """Initiate GitHub OAuth login flow.

    Redirects to GitHub authorization page.

    Args:
        request: The incoming request.

    Returns:
        Redirect to GitHub OAuth.

    Raises:
        HTTPException: 503 if GitHub OAuth not configured.
    """
    settings = get_settings()

    if not settings.github_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth not configured",
        )

    # Build authorization URL
    callback_url = str(request.url_for("github_callback"))
    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={callback_url}"
        f"&scope=user:email"
    )

    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(
    request: Request,
    response: Response,
    code: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Handle GitHub OAuth callback.

    Exchanges authorization code for access token and creates session.

    Args:
        request: The incoming request.
        response: The response to set cookies on.
        code: Authorization code from GitHub.
        error: Error message if authorization failed.

    Returns:
        Redirect to dashboard.

    Raises:
        HTTPException: 400 if error or missing code.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub authorization failed: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code",
        )

    settings = get_settings()

    # Exchange code for access token
    import httpx

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code",
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received",
            )

        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info",
            )

        user_data = user_response.json()

    # Create session
    from rice_factor_web.backend.auth.session import session_manager

    user_info: dict[str, Any] = {
        "id": str(user_data.get("id")),
        "username": user_data.get("login"),
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "avatar_url": user_data.get("avatar_url"),
        "provider": "github",
        "authenticated_at": datetime.now(timezone.utc).isoformat(),
    }

    redirect = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    session_manager.set_session_cookie(redirect, user_info)

    return redirect


@router.get("/google/login")
async def google_login(request: Request) -> RedirectResponse:
    """Initiate Google OAuth login flow.

    Redirects to Google authorization page.

    Args:
        request: The incoming request.

    Returns:
        Redirect to Google OAuth.

    Raises:
        HTTPException: 503 if Google OAuth not configured.
    """
    settings = get_settings()

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured",
        )

    callback_url = str(request.url_for("google_callback"))
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={callback_url}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
    )

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Handle Google OAuth callback.

    Exchanges authorization code for access token and creates session.

    Args:
        request: The incoming request.
        response: The response to set cookies on.
        code: Authorization code from Google.
        error: Error message if authorization failed.

    Returns:
        Redirect to dashboard.

    Raises:
        HTTPException: 400 if error or missing code.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authorization failed: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code",
        )

    settings = get_settings()
    callback_url = str(request.url_for("google_callback"))

    import httpx

    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": callback_url,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code",
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token received",
            )

        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info",
            )

        user_data = user_response.json()

    # Create session
    from rice_factor_web.backend.auth.session import session_manager

    user_info: dict[str, Any] = {
        "id": user_data.get("id"),
        "username": user_data.get("email", "").split("@")[0],
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "avatar_url": user_data.get("picture"),
        "provider": "google",
        "authenticated_at": datetime.now(timezone.utc).isoformat(),
    }

    redirect = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    session_manager.set_session_cookie(redirect, user_info)

    return redirect


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response) -> LogoutResponse:
    """Log out the current user.

    Clears the session cookie.

    Args:
        response: The response to clear cookie on.

    Returns:
        Logout confirmation.
    """
    from rice_factor_web.backend.auth.session import session_manager

    session_manager.clear_session_cookie(response)

    return LogoutResponse(logged_out=True, message="Successfully logged out")
