"""Unit tests for agents CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.adapters.llm.cli.detector import DetectedAgent
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestAgentsCommandHelp:
    """Tests for agents command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["agents", "--help"])
        assert result.exit_code == 0
        assert "agent" in result.stdout.lower()

    def test_help_shows_subcommands(self) -> None:
        """--help should list subcommands."""
        result = runner.invoke(app, ["agents", "--help"])
        assert result.exit_code == 0
        assert "detect" in result.stdout
        assert "list" in result.stdout
        assert "check" in result.stdout


class TestAgentsDetectCommand:
    """Tests for agents detect command."""

    def test_detect_help_shows_options(self) -> None:
        """detect --help should show options."""
        result = runner.invoke(app, ["agents", "detect", "--help"])
        assert result.exit_code == 0
        assert "--json" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_detect_basic(self, mock_detector_class: MagicMock) -> None:
        """Test basic detect output."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_agent = DetectedAgent(
            name="Claude Code",
            command="claude",
            available=True,
            version="1.0.0",
            path="/usr/bin/claude",
        )
        mock_detector.detect_all.return_value = [mock_agent]

        result = runner.invoke(app, ["agents", "detect"])

        assert result.exit_code == 0
        mock_detector.detect_all.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_detect_json_output(self, mock_detector_class: MagicMock) -> None:
        """Test detect with --json output."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_agent = DetectedAgent(
            name="Aider",
            command="aider",
            available=True,
            version="0.40.0",
            path="/usr/bin/aider",
        )
        mock_detector.detect_all.return_value = [mock_agent]
        mock_detector.to_dict.return_value = {
            "agents": [
                {
                    "name": "Aider",
                    "command": "aider",
                    "available": True,
                    "version": "0.40.0",
                    "path": "/usr/bin/aider",
                }
            ]
        }

        result = runner.invoke(app, ["agents", "detect", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "agents" in data
        assert "summary" in data

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_detect_no_agents(self, mock_detector_class: MagicMock) -> None:
        """Test detect when no agents found."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        mock_detector.detect_all.return_value = []

        result = runner.invoke(app, ["agents", "detect"])

        assert result.exit_code == 0
        assert "no" in result.stdout.lower()


class TestAgentsListCommand:
    """Tests for agents list command."""

    def test_list_help_shows_options(self) -> None:
        """list --help should show options."""
        result = runner.invoke(app, ["agents", "list", "--help"])
        assert result.exit_code == 0
        assert "--available" in result.stdout
        assert "--json" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_list_basic(self, mock_detector_class: MagicMock) -> None:
        """Test basic list output."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_agent = DetectedAgent(
            name="Claude Code",
            command="claude",
            available=True,
            version="1.0.0",
            path="/usr/bin/claude",
        )
        mock_detector.detect_all.return_value = [mock_agent]

        result = runner.invoke(app, ["agents", "list"])

        assert result.exit_code == 0

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_list_available_only(self, mock_detector_class: MagicMock) -> None:
        """Test list with --available filter."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        available_agent = DetectedAgent(
            name="Claude Code",
            command="claude",
            available=True,
            version="1.0.0",
            path="/usr/bin/claude",
        )
        unavailable_agent = DetectedAgent(
            name="Aider",
            command="aider",
            available=False,
            version=None,
            path=None,
        )
        mock_detector.detect_all.return_value = [available_agent, unavailable_agent]

        result = runner.invoke(app, ["agents", "list", "--available", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        # Only available agents should be shown
        assert all(a["available"] for a in data["agents"])

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_list_json_output(self, mock_detector_class: MagicMock) -> None:
        """Test list with --json output."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_agent = DetectedAgent(
            name="Aider",
            command="aider",
            available=True,
            version="0.40.0",
            path="/usr/bin/aider",
        )
        mock_detector.detect_all.return_value = [mock_agent]

        result = runner.invoke(app, ["agents", "list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "agents" in data


class TestAgentsCheckCommand:
    """Tests for agents check command."""

    def test_check_help_shows_options(self) -> None:
        """check --help should show options."""
        result = runner.invoke(app, ["agents", "check", "--help"])
        assert result.exit_code == 0

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_check_available(self, mock_detector_class: MagicMock) -> None:
        """Test check when agent is available."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_agent = DetectedAgent(
            name="Claude Code",
            command="claude",
            available=True,
            version="1.0.0",
            path="/usr/bin/claude",
        )
        mock_detector.configs = {"claude_code": MagicMock()}
        mock_detector.detect_agent.return_value = mock_agent

        result = runner.invoke(app, ["agents", "check", "claude_code"])

        assert result.exit_code == 0
        assert "available" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_check_not_available(self, mock_detector_class: MagicMock) -> None:
        """Test check when agent is not available."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        mock_agent = DetectedAgent(
            name="Aider",
            command="aider",
            available=False,
            version=None,
            path=None,
        )
        mock_detector.configs = {"aider": MagicMock()}
        mock_detector.detect_agent.return_value = mock_agent

        result = runner.invoke(app, ["agents", "check", "aider"])

        assert result.exit_code == 1
        assert "not" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.agents.CLIAgentDetector")
    def test_check_unknown_agent(self, mock_detector_class: MagicMock) -> None:
        """Test check with unknown agent ID."""
        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector
        mock_detector.configs = {}

        result = runner.invoke(app, ["agents", "check", "nonexistent"])

        assert result.exit_code == 1
        assert "unknown" in result.stdout.lower()


class TestAgentsTableCreation:
    """Tests for agents table creation."""

    def test_create_agents_table(self) -> None:
        """Test table creation with agents."""
        from rice_factor.entrypoints.cli.commands.agents import _create_agents_table

        agents = [
            DetectedAgent(
                name="Claude Code",
                command="claude",
                available=True,
                version="1.0.0",
                path="/usr/bin/claude",
            ),
            DetectedAgent(
                name="Aider",
                command="aider",
                available=False,
                version=None,
                path=None,
            ),
        ]

        table = _create_agents_table(agents)
        assert table is not None
        assert table.title == "CLI Coding Agents"

    def test_create_agents_table_long_path(self) -> None:
        """Test table creation with long path truncation."""
        from rice_factor.entrypoints.cli.commands.agents import _create_agents_table

        agents = [
            DetectedAgent(
                name="Test",
                command="test",
                available=True,
                version="1.0.0",
                path="/very/long/path/that/exceeds/forty/characters/total/length",
            ),
        ]

        table = _create_agents_table(agents)
        assert table is not None
