"""Provider selector with fallback chain for LLM providers.

This module provides the ProviderSelector class that implements intelligent
provider selection with automatic fallback when providers fail.

Supports three selection strategies:
- PRIORITY: Always try highest priority provider first
- ROUND_ROBIN: Distribute load across providers
- COST_BASED: Select cheapest available provider
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rice_factor.domain.artifacts.compiler_types import (
        CompilerContext,
        CompilerPassType,
        CompilerResult,
    )


class SelectionStrategy(Enum):
    """Provider selection strategy."""

    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"
    COST_BASED = "cost_based"


class AllProvidersFailedError(Exception):
    """Exception raised when all providers in the chain fail."""

    def __init__(self, errors: list[str]) -> None:
        """Initialize with list of errors from each provider.

        Args:
            errors: List of error messages from each provider attempt.
        """
        self.errors = errors
        message = f"All providers failed: {'; '.join(errors)}"
        super().__init__(message)


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider in the fallback chain.

    Attributes:
        name: Unique identifier for the provider (e.g., "claude", "ollama").
        adapter: The LLM adapter instance implementing LLMPort.
        priority: Selection priority (lower = higher priority).
        enabled: Whether this provider is currently enabled.
        cost_per_1k_input: Cost in USD per 1000 input tokens.
        cost_per_1k_output: Cost in USD per 1000 output tokens.
    """

    name: str
    adapter: Any  # LLMAdapter - uses duck typing to call generate()
    priority: int
    enabled: bool = True
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class SelectionResult:
    """Result of a provider selection and generation.

    Attributes:
        result: The CompilerResult from the successful provider.
        provider_name: Name of the provider that succeeded.
        attempts: Number of attempts made before success.
        all_errors: List of errors from failed attempts.
    """

    result: CompilerResult
    provider_name: str
    attempts: int = 1
    all_errors: list[str] = field(default_factory=list)


class ProviderSelector:
    """Selects LLM provider with automatic fallback support.

    The selector maintains a chain of providers and implements retry logic
    with automatic fallback to the next provider when one fails.

    Example:
        >>> providers = [
        ...     ProviderConfig("claude", claude_adapter, priority=1),
        ...     ProviderConfig("ollama", ollama_adapter, priority=2),
        ... ]
        >>> selector = ProviderSelector(providers)
        >>> result = selector.generate(pass_type, context, schema)
    """

    def __init__(
        self,
        providers: list[ProviderConfig],
        strategy: SelectionStrategy = SelectionStrategy.PRIORITY,
        max_retries: int = 3,
        timeout_seconds: float = 120.0,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        """Initialize the provider selector.

        Args:
            providers: List of provider configurations.
            strategy: Selection strategy (PRIORITY, ROUND_ROBIN, COST_BASED).
            max_retries: Maximum number of retry attempts across all providers.
            timeout_seconds: Timeout for each provider attempt.
            retry_delay_seconds: Delay between retry attempts.
        """
        # Filter enabled providers and sort by priority
        self._all_providers = providers
        self._providers = sorted(
            [p for p in providers if p.enabled],
            key=lambda p: p.priority,
        )
        self._strategy = strategy
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._retry_delay_seconds = retry_delay_seconds

        # Round-robin state
        self._current_index = 0

        # Availability cache
        self._availability_cache: dict[str, bool] = {}

    @property
    def strategy(self) -> SelectionStrategy:
        """Return the current selection strategy."""
        return self._strategy

    @property
    def enabled_providers(self) -> list[ProviderConfig]:
        """Return list of enabled providers sorted by priority."""
        return self._providers.copy()

    @property
    def all_providers(self) -> list[ProviderConfig]:
        """Return all providers including disabled ones."""
        return self._all_providers.copy()

    def set_strategy(self, strategy: SelectionStrategy) -> None:
        """Change the selection strategy.

        Args:
            strategy: New selection strategy.
        """
        self._strategy = strategy
        # Reset round-robin index when strategy changes
        self._current_index = 0

    def enable_provider(self, name: str) -> bool:
        """Enable a provider by name.

        Args:
            name: Provider name to enable.

        Returns:
            True if provider was found and enabled.
        """
        for p in self._all_providers:
            if p.name == name:
                p.enabled = True
                self._refresh_providers()
                return True
        return False

    def disable_provider(self, name: str) -> bool:
        """Disable a provider by name.

        Args:
            name: Provider name to disable.

        Returns:
            True if provider was found and disabled.
        """
        for p in self._all_providers:
            if p.name == name:
                p.enabled = False
                self._refresh_providers()
                return True
        return False

    def _refresh_providers(self) -> None:
        """Refresh the enabled providers list."""
        self._providers = sorted(
            [p for p in self._all_providers if p.enabled],
            key=lambda p: p.priority,
        )

    def check_availability(self) -> dict[str, bool]:
        """Check availability of all enabled providers.

        Returns:
            Dict mapping provider names to availability status.
        """
        result: dict[str, bool] = {}
        for provider in self._providers:
            try:
                # Most adapters have is_available method
                if hasattr(provider.adapter, "is_available"):
                    available = provider.adapter.is_available()
                    result[provider.name] = bool(available)
                else:
                    # Assume available if no check method
                    result[provider.name] = True
            except Exception:
                result[provider.name] = False

        self._availability_cache = result
        return result

    def get_provider(self, name: str) -> ProviderConfig | None:
        """Get a provider by name.

        Args:
            name: Provider name.

        Returns:
            ProviderConfig if found, None otherwise.
        """
        for p in self._all_providers:
            if p.name == name:
                return p
        return None

    def _select_provider(self) -> ProviderConfig:
        """Select a provider based on the current strategy.

        Returns:
            The selected provider configuration.

        Raises:
            AllProvidersFailedError: If no providers are available.
        """
        if not self._providers:
            raise AllProvidersFailedError(["No enabled providers available"])

        if self._strategy == SelectionStrategy.PRIORITY:
            return self._providers[0]

        elif self._strategy == SelectionStrategy.ROUND_ROBIN:
            provider = self._providers[self._current_index % len(self._providers)]
            return provider

        elif self._strategy == SelectionStrategy.COST_BASED:
            return min(
                self._providers,
                key=lambda p: p.cost_per_1k_input + p.cost_per_1k_output,
            )

        # Default to priority
        return self._providers[0]

    def _advance_provider(self) -> None:
        """Advance to the next provider in round-robin rotation."""
        self._current_index += 1

    def _get_fallback_order(self, start_provider: ProviderConfig) -> list[ProviderConfig]:
        """Get providers in fallback order starting from a given provider.

        Args:
            start_provider: The provider to start from.

        Returns:
            List of providers in fallback order.
        """
        if self._strategy == SelectionStrategy.PRIORITY:
            # For priority, just use priority order
            return self._providers.copy()

        elif self._strategy == SelectionStrategy.ROUND_ROBIN:
            # Start from current index and wrap around
            n = len(self._providers)
            idx = self._providers.index(start_provider) if start_provider in self._providers else 0
            return [self._providers[(idx + i) % n] for i in range(n)]

        elif self._strategy == SelectionStrategy.COST_BASED:
            # Sort by cost for fallback
            return sorted(
                self._providers,
                key=lambda p: p.cost_per_1k_input + p.cost_per_1k_output,
            )

        return self._providers.copy()

    def generate(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> SelectionResult:
        """Generate an artifact with automatic fallback.

        Tries providers in order based on the selection strategy.
        Falls back to the next provider if one fails.

        Args:
            pass_type: The compiler pass type.
            context: The compilation context.
            schema: JSON Schema for the expected output.

        Returns:
            SelectionResult with the CompilerResult and provider info.

        Raises:
            AllProvidersFailedError: If all providers fail.
        """
        if not self._providers:
            raise AllProvidersFailedError(["No enabled providers available"])

        errors: list[str] = []
        start_provider = self._select_provider()
        fallback_order = self._get_fallback_order(start_provider)

        for attempt, provider in enumerate(fallback_order, start=1):
            if attempt > self._max_retries:
                break

            try:
                result = provider.adapter.generate(pass_type, context, schema)

                # Advance round-robin on success
                if self._strategy == SelectionStrategy.ROUND_ROBIN:
                    self._advance_provider()

                return SelectionResult(
                    result=result,
                    provider_name=provider.name,
                    attempts=attempt,
                    all_errors=errors,
                )

            except Exception as e:
                error_msg = f"{provider.name}: {type(e).__name__}: {e}"
                errors.append(error_msg)

        raise AllProvidersFailedError(errors)

    async def generate_async(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
        schema: dict[str, object],
    ) -> SelectionResult:
        """Generate an artifact with automatic fallback (async).

        Async version of generate() for use with async adapters.

        Args:
            pass_type: The compiler pass type.
            context: The compilation context.
            schema: JSON Schema for the expected output.

        Returns:
            SelectionResult with the CompilerResult and provider info.

        Raises:
            AllProvidersFailedError: If all providers fail.
        """
        if not self._providers:
            raise AllProvidersFailedError(["No enabled providers available"])

        errors: list[str] = []
        start_provider = self._select_provider()
        fallback_order = self._get_fallback_order(start_provider)

        for attempt, provider in enumerate(fallback_order, start=1):
            if attempt > self._max_retries:
                break

            try:
                # Check if adapter has async generate method
                if hasattr(provider.adapter, "generate_async"):
                    coro = provider.adapter.generate_async(pass_type, context, schema)
                    result = await asyncio.wait_for(
                        coro,
                        timeout=self._timeout_seconds,
                    )
                else:
                    # Fall back to sync generate
                    result = provider.adapter.generate(pass_type, context, schema)

                # Advance round-robin on success
                if self._strategy == SelectionStrategy.ROUND_ROBIN:
                    self._advance_provider()

                return SelectionResult(
                    result=result,
                    provider_name=provider.name,
                    attempts=attempt,
                    all_errors=errors,
                )

            except TimeoutError:
                error_msg = f"{provider.name}: Timeout after {self._timeout_seconds}s"
                errors.append(error_msg)

            except Exception as e:
                error_msg = f"{provider.name}: {type(e).__name__}: {e}"
                errors.append(error_msg)

            # Delay before retry
            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_delay_seconds)

        raise AllProvidersFailedError(errors)


def create_provider_selector_from_config() -> ProviderSelector:
    """Create a ProviderSelector from application configuration.

    Reads llm.fallback configuration from Rice-Factor settings
    and instantiates configured providers.

    Returns:
        Configured ProviderSelector instance.
    """
    from rice_factor.adapters.llm import (
        create_claude_adapter_from_config,
        create_ollama_adapter_from_config,
        create_openai_adapter_from_config,
        create_openai_compat_adapter_from_config,
        create_vllm_adapter_from_config,
    )
    from rice_factor.config.settings import settings

    # Default provider costs (USD per 1k tokens)
    PROVIDER_COSTS: dict[str, dict[str, float]] = {
        "claude": {"input": 0.003, "output": 0.015},
        "openai": {"input": 0.005, "output": 0.015},
        "ollama": {"input": 0.0, "output": 0.0},
        "vllm": {"input": 0.0, "output": 0.0},
        "openai_compat": {"input": 0.0, "output": 0.0},
    }

    # Factory functions for each provider
    PROVIDER_FACTORIES: dict[str, Any] = {
        "claude": create_claude_adapter_from_config,
        "openai": create_openai_adapter_from_config,
        "ollama": create_ollama_adapter_from_config,
        "vllm": create_vllm_adapter_from_config,
        "openai_compat": create_openai_compat_adapter_from_config,
    }

    # Get fallback chain configuration
    fallback_config = settings.get("llm.fallback", {})
    provider_order = fallback_config.get(
        "providers", ["claude", "openai", "ollama"]
    )
    strategy_str = fallback_config.get("strategy", "priority")
    max_retries = fallback_config.get("max_retries", 3)
    timeout = fallback_config.get("timeout_seconds", 120.0)

    # Map strategy string to enum
    strategy_map = {
        "priority": SelectionStrategy.PRIORITY,
        "round_robin": SelectionStrategy.ROUND_ROBIN,
        "cost_based": SelectionStrategy.COST_BASED,
    }
    strategy = strategy_map.get(strategy_str, SelectionStrategy.PRIORITY)

    # Build provider configs
    providers: list[ProviderConfig] = []
    for priority, provider_name in enumerate(provider_order, start=1):
        if provider_name not in PROVIDER_FACTORIES:
            continue

        try:
            adapter = PROVIDER_FACTORIES[provider_name]()
            costs = PROVIDER_COSTS.get(provider_name, {"input": 0.0, "output": 0.0})

            providers.append(
                ProviderConfig(
                    name=provider_name,
                    adapter=adapter,
                    priority=priority,
                    enabled=True,
                    cost_per_1k_input=costs["input"],
                    cost_per_1k_output=costs["output"],
                )
            )
        except Exception:
            # Skip providers that fail to initialize
            continue

    return ProviderSelector(
        providers=providers,
        strategy=strategy,
        max_retries=max_retries,
        timeout_seconds=timeout,
    )
