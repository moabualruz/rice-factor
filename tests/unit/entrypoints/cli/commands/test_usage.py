"""Unit tests for usage CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestUsageCommandHelp:
    """Tests for usage command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["usage", "--help"])
        assert result.exit_code == 0
        assert "usage" in result.stdout.lower()

    def test_help_shows_subcommands(self) -> None:
        """--help should list subcommands."""
        result = runner.invoke(app, ["usage", "--help"])
        assert result.exit_code == 0
        assert "show" in result.stdout
        assert "export" in result.stdout
        assert "clear" in result.stdout


class TestUsageShowCommand:
    """Tests for usage show command."""

    def test_show_help_shows_options(self) -> None:
        """show --help should show options."""
        result = runner.invoke(app, ["usage", "show", "--help"])
        assert result.exit_code == 0
        assert "--provider" in result.stdout
        assert "--json" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_show_basic(self, mock_get_tracker: MagicMock) -> None:
        """Test basic show output."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker

        mock_stats = MagicMock(
            total_requests=100,
            successful_requests=95,
            total_input_tokens=50000,
            total_output_tokens=25000,
            total_cost_usd=5.50,
            avg_latency_ms=250.0,
        )
        mock_tracker.by_provider.return_value = {"anthropic": mock_stats}
        mock_tracker.by_model.return_value = {}
        mock_tracker.total_cost.return_value = 5.50
        mock_tracker.total_tokens.return_value = (50000, 25000)

        result = runner.invoke(app, ["usage", "show"])

        assert result.exit_code == 0
        mock_tracker.by_provider.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_show_json_output(self, mock_get_tracker: MagicMock) -> None:
        """Test show with --json output."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker

        mock_tracker.export_json.return_value = {
            "providers": {"anthropic": {"total_requests": 100}},
            "total_cost": 5.50,
        }

        result = runner.invoke(app, ["usage", "show", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "providers" in data
        mock_tracker.export_json.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_show_no_usage(self, mock_get_tracker: MagicMock) -> None:
        """Test show when no usage data."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker
        mock_tracker.by_provider.return_value = {}

        result = runner.invoke(app, ["usage", "show"])

        assert result.exit_code == 0
        assert "no usage" in result.stdout.lower()


class TestUsageExportCommand:
    """Tests for usage export command."""

    def test_export_help_shows_options(self) -> None:
        """export --help should show options."""
        result = runner.invoke(app, ["usage", "export", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.stdout
        assert "--output" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_export_json(self, mock_get_tracker: MagicMock) -> None:
        """Test export with json format."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker

        mock_tracker.export_json.return_value = {
            "providers": {"openai": {"total_requests": 50}},
            "total_cost": 2.75,
        }

        result = runner.invoke(app, ["usage", "export", "--format", "json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "providers" in data

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_export_prometheus(self, mock_get_tracker: MagicMock) -> None:
        """Test export with prometheus format."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker

        mock_tracker.export_prometheus.return_value = (
            "# HELP rice_factor_llm_requests_total Total LLM requests\n"
            "rice_factor_llm_requests_total{provider=\"anthropic\"} 100\n"
        )

        result = runner.invoke(app, ["usage", "export", "--format", "prometheus"])

        assert result.exit_code == 0
        assert "rice_factor" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_export_to_file(self, mock_get_tracker: MagicMock, tmp_path) -> None:
        """Test export with --output to file."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker

        mock_tracker.export_json.return_value = {"providers": {}, "total_cost": 0}

        output_file = tmp_path / "usage.json"
        result = runner.invoke(
            app, ["usage", "export", "--format", "json", "--output", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "providers" in data


class TestUsageClearCommand:
    """Tests for usage clear command."""

    def test_clear_help_shows_options(self) -> None:
        """clear --help should show options."""
        result = runner.invoke(app, ["usage", "clear", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_clear_no_data(self, mock_get_tracker: MagicMock) -> None:
        """Test clear when no data to clear."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker
        mock_tracker.get_records.return_value = []

        result = runner.invoke(app, ["usage", "clear"])

        assert result.exit_code == 0
        assert "no usage data" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_clear_with_force(self, mock_get_tracker: MagicMock) -> None:
        """Test clear with --force flag."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker
        mock_tracker.get_records.return_value = [MagicMock(), MagicMock()]
        mock_tracker.clear.return_value = 2

        result = runner.invoke(app, ["usage", "clear", "--force"])

        assert result.exit_code == 0
        mock_tracker.clear.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.usage.get_usage_tracker")
    def test_clear_requires_confirmation(self, mock_get_tracker: MagicMock) -> None:
        """Test clear requires --force or confirmation."""
        mock_tracker = MagicMock()
        mock_get_tracker.return_value = mock_tracker
        mock_tracker.get_records.return_value = [MagicMock()]

        # Without --force, should prompt or exit
        result = runner.invoke(app, ["usage", "clear"], input="n\n")

        # Should abort when user says no
        assert "cancelled" in result.stdout.lower()


class TestUsageHelperFunctions:
    """Tests for usage helper functions."""

    def test_format_tokens(self) -> None:
        """Test token formatting."""
        from rice_factor.entrypoints.cli.commands.usage import _format_tokens

        assert "50" in _format_tokens(50000)
        assert "K" in _format_tokens(50000)

    def test_format_tokens_millions(self) -> None:
        """Test token formatting for millions."""
        from rice_factor.entrypoints.cli.commands.usage import _format_tokens

        result = _format_tokens(1500000)
        assert "M" in result

    def test_format_cost(self) -> None:
        """Test cost formatting."""
        from rice_factor.entrypoints.cli.commands.usage import _format_cost

        result = _format_cost(5.50)
        assert "$" in result or "5.50" in result

    def test_format_cost_zero(self) -> None:
        """Test zero cost formatting."""
        from rice_factor.entrypoints.cli.commands.usage import _format_cost

        result = _format_cost(0)
        assert "$0" in result

    def test_format_latency(self) -> None:
        """Test latency formatting."""
        from rice_factor.entrypoints.cli.commands.usage import _format_latency

        result = _format_latency(250.0)
        assert "250" in result or "ms" in result.lower()

    def test_format_latency_seconds(self) -> None:
        """Test latency formatting for seconds."""
        from rice_factor.entrypoints.cli.commands.usage import _format_latency

        result = _format_latency(2500.0)
        assert "s" in result
