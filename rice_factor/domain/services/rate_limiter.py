"""Rate limiting for LLM providers.

This module provides the RateLimiter service that enforces rate limits
for LLM provider requests using a token bucket algorithm. Supports
configurable limits per provider with graceful degradation.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RateLimitStrategy(Enum):
    """Strategy for handling rate limit violations."""

    BLOCK = "block"  # Block until tokens available
    REJECT = "reject"  # Immediately reject request
    DEGRADE = "degrade"  # Allow with degraded service flag


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded and strategy is REJECT."""

    def __init__(
        self,
        provider: str,
        limit_type: str,
        current: float,
        limit: float,
        retry_after: float,
    ) -> None:
        """Initialize the exception.

        Args:
            provider: Provider that exceeded the limit.
            limit_type: Type of limit exceeded (requests_per_minute, tokens_per_day).
            current: Current usage value.
            limit: Configured limit value.
            retry_after: Seconds until tokens will be available.
        """
        self.provider = provider
        self.limit_type = limit_type
        self.current = current
        self.limit = limit
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for {provider}: {limit_type} "
            f"({current:.1f}/{limit:.1f}). Retry after {retry_after:.1f}s"
        )


@dataclass
class TokenBucket:
    """Token bucket for rate limiting.

    Uses the token bucket algorithm to control request rates.
    Tokens are added at a fixed rate up to a maximum capacity.

    Attributes:
        capacity: Maximum tokens the bucket can hold.
        tokens: Current token count.
        refill_rate: Tokens added per second.
        last_refill: Timestamp of last token refill.
    """

    capacity: float
    tokens: float = field(default=0.0)
    refill_rate: float = 1.0  # tokens per second
    last_refill: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        """Initialize bucket with full capacity."""
        if self.tokens == 0.0:
            self.tokens = self.capacity

    def refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def consume(self, amount: float = 1.0) -> bool:
        """Attempt to consume tokens.

        Args:
            amount: Number of tokens to consume.

        Returns:
            True if tokens were consumed, False if insufficient tokens.
        """
        self.refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def wait_time(self, amount: float = 1.0) -> float:
        """Calculate time to wait for tokens.

        Args:
            amount: Number of tokens needed.

        Returns:
            Seconds to wait, 0 if tokens available now.
        """
        self.refill()
        if self.tokens >= amount:
            return 0.0
        needed = amount - self.tokens
        return needed / self.refill_rate

    def available(self) -> float:
        """Get current available tokens.

        Returns:
            Current token count after refill.
        """
        self.refill()
        return self.tokens


@dataclass
class ProviderLimits:
    """Rate limit configuration for a provider.

    Attributes:
        provider: Provider name.
        requests_per_minute: Maximum requests per minute.
        tokens_per_minute: Maximum tokens per minute.
        tokens_per_day: Maximum tokens per day.
        concurrent_requests: Maximum concurrent requests.
        enabled: Whether rate limiting is enabled.
    """

    provider: str
    requests_per_minute: float = 60.0
    tokens_per_minute: float = 100000.0
    tokens_per_day: float = 10000000.0
    concurrent_requests: int = 10
    enabled: bool = True


@dataclass
class RateLimitResult:
    """Result of a rate limit check.

    Attributes:
        allowed: Whether the request is allowed.
        degraded: Whether service is degraded.
        wait_time: Seconds to wait if blocked.
        limit_type: Type of limit that was checked/exceeded.
        remaining: Remaining capacity for the checked limit.
    """

    allowed: bool
    degraded: bool = False
    wait_time: float = 0.0
    limit_type: str = ""
    remaining: float = 0.0


class RateLimiter:
    """Rate limiter service for LLM providers.

    Enforces configurable rate limits using token bucket algorithm.
    Supports per-provider limits for requests and tokens.

    Example:
        >>> limiter = RateLimiter()
        >>> limiter.configure("claude", requests_per_minute=30)
        >>> result = limiter.check("claude")
        >>> if result.allowed:
        ...     limiter.acquire("claude")
        ...     # make request
        ...     limiter.release("claude", tokens_used=100)
    """

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        self._limits: dict[str, ProviderLimits] = {}
        self._request_buckets: dict[str, TokenBucket] = {}
        self._token_buckets: dict[str, TokenBucket] = {}
        self._daily_tokens: dict[str, float] = {}
        self._daily_reset: dict[str, float] = {}
        self._concurrent: dict[str, int] = {}
        self._lock = threading.RLock()
        self._strategy = RateLimitStrategy.BLOCK

    def set_strategy(self, strategy: RateLimitStrategy) -> None:
        """Set the rate limit handling strategy.

        Args:
            strategy: Strategy for handling limit violations.
        """
        self._strategy = strategy

    def configure(
        self,
        provider: str,
        requests_per_minute: float | None = None,
        tokens_per_minute: float | None = None,
        tokens_per_day: float | None = None,
        concurrent_requests: int | None = None,
        enabled: bool = True,
    ) -> ProviderLimits:
        """Configure rate limits for a provider.

        Args:
            provider: Provider name.
            requests_per_minute: Max requests per minute.
            tokens_per_minute: Max tokens per minute.
            tokens_per_day: Max tokens per day.
            concurrent_requests: Max concurrent requests.
            enabled: Whether limiting is enabled.

        Returns:
            The configured ProviderLimits.
        """
        with self._lock:
            existing = self._limits.get(provider)

            limits = ProviderLimits(
                provider=provider,
                requests_per_minute=(
                    requests_per_minute
                    if requests_per_minute is not None
                    else (existing.requests_per_minute if existing else 60.0)
                ),
                tokens_per_minute=(
                    tokens_per_minute
                    if tokens_per_minute is not None
                    else (existing.tokens_per_minute if existing else 100000.0)
                ),
                tokens_per_day=(
                    tokens_per_day
                    if tokens_per_day is not None
                    else (existing.tokens_per_day if existing else 10000000.0)
                ),
                concurrent_requests=(
                    concurrent_requests
                    if concurrent_requests is not None
                    else (existing.concurrent_requests if existing else 10)
                ),
                enabled=enabled,
            )

            self._limits[provider] = limits

            # Create/update request bucket
            self._request_buckets[provider] = TokenBucket(
                capacity=limits.requests_per_minute,
                refill_rate=limits.requests_per_minute / 60.0,
            )

            # Create/update token bucket
            self._token_buckets[provider] = TokenBucket(
                capacity=limits.tokens_per_minute,
                refill_rate=limits.tokens_per_minute / 60.0,
            )

            # Initialize daily tracking
            if provider not in self._daily_tokens:
                self._daily_tokens[provider] = 0.0
                self._daily_reset[provider] = time.monotonic() + 86400.0

            # Initialize concurrent tracking
            if provider not in self._concurrent:
                self._concurrent[provider] = 0

            return limits

    def get_limits(self, provider: str) -> ProviderLimits | None:
        """Get configured limits for a provider.

        Args:
            provider: Provider name.

        Returns:
            ProviderLimits if configured, None otherwise.
        """
        return self._limits.get(provider)

    def check(
        self,
        provider: str,
        tokens: int = 0,
    ) -> RateLimitResult:
        """Check if a request would be allowed.

        Does not consume any tokens or modify state.

        Args:
            provider: Provider name.
            tokens: Expected token count for the request.

        Returns:
            RateLimitResult with allowed status and details.
        """
        with self._lock:
            limits = self._limits.get(provider)
            if not limits or not limits.enabled:
                return RateLimitResult(allowed=True, remaining=float("inf"))

            # Check concurrent requests
            if self._concurrent.get(provider, 0) >= limits.concurrent_requests:
                return RateLimitResult(
                    allowed=False,
                    limit_type="concurrent_requests",
                    remaining=0.0,
                )

            # Check request bucket
            request_bucket = self._request_buckets.get(provider)
            if request_bucket:
                request_bucket.refill()
                if request_bucket.tokens < 1.0:
                    wait_time = request_bucket.wait_time(1.0)
                    return RateLimitResult(
                        allowed=False,
                        wait_time=wait_time,
                        limit_type="requests_per_minute",
                        remaining=request_bucket.tokens,
                    )

            # Check token bucket if tokens specified
            if tokens > 0:
                token_bucket = self._token_buckets.get(provider)
                if token_bucket:
                    token_bucket.refill()
                    if token_bucket.tokens < tokens:
                        wait_time = token_bucket.wait_time(tokens)
                        return RateLimitResult(
                            allowed=False,
                            wait_time=wait_time,
                            limit_type="tokens_per_minute",
                            remaining=token_bucket.tokens,
                        )

            # Check daily limit
            self._check_daily_reset(provider)
            daily_used = self._daily_tokens.get(provider, 0.0)
            if daily_used + tokens > limits.tokens_per_day:
                return RateLimitResult(
                    allowed=False,
                    limit_type="tokens_per_day",
                    remaining=limits.tokens_per_day - daily_used,
                )

            # All checks passed
            remaining = float("inf")
            if request_bucket:
                remaining = min(remaining, request_bucket.tokens)

            return RateLimitResult(
                allowed=True,
                remaining=remaining,
            )

    def acquire(
        self,
        provider: str,
        tokens: int = 0,
        block: bool | None = None,
        timeout: float | None = None,
    ) -> RateLimitResult:
        """Acquire permission to make a request.

        Consumes tokens from the bucket and tracks concurrent requests.

        Args:
            provider: Provider name.
            tokens: Expected token count (for pre-check).
            block: Whether to block until allowed. Uses strategy if None.
            timeout: Maximum time to wait if blocking.

        Returns:
            RateLimitResult with acquisition status.

        Raises:
            RateLimitExceeded: If strategy is REJECT and limit exceeded.
        """
        if block is None:
            block = self._strategy == RateLimitStrategy.BLOCK

        start_time = time.monotonic()

        while True:
            with self._lock:
                result = self.check(provider, tokens)

                if result.allowed:
                    # Consume from request bucket
                    request_bucket = self._request_buckets.get(provider)
                    if request_bucket:
                        request_bucket.consume(1.0)

                    # Increment concurrent counter
                    self._concurrent[provider] = self._concurrent.get(provider, 0) + 1

                    return RateLimitResult(
                        allowed=True,
                        remaining=result.remaining,
                    )

                # Not allowed - handle based on strategy
                if not block:
                    if self._strategy == RateLimitStrategy.REJECT:
                        limits = self._limits.get(provider)
                        limit_value = 0.0
                        if limits:
                            if result.limit_type == "requests_per_minute":
                                limit_value = limits.requests_per_minute
                            elif result.limit_type == "tokens_per_minute":
                                limit_value = limits.tokens_per_minute
                            elif result.limit_type == "tokens_per_day":
                                limit_value = limits.tokens_per_day
                            elif result.limit_type == "concurrent_requests":
                                limit_value = float(limits.concurrent_requests)

                        raise RateLimitExceeded(
                            provider=provider,
                            limit_type=result.limit_type,
                            current=limit_value - result.remaining,
                            limit=limit_value,
                            retry_after=result.wait_time,
                        )

                    if self._strategy == RateLimitStrategy.DEGRADE:
                        return RateLimitResult(
                            allowed=True,
                            degraded=True,
                            limit_type=result.limit_type,
                        )

                    return result

                # Check timeout
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed >= timeout:
                        return RateLimitResult(
                            allowed=False,
                            wait_time=result.wait_time,
                            limit_type="timeout",
                        )

            # Wait and retry
            wait = min(result.wait_time, 0.1)  # Check every 100ms max
            if timeout is not None:
                elapsed = time.monotonic() - start_time
                wait = min(wait, timeout - elapsed)
            if wait > 0:
                time.sleep(wait)

    def release(
        self,
        provider: str,
        tokens_used: int = 0,
    ) -> None:
        """Release a request slot and record token usage.

        Call after request completes to update tracking.

        Args:
            provider: Provider name.
            tokens_used: Actual tokens used by the request.
        """
        with self._lock:
            # Decrement concurrent counter
            if provider in self._concurrent:
                self._concurrent[provider] = max(0, self._concurrent[provider] - 1)

            # Track daily token usage
            if tokens_used > 0:
                self._check_daily_reset(provider)
                self._daily_tokens[provider] = (
                    self._daily_tokens.get(provider, 0.0) + tokens_used
                )

    def _check_daily_reset(self, provider: str) -> None:
        """Check and reset daily token counter if needed.

        Args:
            provider: Provider name.
        """
        reset_time = self._daily_reset.get(provider, 0.0)
        now = time.monotonic()
        if now >= reset_time:
            self._daily_tokens[provider] = 0.0
            self._daily_reset[provider] = now + 86400.0

    def get_usage(self, provider: str) -> dict[str, Any]:
        """Get current usage statistics for a provider.

        Args:
            provider: Provider name.

        Returns:
            Dict with usage statistics.
        """
        with self._lock:
            limits = self._limits.get(provider)
            if not limits:
                return {"configured": False}

            request_bucket = self._request_buckets.get(provider)
            token_bucket = self._token_buckets.get(provider)

            return {
                "configured": True,
                "enabled": limits.enabled,
                "concurrent_requests": self._concurrent.get(provider, 0),
                "max_concurrent": limits.concurrent_requests,
                "requests_available": (
                    request_bucket.available() if request_bucket else 0.0
                ),
                "requests_per_minute": limits.requests_per_minute,
                "tokens_available": token_bucket.available() if token_bucket else 0.0,
                "tokens_per_minute": limits.tokens_per_minute,
                "daily_tokens_used": self._daily_tokens.get(provider, 0.0),
                "tokens_per_day": limits.tokens_per_day,
            }

    def reset(self, provider: str | None = None) -> None:
        """Reset rate limit state.

        Args:
            provider: Provider to reset, or None for all.
        """
        with self._lock:
            if provider is None:
                # Reset all
                for p in list(self._limits.keys()):
                    self._reset_provider(p)
            elif provider in self._limits:
                self._reset_provider(provider)

    def _reset_provider(self, provider: str) -> None:
        """Reset state for a single provider.

        Args:
            provider: Provider name.
        """
        limits = self._limits.get(provider)
        if limits:
            self._request_buckets[provider] = TokenBucket(
                capacity=limits.requests_per_minute,
                refill_rate=limits.requests_per_minute / 60.0,
            )
            self._token_buckets[provider] = TokenBucket(
                capacity=limits.tokens_per_minute,
                refill_rate=limits.tokens_per_minute / 60.0,
            )
        self._daily_tokens[provider] = 0.0
        self._daily_reset[provider] = time.monotonic() + 86400.0
        self._concurrent[provider] = 0

    def load_from_dict(self, config: dict[str, Any]) -> int:
        """Load provider limits from a dictionary.

        Args:
            config: Dict with provider configurations.

        Returns:
            Number of providers configured.
        """
        count = 0
        for provider, settings in config.items():
            if isinstance(settings, dict):
                self.configure(
                    provider=provider,
                    requests_per_minute=settings.get("requests_per_minute"),
                    tokens_per_minute=settings.get("tokens_per_minute"),
                    tokens_per_day=settings.get("tokens_per_day"),
                    concurrent_requests=settings.get("concurrent_requests"),
                    enabled=settings.get("enabled", True),
                )
                count += 1
        return count

    def to_dict(self) -> dict[str, Any]:
        """Export current configuration as a dictionary.

        Returns:
            Dict with all provider configurations.
        """
        result: dict[str, Any] = {}
        for provider, limits in self._limits.items():
            result[provider] = {
                "requests_per_minute": limits.requests_per_minute,
                "tokens_per_minute": limits.tokens_per_minute,
                "tokens_per_day": limits.tokens_per_day,
                "concurrent_requests": limits.concurrent_requests,
                "enabled": limits.enabled,
            }
        return result


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance.

    Returns:
        The global RateLimiter instance.
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the global rate limiter (useful for testing)."""
    global _rate_limiter
    _rate_limiter = None
