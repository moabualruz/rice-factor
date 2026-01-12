"""Tests for CLI agent detector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.llm.cli.detector import (
    AgentConfig,
    CLIAgentDetector,
    DEFAULT_AGENT_CONFIGS,
)


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_create_with_defaults(self) -> None:
        """Test creating config with default values."""
        config = AgentConfig(command="test")

        assert config.command == "test"
        assert config.version_flag == "--version"
        assert config.timeout_seconds == 5.0

    def test_create_with_custom_values(self) -> None:
        """Test creating config with custom values."""
        config = AgentConfig(
            command="custom",
            version_flag="-v",
            timeout_seconds=10.0,
        )

        assert config.command == "custom"
        assert config.version_flag == "-v"
        assert config.timeout_seconds == 10.0


class TestDefaultAgentConfigs:
    """Tests for default agent configurations."""

    def test_claude_code_config_exists(self) -> None:
        """Test claude_code is in defaults."""
        assert "claude_code" in DEFAULT_AGENT_CONFIGS
        assert DEFAULT_AGENT_CONFIGS["claude_code"].command == "claude"

    def test_codex_config_exists(self) -> None:
        """Test codex is in defaults."""
        assert "codex" in DEFAULT_AGENT_CONFIGS
        assert DEFAULT_AGENT_CONFIGS["codex"].command == "codex"

    def test_aider_config_exists(self) -> None:
        """Test aider is in defaults."""
        assert "aider" in DEFAULT_AGENT_CONFIGS
        assert DEFAULT_AGENT_CONFIGS["aider"].command == "aider"


class TestCLIAgentDetector:
    """Tests for CLIAgentDetector."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default configs."""
        detector = CLIAgentDetector()

        assert "claude_code" in detector.configs
        assert "codex" in detector.configs
        assert "aider" in detector.configs

    def test_init_with_custom_configs(self) -> None:
        """Test initialization with custom configs."""
        custom = {"custom": AgentConfig(command="custom-tool")}
        detector = CLIAgentDetector(configs=custom)

        assert "custom" in detector.configs
        assert "claude_code" not in detector.configs

    @patch("shutil.which")
    def test_detect_all_none_available(self, mock_which: MagicMock) -> None:
        """Test detect_all when no agents are available."""
        mock_which.return_value = None

        detector = CLIAgentDetector(
            configs={"test": AgentConfig(command="test-cmd")}
        )
        agents = detector.detect_all()

        assert len(agents) == 1
        assert agents[0].name == "test"
        assert agents[0].available is False

    @patch("shutil.which")
    def test_detect_all_some_available(self, mock_which: MagicMock) -> None:
        """Test detect_all when some agents are available."""
        mock_which.side_effect = lambda cmd: "/usr/bin/cmd1" if cmd == "cmd1" else None

        detector = CLIAgentDetector(
            configs={
                "agent1": AgentConfig(command="cmd1"),
                "agent2": AgentConfig(command="cmd2"),
            }
        )
        agents = detector.detect_all()

        available = [a for a in agents if a.available]
        unavailable = [a for a in agents if not a.available]

        assert len(available) == 1
        assert len(unavailable) == 1
        assert available[0].name == "agent1"
        assert unavailable[0].name == "agent2"

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_detect_agent_with_version(
        self, mock_which: MagicMock, mock_run: MagicMock
    ) -> None:
        """Test detecting agent with version info."""
        mock_which.return_value = "/usr/bin/test"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="test version 1.2.3\n",
        )

        detector = CLIAgentDetector(
            configs={"test": AgentConfig(command="test")}
        )
        agent = detector.detect_agent("test", AgentConfig(command="test"))

        assert agent.available is True
        assert agent.version == "test version 1.2.3"
        assert agent.path == "/usr/bin/test"

    @patch("shutil.which")
    def test_detect_available_only(self, mock_which: MagicMock) -> None:
        """Test detect_available returns only available agents."""
        mock_which.side_effect = lambda cmd: "/bin/" + cmd if cmd == "cmd1" else None

        detector = CLIAgentDetector(
            configs={
                "agent1": AgentConfig(command="cmd1"),
                "agent2": AgentConfig(command="cmd2"),
            }
        )
        available = detector.detect_available()

        assert len(available) == 1
        assert available[0].name == "agent1"

    @patch("shutil.which")
    def test_is_agent_available_true(self, mock_which: MagicMock) -> None:
        """Test is_agent_available returns True when installed."""
        mock_which.return_value = "/usr/bin/test"

        detector = CLIAgentDetector(
            configs={"test": AgentConfig(command="test")}
        )

        assert detector.is_agent_available("test") is True

    @patch("shutil.which")
    def test_is_agent_available_false(self, mock_which: MagicMock) -> None:
        """Test is_agent_available returns False when not installed."""
        mock_which.return_value = None

        detector = CLIAgentDetector(
            configs={"test": AgentConfig(command="test")}
        )

        assert detector.is_agent_available("test") is False

    def test_is_agent_available_unknown(self) -> None:
        """Test is_agent_available returns False for unknown agent."""
        detector = CLIAgentDetector(configs={})

        assert detector.is_agent_available("unknown") is False

    def test_add_agent_config(self) -> None:
        """Test adding an agent configuration."""
        detector = CLIAgentDetector(configs={})
        detector.add_agent_config("new", AgentConfig(command="new-cmd"))

        assert "new" in detector.configs
        assert detector.configs["new"].command == "new-cmd"

    def test_remove_agent_config(self) -> None:
        """Test removing an agent configuration."""
        detector = CLIAgentDetector(
            configs={"test": AgentConfig(command="test")}
        )

        result = detector.remove_agent_config("test")

        assert result is True
        assert "test" not in detector.configs

    def test_remove_agent_config_not_found(self) -> None:
        """Test removing non-existent agent configuration."""
        detector = CLIAgentDetector(configs={})

        result = detector.remove_agent_config("unknown")

        assert result is False

    @patch("shutil.which")
    def test_to_dict(self, mock_which: MagicMock) -> None:
        """Test exporting detection results as dictionary."""
        mock_which.return_value = "/usr/bin/test"

        detector = CLIAgentDetector(
            configs={"test": AgentConfig(command="test")}
        )
        result = detector.to_dict()

        assert "test" in result
        assert result["test"]["command"] == "test"
        assert result["test"]["available"] is True
        assert result["test"]["path"] == "/usr/bin/test"

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_get_version_timeout(
        self, mock_which: MagicMock, mock_run: MagicMock
    ) -> None:
        """Test version retrieval handles timeout."""
        import subprocess

        mock_which.return_value = "/usr/bin/test"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)

        detector = CLIAgentDetector(
            configs={"test": AgentConfig(command="test")}
        )
        agent = detector.detect_agent("test", AgentConfig(command="test"))

        assert agent.available is True
        assert agent.version is None

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_get_version_error(
        self, mock_which: MagicMock, mock_run: MagicMock
    ) -> None:
        """Test version retrieval handles errors."""
        mock_which.return_value = "/usr/bin/test"
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        detector = CLIAgentDetector(
            configs={"test": AgentConfig(command="test")}
        )
        agent = detector.detect_agent("test", AgentConfig(command="test"))

        assert agent.available is True
        assert agent.version is None
