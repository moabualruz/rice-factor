"""Cost tracking and billing alerts for LLM usage.

This module provides the CostTracker service that monitors LLM costs,
enforces spending limits, and triggers billing alerts at configurable
thresholds.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"  # Informational alert
    WARNING = "warning"  # Warning threshold reached
    CRITICAL = "critical"  # Critical threshold reached
    LIMIT = "limit"  # Hard limit reached


class CostLimitExceeded(Exception):
    """Raised when cost limit is exceeded."""

    def __init__(
        self,
        current_cost: float,
        limit: float,
        period: str,
    ) -> None:
        """Initialize the exception.

        Args:
            current_cost: Current accumulated cost.
            limit: Configured cost limit.
            period: Time period (daily, monthly, etc.).
        """
        self.current_cost = current_cost
        self.limit = limit
        self.period = period
        super().__init__(
            f"Cost limit exceeded: ${current_cost:.2f} / ${limit:.2f} ({period})"
        )


@dataclass
class CostRecord:
    """Record of a single cost event.

    Attributes:
        timestamp: When the cost was incurred.
        provider: Provider name.
        model: Model identifier.
        operation: Operation type (e.g., "generate", "embed").
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        cost_usd: Total cost in USD.
        metadata: Additional metadata.
    """

    timestamp: datetime
    provider: str
    model: str
    operation: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CostAlert:
    """Alert triggered when cost threshold is reached.

    Attributes:
        timestamp: When the alert was triggered.
        level: Alert severity level.
        threshold: Threshold value that was exceeded.
        current_value: Current cost value.
        period: Time period for the threshold.
        message: Human-readable alert message.
    """

    timestamp: datetime
    level: AlertLevel
    threshold: float
    current_value: float
    period: str
    message: str


@dataclass
class CostThreshold:
    """Cost threshold configuration.

    Attributes:
        amount: Threshold amount in USD.
        level: Alert level when threshold is reached.
        triggered: Whether this threshold has been triggered.
    """

    amount: float
    level: AlertLevel
    triggered: bool = False


@dataclass
class CostLimits:
    """Cost limits and thresholds for a period.

    Attributes:
        period: Time period (daily, monthly, etc.).
        hard_limit: Maximum allowed cost (blocks requests).
        thresholds: Alert thresholds.
        enabled: Whether limits are enabled.
    """

    period: str
    hard_limit: float | None = None
    thresholds: list[CostThreshold] = field(default_factory=list)
    enabled: bool = True


@dataclass
class CostSummary:
    """Summary of costs for a time period.

    Attributes:
        period: Time period covered.
        start_time: Start of the period.
        end_time: End of the period.
        total_cost: Total cost in USD.
        by_provider: Cost breakdown by provider.
        by_model: Cost breakdown by model.
        by_operation: Cost breakdown by operation.
        record_count: Number of records.
    """

    period: str
    start_time: datetime
    end_time: datetime
    total_cost: float
    by_provider: dict[str, float]
    by_model: dict[str, float]
    by_operation: dict[str, float]
    record_count: int


AlertHandler = Callable[[CostAlert], None]


class CostTracker:
    """Cost tracking service for LLM usage.

    Tracks costs, enforces spending limits, and triggers
    billing alerts at configurable thresholds.

    Example:
        >>> tracker = CostTracker()
        >>> tracker.set_daily_limit(100.0)
        >>> tracker.add_threshold("daily", 50.0, AlertLevel.WARNING)
        >>> tracker.record(
        ...     provider="claude",
        ...     model="claude-sonnet-4-20250514",
        ...     operation="generate",
        ...     input_tokens=1000,
        ...     output_tokens=500,
        ...     cost_usd=0.15,
        ... )
        >>> print(tracker.get_daily_cost())
    """

    def __init__(self) -> None:
        """Initialize the cost tracker."""
        self._records: list[CostRecord] = []
        self._limits: dict[str, CostLimits] = {}
        self._alert_handlers: list[AlertHandler] = []
        self._alerts: list[CostAlert] = []
        self._lock = threading.RLock()

        # Initialize default periods
        self._limits["daily"] = CostLimits(period="daily")
        self._limits["monthly"] = CostLimits(period="monthly")

    def record(
        self,
        provider: str,
        model: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        metadata: dict[str, Any] | None = None,
    ) -> CostRecord:
        """Record a cost event.

        Args:
            provider: Provider name.
            model: Model identifier.
            operation: Operation type.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            cost_usd: Cost in USD.
            metadata: Additional metadata.

        Returns:
            The recorded CostRecord.

        Raises:
            CostLimitExceeded: If recording would exceed a hard limit.
        """
        with self._lock:
            # Check hard limits before recording
            self._check_limits(cost_usd)

            record = CostRecord(
                timestamp=datetime.now(UTC),
                provider=provider,
                model=model,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                metadata=metadata or {},
            )

            self._records.append(record)

            # Check thresholds and trigger alerts
            self._check_thresholds()

            return record

    def _check_limits(self, additional_cost: float) -> None:
        """Check if adding cost would exceed any hard limits.

        Args:
            additional_cost: Cost to be added.

        Raises:
            CostLimitExceeded: If limit would be exceeded.
        """
        for period, limits in self._limits.items():
            if not limits.enabled or limits.hard_limit is None:
                continue

            current = self._get_period_cost(period)
            if current + additional_cost > limits.hard_limit:
                raise CostLimitExceeded(
                    current_cost=current + additional_cost,
                    limit=limits.hard_limit,
                    period=period,
                )

    def _check_thresholds(self) -> None:
        """Check all thresholds and trigger alerts."""
        for period, limits in self._limits.items():
            if not limits.enabled:
                continue

            current = self._get_period_cost(period)

            for threshold in limits.thresholds:
                if not threshold.triggered and current >= threshold.amount:
                    threshold.triggered = True
                    self._trigger_alert(
                        level=threshold.level,
                        threshold=threshold.amount,
                        current=current,
                        period=period,
                    )

    def _trigger_alert(
        self,
        level: AlertLevel,
        threshold: float,
        current: float,
        period: str,
    ) -> None:
        """Trigger an alert and notify handlers.

        Args:
            level: Alert severity level.
            threshold: Threshold that was exceeded.
            current: Current cost value.
            period: Time period.
        """
        alert = CostAlert(
            timestamp=datetime.now(UTC),
            level=level,
            threshold=threshold,
            current_value=current,
            period=period,
            message=f"{level.value.upper()}: {period} cost ${current:.2f} "
            f"exceeded threshold ${threshold:.2f}",
        )

        self._alerts.append(alert)

        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception:
                pass  # Don't let handler errors break tracking

    def _get_period_cost(self, period: str) -> float:
        """Get total cost for a time period.

        Args:
            period: Time period (daily, monthly, etc.).

        Returns:
            Total cost in USD for the period.
        """
        now = datetime.now(UTC)

        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            # Start of week (Monday)
            days_since_monday = now.weekday()
            start = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif period == "hourly":
            start = now.replace(minute=0, second=0, microsecond=0)
        else:
            # Custom period - use all records
            start = datetime.min.replace(tzinfo=UTC)

        return sum(r.cost_usd for r in self._records if r.timestamp >= start)

    def set_daily_limit(self, limit: float | None) -> None:
        """Set the daily hard limit.

        Args:
            limit: Maximum daily cost in USD, or None to disable.
        """
        with self._lock:
            self._limits["daily"].hard_limit = limit

    def set_monthly_limit(self, limit: float | None) -> None:
        """Set the monthly hard limit.

        Args:
            limit: Maximum monthly cost in USD, or None to disable.
        """
        with self._lock:
            self._limits["monthly"].hard_limit = limit

    def add_threshold(
        self,
        period: str,
        amount: float,
        level: AlertLevel = AlertLevel.WARNING,
    ) -> None:
        """Add an alert threshold.

        Args:
            period: Time period (daily, monthly, etc.).
            amount: Threshold amount in USD.
            level: Alert level when threshold is reached.
        """
        with self._lock:
            if period not in self._limits:
                self._limits[period] = CostLimits(period=period)

            self._limits[period].thresholds.append(
                CostThreshold(amount=amount, level=level)
            )
            # Sort thresholds by amount
            self._limits[period].thresholds.sort(key=lambda t: t.amount)

    def add_alert_handler(self, handler: AlertHandler) -> None:
        """Add a handler for cost alerts.

        Args:
            handler: Callback function for alerts.
        """
        with self._lock:
            self._alert_handlers.append(handler)

    def remove_alert_handler(self, handler: AlertHandler) -> bool:
        """Remove an alert handler.

        Args:
            handler: Handler to remove.

        Returns:
            True if handler was found and removed.
        """
        with self._lock:
            try:
                self._alert_handlers.remove(handler)
                return True
            except ValueError:
                return False

    def get_daily_cost(self) -> float:
        """Get today's total cost.

        Returns:
            Total cost in USD for today.
        """
        with self._lock:
            return self._get_period_cost("daily")

    def get_monthly_cost(self) -> float:
        """Get this month's total cost.

        Returns:
            Total cost in USD for this month.
        """
        with self._lock:
            return self._get_period_cost("monthly")

    def get_total_cost(self) -> float:
        """Get total cost across all records.

        Returns:
            Total cost in USD.
        """
        with self._lock:
            return sum(r.cost_usd for r in self._records)

    def get_alerts(
        self,
        level: AlertLevel | None = None,
        since: datetime | None = None,
    ) -> list[CostAlert]:
        """Get triggered alerts.

        Args:
            level: Optional level filter.
            since: Optional time filter.

        Returns:
            List of matching alerts.
        """
        with self._lock:
            alerts = self._alerts

            if level:
                alerts = [a for a in alerts if a.level == level]

            if since:
                alerts = [a for a in alerts if a.timestamp >= since]

            return alerts

    def get_summary(
        self,
        period: str = "daily",
    ) -> CostSummary:
        """Get a cost summary for a time period.

        Args:
            period: Time period (daily, monthly, etc.).

        Returns:
            CostSummary for the period.
        """
        with self._lock:
            now = datetime.now(UTC)

            if period == "daily":
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "monthly":
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == "weekly":
                days_since_monday = now.weekday()
                start = (now - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            else:
                start = datetime.min.replace(tzinfo=UTC)

            records = [r for r in self._records if r.timestamp >= start]

            by_provider: dict[str, float] = {}
            by_model: dict[str, float] = {}
            by_operation: dict[str, float] = {}

            for record in records:
                by_provider[record.provider] = (
                    by_provider.get(record.provider, 0) + record.cost_usd
                )
                by_model[record.model] = (
                    by_model.get(record.model, 0) + record.cost_usd
                )
                by_operation[record.operation] = (
                    by_operation.get(record.operation, 0) + record.cost_usd
                )

            return CostSummary(
                period=period,
                start_time=start,
                end_time=now,
                total_cost=sum(r.cost_usd for r in records),
                by_provider=by_provider,
                by_model=by_model,
                by_operation=by_operation,
                record_count=len(records),
            )

    def export_report(
        self,
        period: str = "daily",
        format: str = "json",
    ) -> str | dict[str, Any]:
        """Export a cost report.

        Args:
            period: Time period for the report.
            format: Output format (json, csv, text).

        Returns:
            Report in requested format.
        """
        with self._lock:
            summary = self.get_summary(period)

            if format == "json":
                return {
                    "period": summary.period,
                    "start_time": summary.start_time.isoformat(),
                    "end_time": summary.end_time.isoformat(),
                    "total_cost_usd": summary.total_cost,
                    "by_provider": summary.by_provider,
                    "by_model": summary.by_model,
                    "by_operation": summary.by_operation,
                    "record_count": summary.record_count,
                }

            elif format == "csv":
                lines = ["provider,model,operation,cost_usd"]
                for record in self._records:
                    if record.timestamp >= summary.start_time:
                        lines.append(
                            f"{record.provider},{record.model},"
                            f"{record.operation},{record.cost_usd:.6f}"
                        )
                return "\n".join(lines)

            else:  # text format
                lines = [
                    f"Cost Report - {summary.period.title()}",
                    f"Period: {summary.start_time.isoformat()} to {summary.end_time.isoformat()}",
                    f"Total Cost: ${summary.total_cost:.4f}",
                    f"Records: {summary.record_count}",
                    "",
                    "By Provider:",
                ]
                for provider, cost in sorted(
                    summary.by_provider.items(), key=lambda x: -x[1]
                ):
                    lines.append(f"  {provider}: ${cost:.4f}")

                lines.extend(["", "By Model:"])
                for model, cost in sorted(
                    summary.by_model.items(), key=lambda x: -x[1]
                ):
                    lines.append(f"  {model}: ${cost:.4f}")

                return "\n".join(lines)

    def reset_thresholds(self, period: str | None = None) -> None:
        """Reset threshold triggered status.

        Called at period boundaries to re-enable alerts.

        Args:
            period: Period to reset, or None for all.
        """
        with self._lock:
            if period is None:
                periods = list(self._limits.keys())
            else:
                periods = [period] if period in self._limits else []

            for p in periods:
                for threshold in self._limits[p].thresholds:
                    threshold.triggered = False

    def clear_records(
        self,
        before: datetime | None = None,
    ) -> int:
        """Clear cost records.

        Args:
            before: Optional cutoff time. Records before this are cleared.

        Returns:
            Number of records cleared.
        """
        with self._lock:
            if before is None:
                count = len(self._records)
                self._records = []
                return count

            original = len(self._records)
            self._records = [r for r in self._records if r.timestamp >= before]
            return original - len(self._records)

    def get_records(
        self,
        provider: str | None = None,
        model: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[CostRecord]:
        """Get filtered cost records.

        Args:
            provider: Optional provider filter.
            model: Optional model filter.
            since: Optional start time.
            until: Optional end time.

        Returns:
            List of matching records.
        """
        with self._lock:
            records = self._records

            if provider:
                records = [r for r in records if r.provider == provider]

            if model:
                records = [r for r in records if r.model == model]

            if since:
                records = [r for r in records if r.timestamp >= since]

            if until:
                records = [r for r in records if r.timestamp <= until]

            return records

    def to_dict(self) -> dict[str, Any]:
        """Export tracker state as dictionary.

        Returns:
            Dict with all tracker state.
        """
        with self._lock:
            return {
                "total_cost": self.get_total_cost(),
                "daily_cost": self.get_daily_cost(),
                "monthly_cost": self.get_monthly_cost(),
                "limits": {
                    p: {
                        "hard_limit": l.hard_limit,
                        "enabled": l.enabled,
                        "thresholds": [
                            {"amount": t.amount, "level": t.level.value}
                            for t in l.thresholds
                        ],
                    }
                    for p, l in self._limits.items()
                },
                "record_count": len(self._records),
                "alert_count": len(self._alerts),
            }


# Global cost tracker instance
_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance.

    Returns:
        The global CostTracker instance.
    """
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def reset_cost_tracker() -> None:
    """Reset the global cost tracker (useful for testing)."""
    global _cost_tracker
    _cost_tracker = None
