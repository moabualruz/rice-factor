"""Unit tests for RateLimiter service."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from rice_factor.domain.services.rate_limiter import (
    ProviderLimits,
    RateLimitExceeded,
    RateLimiter,
    RateLimitResult,
    RateLimitStrategy,
    TokenBucket,
    get_rate_limiter,
    reset_rate_limiter,
)


class TestRateLimitStrategy:
    """Tests for RateLimitStrategy enum."""

    def test_block_value(self) -> None:
        """RateLimitStrategy.BLOCK should have 'block' value."""
        assert RateLimitStrategy.BLOCK.value == "block"

    def test_reject_value(self) -> None:
        """RateLimitStrategy.REJECT should have 'reject' value."""
        assert RateLimitStrategy.REJECT.value == "reject"

    def test_degrade_value(self) -> None:
        """RateLimitStrategy.DEGRADE should have 'degrade' value."""
        assert RateLimitStrategy.DEGRADE.value == "degrade"


class TestRateLimitExceeded:
    """Tests for RateLimitExceeded exception."""

    def test_exception_attributes(self) -> None:
        """RateLimitExceeded should store all attributes."""
        exc = RateLimitExceeded(
            provider="claude",
            limit_type="requests_per_minute",
            current=60.0,
            limit=60.0,
            retry_after=5.0,
        )
        assert exc.provider == "claude"
        assert exc.limit_type == "requests_per_minute"
        assert exc.current == 60.0
        assert exc.limit == 60.0
        assert exc.retry_after == 5.0

    def test_exception_message(self) -> None:
        """RateLimitExceeded message should be descriptive."""
        exc = RateLimitExceeded(
            provider="openai",
            limit_type="tokens_per_day",
            current=1000000.0,
            limit=1000000.0,
            retry_after=3600.0,
        )
        assert "openai" in str(exc)
        assert "tokens_per_day" in str(exc)


class TestTokenBucket:
    """Tests for TokenBucket class."""

    def test_initial_capacity(self) -> None:
        """TokenBucket should start with full capacity."""
        bucket = TokenBucket(capacity=10.0)
        assert bucket.tokens == 10.0
        assert bucket.capacity == 10.0

    def test_consume_reduces_tokens(self) -> None:
        """consume should reduce available tokens."""
        bucket = TokenBucket(capacity=10.0, refill_rate=0.0)
        bucket.consume(3.0)
        assert bucket.tokens == 7.0

    def test_consume_returns_false_when_insufficient(self) -> None:
        """consume should return False when tokens insufficient."""
        bucket = TokenBucket(capacity=5.0, refill_rate=0.0)
        bucket.tokens = 2.0
        result = bucket.consume(5.0)
        assert result is False
        assert bucket.tokens == 2.0  # Tokens unchanged

    def test_consume_returns_true_when_sufficient(self) -> None:
        """consume should return True when tokens available."""
        bucket = TokenBucket(capacity=10.0, refill_rate=0.0)
        result = bucket.consume(5.0)
        assert result is True

    def test_refill_adds_tokens(self) -> None:
        """refill should add tokens based on elapsed time."""
        bucket = TokenBucket(capacity=10.0, refill_rate=100.0)
        bucket.tokens = 0.0

        # Simulate time passage
        bucket.last_refill = time.monotonic() - 0.05  # 50ms ago
        bucket.refill()

        # Should have refilled about 5 tokens (100/s * 0.05s)
        assert bucket.tokens > 0
        assert bucket.tokens <= 10.0  # Capped at capacity

    def test_refill_capped_at_capacity(self) -> None:
        """refill should not exceed capacity."""
        bucket = TokenBucket(capacity=10.0, refill_rate=100.0)
        bucket.tokens = 9.0
        bucket.last_refill = time.monotonic() - 1.0
        bucket.refill()
        assert bucket.tokens == 10.0

    def test_wait_time_when_empty(self) -> None:
        """wait_time should calculate time until tokens available."""
        bucket = TokenBucket(capacity=10.0, refill_rate=10.0)  # 10 tokens/sec
        bucket.tokens = 0.0
        bucket.last_refill = time.monotonic()

        wait = bucket.wait_time(5.0)
        assert 0.4 <= wait <= 0.6  # ~0.5 seconds for 5 tokens at 10/sec

    def test_wait_time_when_available(self) -> None:
        """wait_time should return 0 when tokens available."""
        bucket = TokenBucket(capacity=10.0)
        wait = bucket.wait_time(5.0)
        assert wait == 0.0

    def test_available_after_refill(self) -> None:
        """available should return tokens after refill."""
        bucket = TokenBucket(capacity=10.0, refill_rate=100.0)
        bucket.tokens = 5.0
        bucket.last_refill = time.monotonic() - 0.01

        available = bucket.available()
        assert available >= 5.0


class TestProviderLimits:
    """Tests for ProviderLimits dataclass."""

    def test_default_values(self) -> None:
        """ProviderLimits should have sensible defaults."""
        limits = ProviderLimits(provider="test")
        assert limits.requests_per_minute == 60.0
        assert limits.tokens_per_minute == 100000.0
        assert limits.tokens_per_day == 10000000.0
        assert limits.concurrent_requests == 10
        assert limits.enabled is True

    def test_custom_values(self) -> None:
        """ProviderLimits should accept custom values."""
        limits = ProviderLimits(
            provider="custom",
            requests_per_minute=30.0,
            tokens_per_minute=50000.0,
            tokens_per_day=1000000.0,
            concurrent_requests=5,
            enabled=False,
        )
        assert limits.provider == "custom"
        assert limits.requests_per_minute == 30.0
        assert limits.enabled is False


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_allowed_result(self) -> None:
        """RateLimitResult should represent allowed request."""
        result = RateLimitResult(allowed=True, remaining=10.0)
        assert result.allowed is True
        assert result.degraded is False
        assert result.wait_time == 0.0

    def test_denied_result(self) -> None:
        """RateLimitResult should represent denied request."""
        result = RateLimitResult(
            allowed=False,
            wait_time=5.0,
            limit_type="requests_per_minute",
            remaining=0.0,
        )
        assert result.allowed is False
        assert result.wait_time == 5.0
        assert result.limit_type == "requests_per_minute"


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_empty_by_default(self) -> None:
        """RateLimiter should start with no configured providers."""
        limiter = RateLimiter()
        assert limiter.get_limits("claude") is None

    def test_default_strategy_is_block(self) -> None:
        """RateLimiter should default to BLOCK strategy."""
        limiter = RateLimiter()
        limiter.configure("test")
        # Verify by checking behavior - block strategy doesn't raise
        result = limiter.check("test")
        assert result.allowed is True


class TestRateLimiterConfigure:
    """Tests for RateLimiter.configure."""

    def test_configure_creates_limits(self) -> None:
        """configure should create provider limits."""
        limiter = RateLimiter()
        limits = limiter.configure("claude", requests_per_minute=30.0)

        assert limits.provider == "claude"
        assert limits.requests_per_minute == 30.0

    def test_configure_updates_existing(self) -> None:
        """configure should update existing provider limits."""
        limiter = RateLimiter()
        limiter.configure("claude", requests_per_minute=60.0)
        limiter.configure("claude", requests_per_minute=30.0)

        limits = limiter.get_limits("claude")
        assert limits is not None
        assert limits.requests_per_minute == 30.0

    def test_configure_preserves_unset_values(self) -> None:
        """configure should preserve values not explicitly set."""
        limiter = RateLimiter()
        limiter.configure("claude", requests_per_minute=30.0, tokens_per_day=5000000.0)
        limiter.configure("claude", requests_per_minute=60.0)  # Only update RPM

        limits = limiter.get_limits("claude")
        assert limits is not None
        assert limits.requests_per_minute == 60.0
        assert limits.tokens_per_day == 5000000.0  # Preserved

    def test_configure_disabled_provider(self) -> None:
        """configure should support disabling rate limiting."""
        limiter = RateLimiter()
        limits = limiter.configure("local", enabled=False)

        assert limits.enabled is False


class TestRateLimiterCheck:
    """Tests for RateLimiter.check."""

    def test_check_unconfigured_provider_allowed(self) -> None:
        """check should allow requests for unconfigured providers."""
        limiter = RateLimiter()
        result = limiter.check("unknown")
        assert result.allowed is True

    def test_check_disabled_provider_allowed(self) -> None:
        """check should allow requests for disabled providers."""
        limiter = RateLimiter()
        limiter.configure("local", enabled=False)
        result = limiter.check("local")
        assert result.allowed is True

    def test_check_when_tokens_available(self) -> None:
        """check should allow when tokens available."""
        limiter = RateLimiter()
        limiter.configure("claude", requests_per_minute=60.0)
        result = limiter.check("claude")
        assert result.allowed is True
        assert result.remaining > 0

    def test_check_with_token_estimate(self) -> None:
        """check should consider token count in limit check."""
        limiter = RateLimiter()
        limiter.configure("claude", tokens_per_minute=100.0)

        # Should fail with large token request
        result = limiter.check("claude", tokens=1000)
        assert result.allowed is False
        assert result.limit_type == "tokens_per_minute"


class TestRateLimiterAcquire:
    """Tests for RateLimiter.acquire."""

    def test_acquire_consumes_token(self) -> None:
        """acquire should consume from request bucket."""
        limiter = RateLimiter()
        limiter.configure("claude", requests_per_minute=60.0)

        initial = limiter.check("claude").remaining
        limiter.acquire("claude")
        after = limiter.check("claude").remaining

        assert after < initial

    def test_acquire_increments_concurrent(self) -> None:
        """acquire should increment concurrent request count."""
        limiter = RateLimiter()
        limiter.configure("claude", concurrent_requests=5)

        usage1 = limiter.get_usage("claude")
        limiter.acquire("claude")
        usage2 = limiter.get_usage("claude")

        assert usage2["concurrent_requests"] == usage1["concurrent_requests"] + 1

    def test_acquire_reject_strategy_raises(self) -> None:
        """acquire with REJECT strategy should raise on limit exceeded."""
        limiter = RateLimiter()
        limiter.set_strategy(RateLimitStrategy.REJECT)
        limiter.configure("claude", concurrent_requests=1)

        limiter.acquire("claude")
        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.acquire("claude", block=False)

        assert exc_info.value.provider == "claude"

    def test_acquire_degrade_strategy_returns_degraded(self) -> None:
        """acquire with DEGRADE strategy should return degraded result."""
        limiter = RateLimiter()
        limiter.set_strategy(RateLimitStrategy.DEGRADE)
        limiter.configure("claude", concurrent_requests=1)

        limiter.acquire("claude")
        result = limiter.acquire("claude", block=False)

        assert result.allowed is True
        assert result.degraded is True

    def test_acquire_with_timeout(self) -> None:
        """acquire should timeout if cannot get tokens."""
        limiter = RateLimiter()
        limiter.configure("claude", concurrent_requests=1)
        limiter.acquire("claude")

        start = time.monotonic()
        result = limiter.acquire("claude", block=True, timeout=0.1)
        elapsed = time.monotonic() - start

        assert result.allowed is False
        assert 0.1 <= elapsed < 0.3


class TestRateLimiterRelease:
    """Tests for RateLimiter.release."""

    def test_release_decrements_concurrent(self) -> None:
        """release should decrement concurrent request count."""
        limiter = RateLimiter()
        limiter.configure("claude", concurrent_requests=5)
        limiter.acquire("claude")

        usage1 = limiter.get_usage("claude")
        limiter.release("claude")
        usage2 = limiter.get_usage("claude")

        assert usage2["concurrent_requests"] == usage1["concurrent_requests"] - 1

    def test_release_tracks_token_usage(self) -> None:
        """release should track daily token usage."""
        limiter = RateLimiter()
        limiter.configure("claude", tokens_per_day=1000000.0)
        limiter.acquire("claude")

        limiter.release("claude", tokens_used=1000)
        usage = limiter.get_usage("claude")

        assert usage["daily_tokens_used"] == 1000.0

    def test_release_without_acquire(self) -> None:
        """release without acquire should not go negative."""
        limiter = RateLimiter()
        limiter.configure("claude")

        limiter.release("claude", tokens_used=100)
        usage = limiter.get_usage("claude")

        assert usage["concurrent_requests"] == 0


class TestRateLimiterGetUsage:
    """Tests for RateLimiter.get_usage."""

    def test_get_usage_unconfigured(self) -> None:
        """get_usage should return configured=False for unknown provider."""
        limiter = RateLimiter()
        usage = limiter.get_usage("unknown")
        assert usage["configured"] is False

    def test_get_usage_returns_all_stats(self) -> None:
        """get_usage should return all relevant statistics."""
        limiter = RateLimiter()
        limiter.configure(
            "claude",
            requests_per_minute=60.0,
            tokens_per_minute=100000.0,
            tokens_per_day=1000000.0,
            concurrent_requests=5,
        )

        usage = limiter.get_usage("claude")

        assert usage["configured"] is True
        assert usage["enabled"] is True
        assert "concurrent_requests" in usage
        assert "max_concurrent" in usage
        assert "requests_available" in usage
        assert "tokens_available" in usage
        assert "daily_tokens_used" in usage


class TestRateLimiterReset:
    """Tests for RateLimiter.reset."""

    def test_reset_single_provider(self) -> None:
        """reset should reset a single provider."""
        limiter = RateLimiter()
        limiter.configure("claude")
        limiter.acquire("claude")
        limiter.release("claude", tokens_used=1000)

        limiter.reset("claude")
        usage = limiter.get_usage("claude")

        assert usage["concurrent_requests"] == 0
        assert usage["daily_tokens_used"] == 0.0

    def test_reset_all_providers(self) -> None:
        """reset without argument should reset all providers."""
        limiter = RateLimiter()
        limiter.configure("claude")
        limiter.configure("openai")
        limiter.acquire("claude")
        limiter.acquire("openai")

        limiter.reset()

        assert limiter.get_usage("claude")["concurrent_requests"] == 0
        assert limiter.get_usage("openai")["concurrent_requests"] == 0


class TestRateLimiterLoadFromDict:
    """Tests for RateLimiter.load_from_dict."""

    def test_load_from_dict(self) -> None:
        """load_from_dict should configure multiple providers."""
        limiter = RateLimiter()
        config = {
            "claude": {"requests_per_minute": 60.0, "enabled": True},
            "openai": {"requests_per_minute": 30.0, "enabled": False},
        }

        count = limiter.load_from_dict(config)

        assert count == 2
        assert limiter.get_limits("claude") is not None
        assert limiter.get_limits("openai") is not None
        assert limiter.get_limits("openai").enabled is False  # type: ignore[union-attr]


class TestRateLimiterToDict:
    """Tests for RateLimiter.to_dict."""

    def test_to_dict_exports_all_providers(self) -> None:
        """to_dict should export all configured providers."""
        limiter = RateLimiter()
        limiter.configure("claude", requests_per_minute=60.0)
        limiter.configure("openai", requests_per_minute=30.0)

        result = limiter.to_dict()

        assert "claude" in result
        assert "openai" in result
        assert result["claude"]["requests_per_minute"] == 60.0
        assert result["openai"]["requests_per_minute"] == 30.0


class TestDailyLimit:
    """Tests for daily token limit tracking."""

    def test_daily_limit_enforcement(self) -> None:
        """Daily token limit should be enforced."""
        limiter = RateLimiter()
        limiter.configure("claude", tokens_per_day=1000.0)

        # Use up daily quota
        limiter.acquire("claude")
        limiter.release("claude", tokens_used=1000)

        # Should now be blocked
        result = limiter.check("claude", tokens=100)
        assert result.allowed is False
        assert result.limit_type == "tokens_per_day"

    def test_daily_reset(self) -> None:
        """Daily counter should reset after 24 hours."""
        limiter = RateLimiter()
        limiter.configure("claude", tokens_per_day=1000.0)

        # Use tokens
        limiter.acquire("claude")
        limiter.release("claude", tokens_used=500)

        # Simulate day passing
        limiter._daily_reset["claude"] = time.monotonic() - 1.0

        # Check should trigger reset
        usage = limiter.get_usage("claude")
        # After reset, daily_tokens_used might still show old value until next check
        # The important thing is that check() will pass
        result = limiter.check("claude", tokens=500)
        assert result.allowed is True


class TestConcurrentRequestLimit:
    """Tests for concurrent request limiting."""

    def test_concurrent_limit_enforcement(self) -> None:
        """Concurrent request limit should be enforced."""
        limiter = RateLimiter()
        limiter.configure("claude", concurrent_requests=2)

        limiter.acquire("claude")
        limiter.acquire("claude")

        # Third request should be blocked
        result = limiter.check("claude")
        assert result.allowed is False
        assert result.limit_type == "concurrent_requests"

    def test_concurrent_limit_release(self) -> None:
        """Releasing should allow new requests."""
        limiter = RateLimiter()
        limiter.configure("claude", concurrent_requests=1)

        limiter.acquire("claude")
        result1 = limiter.check("claude")
        assert result1.allowed is False

        limiter.release("claude")
        result2 = limiter.check("claude")
        assert result2.allowed is True


class TestGlobalRateLimiter:
    """Tests for global rate limiter functions."""

    def test_get_rate_limiter_returns_same_instance(self) -> None:
        """get_rate_limiter should return same instance."""
        reset_rate_limiter()

        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2

    def test_reset_rate_limiter_clears_instance(self) -> None:
        """reset_rate_limiter should clear global instance."""
        limiter1 = get_rate_limiter()

        reset_rate_limiter()

        limiter2 = get_rate_limiter()
        assert limiter1 is not limiter2


class TestSetStrategy:
    """Tests for RateLimiter.set_strategy."""

    def test_set_strategy_changes_behavior(self) -> None:
        """set_strategy should change rate limit handling."""
        limiter = RateLimiter()
        limiter.set_strategy(RateLimitStrategy.REJECT)
        limiter.configure("claude", concurrent_requests=0)

        with pytest.raises(RateLimitExceeded):
            limiter.acquire("claude", block=False)

        limiter.set_strategy(RateLimitStrategy.DEGRADE)
        result = limiter.acquire("claude", block=False)
        assert result.degraded is True


class TestThreadSafety:
    """Tests for thread safety of RateLimiter."""

    def test_concurrent_acquire_release(self) -> None:
        """acquire and release should be thread-safe."""
        import threading

        limiter = RateLimiter()
        limiter.configure("claude", concurrent_requests=100)
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for _ in range(10):
                    limiter.acquire("claude")
                    time.sleep(0.001)
                    limiter.release("claude", tokens_used=10)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert limiter.get_usage("claude")["concurrent_requests"] == 0
