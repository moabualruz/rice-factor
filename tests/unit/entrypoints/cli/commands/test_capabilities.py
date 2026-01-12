"""Unit tests for capabilities CLI command."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.adapters.refactoring.capability_detector import ToolAvailability
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestCapabilitiesCommand:
    """Tests for the capabilities command."""

    @patch("rice_factor.entrypoints.cli.commands.capabilities.CapabilityDetector")
    def test_capabilities_basic(self, mock_detector_class: MagicMock) -> None:
        """Test basic capabilities output."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_detector.detect_all.return_value = {
            "rope": ToolAvailability(
                name="rope",
                available=True,
                version="1.11.0",
                languages=["python"],
                operations=["rename", "move"],
            ),
            "jscodeshift": ToolAvailability(
                name="jscodeshift",
                available=False,
                languages=["javascript", "typescript"],
                operations=["rename", "move"],
            ),
        }
        mock_detector.get_language_capabilities.return_value = []

        result = runner.invoke(app, ["capabilities"])

        assert result.exit_code == 0
        assert "rope" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.capabilities.CapabilityDetector")
    def test_capabilities_refresh(self, mock_detector_class: MagicMock) -> None:
        """Test capabilities with --refresh flag."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_detector.refresh.return_value = {}
        mock_detector.detect_all.return_value = {}
        mock_detector.get_language_capabilities.return_value = []

        result = runner.invoke(app, ["capabilities", "--refresh"])

        assert result.exit_code == 0
        mock_detector.refresh.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.capabilities.CapabilityDetector")
    def test_capabilities_tools_only(self, mock_detector_class: MagicMock) -> None:
        """Test capabilities with --tools flag."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_detector.detect_all.return_value = {
            "rope": ToolAvailability(
                name="rope",
                available=True,
                version="1.11.0",
                languages=["python"],
                operations=["rename"],
            ),
        }
        mock_detector.get_language_capabilities.return_value = []

        result = runner.invoke(app, ["capabilities", "--tools"])

        assert result.exit_code == 0
        # Should show tools table but not language table
        assert "rope" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.capabilities.CapabilityDetector")
    def test_capabilities_json_output(self, mock_detector_class: MagicMock) -> None:
        """Test capabilities with --json flag."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_detector.detect_all.return_value = {
            "rope": ToolAvailability(
                name="rope",
                available=True,
                version="1.11.0",
                languages=["python"],
                operations=["rename", "move"],
            ),
        }
        mock_detector.get_language_capabilities.return_value = []

        result = runner.invoke(app, ["capabilities", "--json"])

        assert result.exit_code == 0
        # Should be valid JSON
        import json

        output = json.loads(result.stdout)
        assert "tools" in output
        assert "languages" in output
        assert output["tools"]["rope"]["available"] is True
        assert output["tools"]["rope"]["version"] == "1.11.0"

    @patch("rice_factor.entrypoints.cli.commands.capabilities.CapabilityDetector")
    def test_capabilities_no_tools_available(self, mock_detector_class: MagicMock) -> None:
        """Test capabilities when no tools are available."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_detector.detect_all.return_value = {
            "rope": ToolAvailability(
                name="rope", available=False, languages=["python"], operations=[]
            ),
            "jscodeshift": ToolAvailability(
                name="jscodeshift", available=False, languages=["javascript"], operations=[]
            ),
        }
        mock_detector.get_language_capabilities.return_value = []

        result = runner.invoke(app, ["capabilities"])

        assert result.exit_code == 0
        assert "no refactoring tools detected" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.capabilities.CapabilityDetector")
    def test_capabilities_all_tools_available(self, mock_detector_class: MagicMock) -> None:
        """Test capabilities when all tools are available."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_detector.detect_all.return_value = {
            "rope": ToolAvailability(
                name="rope",
                available=True,
                version="1.11.0",
                languages=["python"],
                operations=["rename"],
            ),
        }
        mock_detector.get_language_capabilities.return_value = []

        result = runner.invoke(app, ["capabilities"])

        assert result.exit_code == 0
        assert "all" in result.stdout.lower() and "available" in result.stdout.lower()


class TestCapabilitiesHelperFunctions:
    """Tests for helper functions."""

    def test_format_operations_empty(self) -> None:
        """Test formatting empty operations list."""
        from rice_factor.entrypoints.cli.commands.capabilities import _format_operations

        assert _format_operations([]) == "-"

    def test_format_operations_with_values(self) -> None:
        """Test formatting operations list with values."""
        from rice_factor.entrypoints.cli.commands.capabilities import _format_operations

        result = _format_operations(["rename", "move"])
        assert "rename" in result
        assert "move" in result
