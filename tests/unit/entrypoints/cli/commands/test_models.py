"""Unit tests for models CLI command."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.domain.services.model_registry import ModelCapability, ModelInfo
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestModelsCommandHelp:
    """Tests for models command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["models", "--help"])
        assert result.exit_code == 0
        assert "model" in result.stdout.lower()

    def test_help_shows_options(self) -> None:
        """--help should show all options."""
        result = runner.invoke(app, ["models", "--help"])
        assert result.exit_code == 0
        assert "--provider" in result.stdout
        assert "--capability" in result.stdout
        assert "--local" in result.stdout
        assert "--cloud" in result.stdout
        assert "--available" in result.stdout
        assert "--json" in result.stdout


class TestModelsCommand:
    """Tests for models command."""

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_basic(self, mock_get_registry: MagicMock) -> None:
        """Test basic models output."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        mock_registry.get_all.return_value = [
            ModelInfo(
                id="claude-3-opus",
                provider="anthropic",
                capabilities=[ModelCapability.CODE, ModelCapability.CHAT],
                is_local=False,
                available=True,
                context_length=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                strengths=["coding", "reasoning"],
            ),
        ]

        result = runner.invoke(app, ["models"])

        assert result.exit_code == 0
        mock_registry.get_all.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_json_output(self, mock_get_registry: MagicMock) -> None:
        """Test models with --json output."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        mock_registry.get_all.return_value = [
            ModelInfo(
                id="claude-3-opus",
                provider="anthropic",
                capabilities=[ModelCapability.CODE, ModelCapability.CHAT],
                is_local=False,
                available=True,
                context_length=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                strengths=["coding"],
            ),
        ]

        result = runner.invoke(app, ["models", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "models" in data
        assert len(data["models"]) == 1
        assert data["models"][0]["id"] == "claude-3-opus"
        assert data["models"][0]["provider"] == "anthropic"

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_provider_filter(self, mock_get_registry: MagicMock) -> None:
        """Test models with --provider filter."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        mock_registry.get_all.return_value = [
            ModelInfo(
                id="claude-3-opus",
                provider="anthropic",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=True,
                context_length=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                strengths=[],
            ),
            ModelInfo(
                id="gpt-4",
                provider="openai",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=True,
                context_length=128000,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
                strengths=[],
            ),
        ]

        result = runner.invoke(app, ["models", "--provider", "anthropic", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["models"]) == 1
        assert data["models"][0]["provider"] == "anthropic"

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_capability_filter(self, mock_get_registry: MagicMock) -> None:
        """Test models with --capability filter."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        mock_registry.get_all.return_value = [
            ModelInfo(
                id="gpt-4-vision",
                provider="openai",
                capabilities=[ModelCapability.VISION],
                is_local=False,
                available=True,
                context_length=128000,
                cost_per_1k_input=0.01,
                cost_per_1k_output=0.03,
                strengths=[],
            ),
            ModelInfo(
                id="claude-3-opus",
                provider="anthropic",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=True,
                context_length=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                strengths=[],
            ),
        ]

        result = runner.invoke(app, ["models", "--capability", "vision", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["models"]) == 1
        assert "vision" in data["models"][0]["capabilities"]

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_local_only(self, mock_get_registry: MagicMock) -> None:
        """Test models with --local filter."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        mock_registry.get_all.return_value = [
            ModelInfo(
                id="llama-3",
                provider="ollama",
                capabilities=[ModelCapability.CODE],
                is_local=True,
                available=True,
                context_length=8192,
                cost_per_1k_input=0,
                cost_per_1k_output=0,
                strengths=[],
            ),
            ModelInfo(
                id="claude-3-opus",
                provider="anthropic",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=True,
                context_length=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                strengths=[],
            ),
        ]

        result = runner.invoke(app, ["models", "--local", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["models"]) == 1
        assert data["models"][0]["is_local"] is True

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_cloud_only(self, mock_get_registry: MagicMock) -> None:
        """Test models with --cloud filter."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        mock_registry.get_all.return_value = [
            ModelInfo(
                id="llama-3",
                provider="ollama",
                capabilities=[ModelCapability.CODE],
                is_local=True,
                available=True,
                context_length=8192,
                cost_per_1k_input=0,
                cost_per_1k_output=0,
                strengths=[],
            ),
            ModelInfo(
                id="claude-3-opus",
                provider="anthropic",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=True,
                context_length=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                strengths=[],
            ),
        ]

        result = runner.invoke(app, ["models", "--cloud", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["models"]) == 1
        assert data["models"][0]["is_local"] is False

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_available_only(self, mock_get_registry: MagicMock) -> None:
        """Test models with --available filter."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        mock_registry.get_all.return_value = [
            ModelInfo(
                id="claude-3-opus",
                provider="anthropic",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=True,
                context_length=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                strengths=[],
            ),
            ModelInfo(
                id="unavailable-model",
                provider="test",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=False,
                context_length=1000,
                cost_per_1k_input=0,
                cost_per_1k_output=0,
                strengths=[],
            ),
        ]

        result = runner.invoke(app, ["models", "--available", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["models"]) == 1
        assert data["models"][0]["available"] is True

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_no_models_found(self, mock_get_registry: MagicMock) -> None:
        """Test models when no models match filters."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry
        mock_registry.get_all.return_value = []

        result = runner.invoke(app, ["models"])

        assert result.exit_code == 0
        assert "no models" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.models.get_model_registry")
    def test_models_invalid_capability(self, mock_get_registry: MagicMock) -> None:
        """Test models with invalid capability value."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry
        mock_registry.get_all.return_value = [
            ModelInfo(
                id="claude-3-opus",
                provider="anthropic",
                capabilities=[ModelCapability.CODE],
                is_local=False,
                available=True,
                context_length=200000,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                strengths=[],
            ),
        ]

        result = runner.invoke(app, ["models", "--capability", "invalid"])

        # Should handle gracefully - no models match invalid capability
        assert result.exit_code == 0


class TestModelsHelperFunctions:
    """Tests for helper functions."""

    def test_format_capabilities(self) -> None:
        """Test capability formatting."""
        from rice_factor.entrypoints.cli.commands.models import _format_capabilities

        caps = [ModelCapability.CODE, ModelCapability.CHAT]
        result = _format_capabilities(caps)
        assert "code" in result.lower()
        assert "chat" in result.lower()

    def test_format_capabilities_empty(self) -> None:
        """Test formatting empty capabilities."""
        from rice_factor.entrypoints.cli.commands.models import _format_capabilities

        result = _format_capabilities([])
        assert result == "-"

    def test_format_cost_free(self) -> None:
        """Test free cost formatting."""
        from rice_factor.entrypoints.cli.commands.models import _format_cost

        result = _format_cost(0, 0)
        assert "free" in result.lower()

    def test_format_cost_paid(self) -> None:
        """Test paid cost formatting."""
        from rice_factor.entrypoints.cli.commands.models import _format_cost

        result = _format_cost(0.015, 0.075)
        assert "$" in result or "0.015" in result
