"""Session management for secure cookie-based authentication.

Provides secure session handling using signed cookies with itsdangerous.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rice_factor_web.backend.config import get_settings

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response


class SessionManager:
    """Manage secure session cookies.

    Uses itsdangerous URLSafeTimedSerializer for signed cookies that
    are tamper-proof and optionally time-limited.
    """

    def __init__(self) -> None:
        """Initialize session manager with settings."""
        self._serializer: Any = None

    def _get_serializer(self) -> Any:
        """Get or create the serializer (lazy initialization)."""
        if self._serializer is None:
            from itsdangerous import URLSafeTimedSerializer

            settings = get_settings()
            self._serializer = URLSafeTimedSerializer(settings.secret_key)
        return self._serializer

    def create_session(self, user_data: dict[str, Any]) -> str:
        """Create a signed session token.

        Args:
            user_data: User information to store in session.

        Returns:
            Signed session token string.
        """
        return self._get_serializer().dumps(user_data)

    def load_session(self, token: str) -> dict[str, Any] | None:
        """Load and verify session data from token.

        Args:
            token: Signed session token.

        Returns:
            User data dictionary or None if invalid/expired.
        """
        settings = get_settings()
        try:
            return self._get_serializer().loads(token, max_age=settings.session_max_age)
        except Exception:
            return None

    def set_session_cookie(
        self,
        response: "Response",
        user_data: dict[str, Any],
    ) -> None:
        """Set session cookie on response.

        Args:
            response: The response to set cookie on.
            user_data: User information to store in session.
        """
        settings = get_settings()
        token = self.create_session(user_data)
        response.set_cookie(
            key=settings.session_cookie_name,
            value=token,
            max_age=settings.session_max_age,
            httponly=True,
            secure=not settings.debug,  # Secure in production
            samesite="lax",
        )

    def clear_session_cookie(self, response: "Response") -> None:
        """Clear the session cookie.

        Args:
            response: The response to clear cookie on.
        """
        settings = get_settings()
        response.delete_cookie(
            key=settings.session_cookie_name,
            httponly=True,
            secure=not settings.debug,
            samesite="lax",
        )

    def get_current_user(self, request: "Request") -> dict[str, Any] | None:
        """Get current user from session cookie.

        Args:
            request: The incoming request.

        Returns:
            User data dictionary or None if not authenticated.
        """
        settings = get_settings()
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return self.load_session(token)


# Global session manager instance
session_manager = SessionManager()
