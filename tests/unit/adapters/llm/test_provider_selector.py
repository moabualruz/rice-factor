"""Unit tests for ProviderSelector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.llm.provider_selector import (
    AllProvidersFailedError,
    ProviderConfig,
    ProviderSelector,
    SelectionResult,
    SelectionStrategy,
)
from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)


def create_mock_adapter(
    success: bool = True,
    payload: dict | None = None,
    available: bool = True,
    raises: Exception | None = None,
) -> MagicMock:
    """Create a mock LLM adapter for testing."""
    adapter = MagicMock()

    if raises:
        adapter.generate.side_effect = raises
    else:
        adapter.generate.return_value = CompilerResult(
            success=success,
            payload=payload or {"test": "data"},
        )

    adapter.is_available.return_value = available
    return adapter


def create_context() -> CompilerContext:
    """Create a test CompilerContext."""
    return CompilerContext(
        pass_type=CompilerPassType.PROJECT,
        project_files={},
        artifacts={},
    )


class TestSelectionStrategy:
    """Tests for SelectionStrategy enum."""

    def test_priority_value(self) -> None:
        """SelectionStrategy.PRIORITY should have 'priority' value."""
        assert SelectionStrategy.PRIORITY.value == "priority"

    def test_round_robin_value(self) -> None:
        """SelectionStrategy.ROUND_ROBIN should have 'round_robin' value."""
        assert SelectionStrategy.ROUND_ROBIN.value == "round_robin"

    def test_cost_based_value(self) -> None:
        """SelectionStrategy.COST_BASED should have 'cost_based' value."""
        assert SelectionStrategy.COST_BASED.value == "cost_based"


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_default_enabled(self) -> None:
        """ProviderConfig should be enabled by default."""
        adapter = create_mock_adapter()
        config = ProviderConfig(name="test", adapter=adapter, priority=1)
        assert config.enabled is True

    def test_default_costs(self) -> None:
        """ProviderConfig should have zero costs by default."""
        adapter = create_mock_adapter()
        config = ProviderConfig(name="test", adapter=adapter, priority=1)
        assert config.cost_per_1k_input == 0.0
        assert config.cost_per_1k_output == 0.0

    def test_custom_costs(self) -> None:
        """ProviderConfig should accept custom costs."""
        adapter = create_mock_adapter()
        config = ProviderConfig(
            name="claude",
            adapter=adapter,
            priority=1,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
        )
        assert config.cost_per_1k_input == 0.003
        assert config.cost_per_1k_output == 0.015


class TestAllProvidersFailedError:
    """Tests for AllProvidersFailedError exception."""

    def test_message_format(self) -> None:
        """AllProvidersFailedError should format errors in message."""
        errors = ["claude: Timeout", "ollama: Connection refused"]
        exc = AllProvidersFailedError(errors)
        assert "claude: Timeout" in str(exc)
        assert "ollama: Connection refused" in str(exc)

    def test_errors_attribute(self) -> None:
        """AllProvidersFailedError should store errors list."""
        errors = ["error1", "error2"]
        exc = AllProvidersFailedError(errors)
        assert exc.errors == errors


class TestProviderSelectorInit:
    """Tests for ProviderSelector initialization."""

    def test_default_strategy(self) -> None:
        """ProviderSelector should use PRIORITY strategy by default."""
        adapter = create_mock_adapter()
        providers = [ProviderConfig("test", adapter, priority=1)]
        selector = ProviderSelector(providers)
        assert selector.strategy == SelectionStrategy.PRIORITY

    def test_filters_disabled_providers(self) -> None:
        """ProviderSelector should filter out disabled providers."""
        adapter1 = create_mock_adapter()
        adapter2 = create_mock_adapter()
        providers = [
            ProviderConfig("enabled", adapter1, priority=1, enabled=True),
            ProviderConfig("disabled", adapter2, priority=2, enabled=False),
        ]
        selector = ProviderSelector(providers)
        assert len(selector.enabled_providers) == 1
        assert selector.enabled_providers[0].name == "enabled"

    def test_sorts_by_priority(self) -> None:
        """ProviderSelector should sort providers by priority."""
        adapter1 = create_mock_adapter()
        adapter2 = create_mock_adapter()
        adapter3 = create_mock_adapter()
        providers = [
            ProviderConfig("low", adapter3, priority=3),
            ProviderConfig("high", adapter1, priority=1),
            ProviderConfig("mid", adapter2, priority=2),
        ]
        selector = ProviderSelector(providers)
        names = [p.name for p in selector.enabled_providers]
        assert names == ["high", "mid", "low"]

    def test_all_providers_includes_disabled(self) -> None:
        """all_providers should include disabled providers."""
        adapter1 = create_mock_adapter()
        adapter2 = create_mock_adapter()
        providers = [
            ProviderConfig("enabled", adapter1, priority=1, enabled=True),
            ProviderConfig("disabled", adapter2, priority=2, enabled=False),
        ]
        selector = ProviderSelector(providers)
        assert len(selector.all_providers) == 2


class TestProviderSelectorStrategy:
    """Tests for ProviderSelector strategy selection."""

    def test_priority_selects_first(self) -> None:
        """PRIORITY strategy should select highest priority provider."""
        adapter1 = create_mock_adapter()
        adapter2 = create_mock_adapter()
        providers = [
            ProviderConfig("second", adapter2, priority=2),
            ProviderConfig("first", adapter1, priority=1),
        ]
        selector = ProviderSelector(providers, strategy=SelectionStrategy.PRIORITY)
        context = create_context()

        result = selector.generate(CompilerPassType.PROJECT, context, {})

        assert result.provider_name == "first"
        adapter1.generate.assert_called_once()
        adapter2.generate.assert_not_called()

    def test_round_robin_rotates(self) -> None:
        """ROUND_ROBIN strategy should rotate through providers."""
        adapter1 = create_mock_adapter()
        adapter2 = create_mock_adapter()
        providers = [
            ProviderConfig("first", adapter1, priority=1),
            ProviderConfig("second", adapter2, priority=2),
        ]
        selector = ProviderSelector(providers, strategy=SelectionStrategy.ROUND_ROBIN)
        context = create_context()

        result1 = selector.generate(CompilerPassType.PROJECT, context, {})
        result2 = selector.generate(CompilerPassType.PROJECT, context, {})

        assert result1.provider_name == "first"
        assert result2.provider_name == "second"

    def test_cost_based_selects_cheapest(self) -> None:
        """COST_BASED strategy should select cheapest provider."""
        adapter1 = create_mock_adapter()
        adapter2 = create_mock_adapter()
        providers = [
            ProviderConfig(
                "expensive", adapter1, priority=1, cost_per_1k_input=0.01
            ),
            ProviderConfig("cheap", adapter2, priority=2, cost_per_1k_input=0.001),
        ]
        selector = ProviderSelector(providers, strategy=SelectionStrategy.COST_BASED)
        context = create_context()

        result = selector.generate(CompilerPassType.PROJECT, context, {})

        assert result.provider_name == "cheap"

    def test_set_strategy_changes_selection(self) -> None:
        """set_strategy should change the selection strategy."""
        adapter = create_mock_adapter()
        providers = [ProviderConfig("test", adapter, priority=1)]
        selector = ProviderSelector(providers, strategy=SelectionStrategy.PRIORITY)

        selector.set_strategy(SelectionStrategy.ROUND_ROBIN)

        assert selector.strategy == SelectionStrategy.ROUND_ROBIN


class TestProviderSelectorFallback:
    """Tests for ProviderSelector fallback behavior."""

    def test_fallback_on_exception(self) -> None:
        """Should fallback to next provider on exception."""
        adapter1 = create_mock_adapter(raises=RuntimeError("Failed"))
        adapter2 = create_mock_adapter()
        providers = [
            ProviderConfig("fails", adapter1, priority=1),
            ProviderConfig("succeeds", adapter2, priority=2),
        ]
        selector = ProviderSelector(providers)
        context = create_context()

        result = selector.generate(CompilerPassType.PROJECT, context, {})

        assert result.provider_name == "succeeds"
        assert result.attempts == 2
        assert len(result.all_errors) == 1

    def test_all_providers_fail(self) -> None:
        """Should raise AllProvidersFailedError when all providers fail."""
        adapter1 = create_mock_adapter(raises=RuntimeError("Error1"))
        adapter2 = create_mock_adapter(raises=RuntimeError("Error2"))
        providers = [
            ProviderConfig("first", adapter1, priority=1),
            ProviderConfig("second", adapter2, priority=2),
        ]
        selector = ProviderSelector(providers, max_retries=2)
        context = create_context()

        with pytest.raises(AllProvidersFailedError) as exc_info:
            selector.generate(CompilerPassType.PROJECT, context, {})

        assert len(exc_info.value.errors) == 2

    def test_respects_max_retries(self) -> None:
        """Should stop after max_retries attempts."""
        adapter1 = create_mock_adapter(raises=RuntimeError("Error"))
        adapter2 = create_mock_adapter(raises=RuntimeError("Error"))
        adapter3 = create_mock_adapter()  # This would succeed
        providers = [
            ProviderConfig("first", adapter1, priority=1),
            ProviderConfig("second", adapter2, priority=2),
            ProviderConfig("third", adapter3, priority=3),
        ]
        selector = ProviderSelector(providers, max_retries=2)
        context = create_context()

        with pytest.raises(AllProvidersFailedError):
            selector.generate(CompilerPassType.PROJECT, context, {})

        # Should not have tried third provider
        adapter3.generate.assert_not_called()

    def test_no_enabled_providers(self) -> None:
        """Should raise error when no providers are enabled."""
        adapter = create_mock_adapter()
        providers = [ProviderConfig("disabled", adapter, priority=1, enabled=False)]
        selector = ProviderSelector(providers)
        context = create_context()

        with pytest.raises(AllProvidersFailedError) as exc_info:
            selector.generate(CompilerPassType.PROJECT, context, {})

        assert "No enabled providers" in str(exc_info.value)


class TestProviderSelectorEnableDisable:
    """Tests for enabling/disabling providers."""

    def test_disable_provider(self) -> None:
        """disable_provider should remove provider from enabled list."""
        adapter1 = create_mock_adapter()
        adapter2 = create_mock_adapter()
        providers = [
            ProviderConfig("first", adapter1, priority=1),
            ProviderConfig("second", adapter2, priority=2),
        ]
        selector = ProviderSelector(providers)

        result = selector.disable_provider("first")

        assert result is True
        assert len(selector.enabled_providers) == 1
        assert selector.enabled_providers[0].name == "second"

    def test_enable_provider(self) -> None:
        """enable_provider should add provider back to enabled list."""
        adapter = create_mock_adapter()
        providers = [ProviderConfig("test", adapter, priority=1, enabled=False)]
        selector = ProviderSelector(providers)

        result = selector.enable_provider("test")

        assert result is True
        assert len(selector.enabled_providers) == 1

    def test_disable_nonexistent_provider(self) -> None:
        """disable_provider should return False for unknown provider."""
        adapter = create_mock_adapter()
        providers = [ProviderConfig("test", adapter, priority=1)]
        selector = ProviderSelector(providers)

        result = selector.disable_provider("nonexistent")

        assert result is False

    def test_enable_nonexistent_provider(self) -> None:
        """enable_provider should return False for unknown provider."""
        adapter = create_mock_adapter()
        providers = [ProviderConfig("test", adapter, priority=1)]
        selector = ProviderSelector(providers)

        result = selector.enable_provider("nonexistent")

        assert result is False


class TestProviderSelectorAvailability:
    """Tests for provider availability checking."""

    def test_check_availability(self) -> None:
        """check_availability should return dict of provider statuses."""
        adapter1 = create_mock_adapter(available=True)
        adapter2 = create_mock_adapter(available=False)
        providers = [
            ProviderConfig("available", adapter1, priority=1),
            ProviderConfig("unavailable", adapter2, priority=2),
        ]
        selector = ProviderSelector(providers)

        result = selector.check_availability()

        assert result["available"] is True
        assert result["unavailable"] is False

    def test_check_availability_handles_exception(self) -> None:
        """check_availability should return False on exception."""
        adapter = create_mock_adapter()
        adapter.is_available.side_effect = RuntimeError("Error")
        providers = [ProviderConfig("test", adapter, priority=1)]
        selector = ProviderSelector(providers)

        result = selector.check_availability()

        assert result["test"] is False


class TestProviderSelectorGetProvider:
    """Tests for get_provider method."""

    def test_get_existing_provider(self) -> None:
        """get_provider should return provider config if found."""
        adapter = create_mock_adapter()
        providers = [ProviderConfig("test", adapter, priority=1)]
        selector = ProviderSelector(providers)

        result = selector.get_provider("test")

        assert result is not None
        assert result.name == "test"

    def test_get_nonexistent_provider(self) -> None:
        """get_provider should return None if not found."""
        adapter = create_mock_adapter()
        providers = [ProviderConfig("test", adapter, priority=1)]
        selector = ProviderSelector(providers)

        result = selector.get_provider("nonexistent")

        assert result is None


class TestSelectionResult:
    """Tests for SelectionResult dataclass."""

    def test_default_attempts(self) -> None:
        """SelectionResult should default to 1 attempt."""
        result = SelectionResult(
            result=CompilerResult(success=True),
            provider_name="test",
        )
        assert result.attempts == 1

    def test_default_errors(self) -> None:
        """SelectionResult should default to empty error list."""
        result = SelectionResult(
            result=CompilerResult(success=True),
            provider_name="test",
        )
        assert result.all_errors == []


class TestCreateProviderSelectorFromConfig:
    """Tests for create_provider_selector_from_config function."""

    def test_creates_selector_with_defaults(self) -> None:
        """create_provider_selector_from_config should use defaults."""
        # This test verifies that the function runs and creates a selector
        # Even if some providers fail (e.g., missing API keys), it should work
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default=None: {
                "llm.fallback": {
                    "providers": [],  # Empty list means no providers
                    "strategy": "priority",
                },
            }.get(key, default)

            from rice_factor.adapters.llm.provider_selector import (
                create_provider_selector_from_config,
            )

            selector = create_provider_selector_from_config()

        assert selector.strategy == SelectionStrategy.PRIORITY
        # With empty providers list, we get 0 enabled providers
        assert len(selector.enabled_providers) == 0

    def test_creates_selector_with_round_robin_strategy(self) -> None:
        """create_provider_selector_from_config should handle round_robin strategy."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default=None: {
                "llm.fallback": {
                    "providers": [],
                    "strategy": "round_robin",
                },
            }.get(key, default)

            from rice_factor.adapters.llm.provider_selector import (
                create_provider_selector_from_config,
            )

            selector = create_provider_selector_from_config()

        assert selector.strategy == SelectionStrategy.ROUND_ROBIN

    def test_creates_selector_with_cost_based_strategy(self) -> None:
        """create_provider_selector_from_config should handle cost_based strategy."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default=None: {
                "llm.fallback": {
                    "providers": [],
                    "strategy": "cost_based",
                },
            }.get(key, default)

            from rice_factor.adapters.llm.provider_selector import (
                create_provider_selector_from_config,
            )

            selector = create_provider_selector_from_config()

        assert selector.strategy == SelectionStrategy.COST_BASED

    def test_unknown_strategy_defaults_to_priority(self) -> None:
        """create_provider_selector_from_config should default to priority for unknown strategy."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default=None: {
                "llm.fallback": {
                    "providers": [],
                    "strategy": "unknown_strategy",
                },
            }.get(key, default)

            from rice_factor.adapters.llm.provider_selector import (
                create_provider_selector_from_config,
            )

            selector = create_provider_selector_from_config()

        assert selector.strategy == SelectionStrategy.PRIORITY

    def test_unknown_provider_is_skipped(self) -> None:
        """create_provider_selector_from_config should skip unknown providers."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default=None: {
                "llm.fallback": {
                    "providers": ["unknown_provider", "another_unknown"],
                    "strategy": "priority",
                },
            }.get(key, default)

            from rice_factor.adapters.llm.provider_selector import (
                create_provider_selector_from_config,
            )

            selector = create_provider_selector_from_config()

        # Unknown providers should be skipped
        assert len(selector.enabled_providers) == 0
