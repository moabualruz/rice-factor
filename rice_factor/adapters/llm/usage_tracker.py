"""Usage tracking for LLM providers.

This module provides the UsageTracker class for tracking LLM usage
across providers, including token counts, costs, and latency metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class UsageRecord:
    """Record of a single LLM request.

    Attributes:
        timestamp: When the request was made.
        provider: Provider name (e.g., "claude", "ollama").
        model: Model identifier.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        latency_ms: Request latency in milliseconds.
        cost_usd: Calculated cost in USD.
        success: Whether the request succeeded.
        error: Error message if request failed.
    """

    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    success: bool = True
    error: str | None = None


@dataclass
class ProviderStats:
    """Aggregated statistics for a single provider.

    Attributes:
        provider: Provider name.
        total_requests: Total number of requests.
        successful_requests: Number of successful requests.
        total_input_tokens: Total input tokens used.
        total_output_tokens: Total output tokens generated.
        total_cost_usd: Total cost in USD.
        avg_latency_ms: Average latency in milliseconds.
        min_latency_ms: Minimum latency.
        max_latency_ms: Maximum latency.
    """

    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0


class UsageTracker:
    """Tracks LLM usage across providers.

    Provides methods for recording usage, calculating costs,
    and exporting metrics in various formats.

    Example:
        >>> tracker = UsageTracker()
        >>> tracker.record(
        ...     provider="claude",
        ...     model="claude-sonnet-4-20250514",
        ...     prompt="Hello",
        ...     response="Hi there!",
        ...     latency_ms=150.0,
        ...     cost_per_1k_input=0.003,
        ...     cost_per_1k_output=0.015,
        ... )
        >>> print(tracker.total_cost())
    """

    def __init__(self) -> None:
        """Initialize the usage tracker."""
        self._records: list[UsageRecord] = []

    def record(
        self,
        provider: str,
        model: str,
        prompt: str,
        response: str,
        latency_ms: float,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
        success: bool = True,
        error: str | None = None,
    ) -> UsageRecord:
        """Record an LLM request.

        Args:
            provider: Provider name.
            model: Model identifier.
            prompt: Input prompt text.
            response: Output response text.
            latency_ms: Request latency in milliseconds.
            cost_per_1k_input: Cost per 1000 input tokens.
            cost_per_1k_output: Cost per 1000 output tokens.
            success: Whether the request succeeded.
            error: Error message if failed.

        Returns:
            The recorded UsageRecord.
        """
        input_tokens = self.count_tokens(prompt)
        output_tokens = self.count_tokens(response)

        cost = (
            (input_tokens / 1000) * cost_per_1k_input
            + (output_tokens / 1000) * cost_per_1k_output
        )

        record = UsageRecord(
            timestamp=datetime.now(UTC),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost,
            success=success,
            error=error,
        )

        self._records.append(record)
        return record

    def record_with_tokens(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
        success: bool = True,
        error: str | None = None,
    ) -> UsageRecord:
        """Record an LLM request with known token counts.

        Use this when token counts are already available from the provider.

        Args:
            provider: Provider name.
            model: Model identifier.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            latency_ms: Request latency in milliseconds.
            cost_per_1k_input: Cost per 1000 input tokens.
            cost_per_1k_output: Cost per 1000 output tokens.
            success: Whether the request succeeded.
            error: Error message if failed.

        Returns:
            The recorded UsageRecord.
        """
        cost = (
            (input_tokens / 1000) * cost_per_1k_input
            + (output_tokens / 1000) * cost_per_1k_output
        )

        record = UsageRecord(
            timestamp=datetime.now(UTC),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost,
            success=success,
            error=error,
        )

        self._records.append(record)
        return record

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using simple estimation.

        Uses a simple heuristic: ~4 characters per token for English.
        For production, use tiktoken or model-specific tokenizers.

        Args:
            text: Text to count tokens for.

        Returns:
            Estimated token count.
        """
        # Simple heuristic: ~4 characters per token
        # More accurate would be to use tiktoken
        return max(1, len(text) // 4)

    def total_cost(self) -> float:
        """Get total cost across all providers.

        Returns:
            Total cost in USD.
        """
        return sum(r.cost_usd for r in self._records)

    def total_tokens(self) -> tuple[int, int]:
        """Get total input and output tokens.

        Returns:
            Tuple of (total_input_tokens, total_output_tokens).
        """
        input_total = sum(r.input_tokens for r in self._records)
        output_total = sum(r.output_tokens for r in self._records)
        return input_total, output_total

    def by_provider(self) -> dict[str, ProviderStats]:
        """Get usage statistics grouped by provider.

        Returns:
            Dict mapping provider names to ProviderStats.
        """
        stats: dict[str, ProviderStats] = {}

        for record in self._records:
            if record.provider not in stats:
                stats[record.provider] = ProviderStats(provider=record.provider)

            s = stats[record.provider]
            s.total_requests += 1
            if record.success:
                s.successful_requests += 1
            s.total_input_tokens += record.input_tokens
            s.total_output_tokens += record.output_tokens
            s.total_cost_usd += record.cost_usd
            s.min_latency_ms = min(s.min_latency_ms, record.latency_ms)
            s.max_latency_ms = max(s.max_latency_ms, record.latency_ms)

        # Calculate averages
        for s in stats.values():
            if s.total_requests > 0:
                total_latency = sum(
                    r.latency_ms
                    for r in self._records
                    if r.provider == s.provider
                )
                s.avg_latency_ms = total_latency / s.total_requests

        return stats

    def by_model(self) -> dict[str, float]:
        """Get cost breakdown by model.

        Returns:
            Dict mapping model names to total cost.
        """
        result: dict[str, float] = {}
        for record in self._records:
            result[record.model] = result.get(record.model, 0) + record.cost_usd
        return result

    def get_records(
        self,
        provider: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[UsageRecord]:
        """Get filtered usage records.

        Args:
            provider: Optional provider filter.
            since: Optional start datetime filter.
            until: Optional end datetime filter.

        Returns:
            List of matching UsageRecords.
        """
        records = self._records

        if provider:
            records = [r for r in records if r.provider == provider]

        if since:
            records = [r for r in records if r.timestamp >= since]

        if until:
            records = [r for r in records if r.timestamp <= until]

        return records

    def clear(self) -> int:
        """Clear all usage records.

        Returns:
            Number of records cleared.
        """
        count = len(self._records)
        self._records = []
        return count

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus metrics as a string.
        """
        lines: list[str] = []

        # Cost metrics
        lines.append("# HELP llm_cost_usd Total cost in USD by provider")
        lines.append("# TYPE llm_cost_usd counter")
        for provider, cost in self.by_provider().items():
            lines.append(f'llm_cost_usd{{provider="{provider}"}} {cost.total_cost_usd}')

        # Token metrics
        lines.append("# HELP llm_tokens_total Total tokens by type and provider")
        lines.append("# TYPE llm_tokens_total counter")
        for provider, stats in self.by_provider().items():
            lines.append(
                f'llm_tokens_total{{provider="{provider}",type="input"}} {stats.total_input_tokens}'
            )
            lines.append(
                f'llm_tokens_total{{provider="{provider}",type="output"}} {stats.total_output_tokens}'
            )

        # Request metrics
        lines.append("# HELP llm_requests_total Total requests by provider")
        lines.append("# TYPE llm_requests_total counter")
        for provider, stats in self.by_provider().items():
            lines.append(
                f'llm_requests_total{{provider="{provider}"}} {stats.total_requests}'
            )

        # Latency metrics
        lines.append("# HELP llm_latency_ms Request latency in milliseconds")
        lines.append("# TYPE llm_latency_ms gauge")
        for provider, stats in self.by_provider().items():
            lines.append(
                f'llm_latency_ms{{provider="{provider}",stat="avg"}} {stats.avg_latency_ms}'
            )
            lines.append(
                f'llm_latency_ms{{provider="{provider}",stat="min"}} {stats.min_latency_ms}'
            )
            lines.append(
                f'llm_latency_ms{{provider="{provider}",stat="max"}} {stats.max_latency_ms}'
            )

        return "\n".join(lines)

    def export_json(self) -> dict[str, Any]:
        """Export metrics as JSON-serializable dict.

        Returns:
            Dict with all usage metrics.
        """
        return {
            "total_cost_usd": self.total_cost(),
            "total_input_tokens": self.total_tokens()[0],
            "total_output_tokens": self.total_tokens()[1],
            "by_provider": {
                p: {
                    "total_requests": s.total_requests,
                    "successful_requests": s.successful_requests,
                    "total_input_tokens": s.total_input_tokens,
                    "total_output_tokens": s.total_output_tokens,
                    "total_cost_usd": s.total_cost_usd,
                    "avg_latency_ms": s.avg_latency_ms,
                }
                for p, s in self.by_provider().items()
            },
            "by_model": self.by_model(),
            "record_count": len(self._records),
        }


# Global tracker instance
_tracker: UsageTracker | None = None


def get_usage_tracker() -> UsageTracker:
    """Get the global usage tracker instance.

    Returns:
        The global UsageTracker instance.
    """
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker


def reset_usage_tracker() -> None:
    """Reset the global usage tracker (useful for testing)."""
    global _tracker
    _tracker = None
