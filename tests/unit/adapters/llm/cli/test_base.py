"""Tests for CLI agent base protocol and types."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from rice_factor.adapters.llm.cli.base import (
    CLIAgentPort,
    CLITaskResult,
    DetectedAgent,
)


class TestCLITaskResult:
    """Tests for CLITaskResult dataclass."""

    def test_create_success_result(self) -> None:
        """Test creating a successful result."""
        result = CLITaskResult(
            success=True,
            output="Task completed successfully",
            agent_name="claude_code",
            duration_seconds=5.5,
            files_modified=["src/main.py"],
            files_created=["src/utils.py"],
        )

        assert result.success is True
        assert result.output == "Task completed successfully"
        assert result.agent_name == "claude_code"
        assert result.duration_seconds == 5.5
        assert result.files_modified == ["src/main.py"]
        assert result.files_created == ["src/utils.py"]
        assert result.error is None
        assert result.exit_code == 0

    def test_create_failure_result(self) -> None:
        """Test creating a failed result."""
        result = CLITaskResult(
            success=False,
            output="",
            error="Command failed: timeout",
            agent_name="aider",
            exit_code=1,
        )

        assert result.success is False
        assert result.output == ""
        assert result.error == "Command failed: timeout"
        assert result.exit_code == 1

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        result = CLITaskResult(
            success=True,
            output="output",
        )

        assert result.error is None
        assert result.files_modified == []
        assert result.files_created == []
        assert result.duration_seconds == 0.0
        assert result.agent_name == ""
        assert result.exit_code == 0
        assert result.metadata == {}

    def test_metadata_field(self) -> None:
        """Test metadata dictionary."""
        result = CLITaskResult(
            success=True,
            output="done",
            metadata={"tokens_used": "1500", "model": "claude-sonnet"},
        )

        assert result.metadata["tokens_used"] == "1500"
        assert result.metadata["model"] == "claude-sonnet"


class TestDetectedAgent:
    """Tests for DetectedAgent dataclass."""

    def test_create_available_agent(self) -> None:
        """Test creating an available agent."""
        agent = DetectedAgent(
            name="claude_code",
            command="claude",
            version="1.2.3",
            available=True,
            path="/usr/local/bin/claude",
        )

        assert agent.name == "claude_code"
        assert agent.command == "claude"
        assert agent.version == "1.2.3"
        assert agent.available is True
        assert agent.path == "/usr/local/bin/claude"

    def test_create_unavailable_agent(self) -> None:
        """Test creating an unavailable agent."""
        agent = DetectedAgent(
            name="codex",
            command="codex",
            available=False,
        )

        assert agent.name == "codex"
        assert agent.command == "codex"
        assert agent.version is None
        assert agent.available is False
        assert agent.path is None

    def test_default_values(self) -> None:
        """Test default values."""
        agent = DetectedAgent(
            name="test",
            command="test",
        )

        assert agent.version is None
        assert agent.available is False
        assert agent.path is None


class TestCLIAgentPortProtocol:
    """Tests for CLIAgentPort protocol verification."""

    def test_protocol_is_runtime_checkable(self) -> None:
        """Test that CLIAgentPort is runtime checkable."""
        # Create a mock class that implements the protocol
        class MockAgent:
            @property
            def name(self) -> str:
                return "mock"

            @property
            def command(self) -> str:
                return "mock"

            @property
            def priority(self) -> int:
                return 10

            async def is_available(self) -> bool:
                return True

            async def execute_task(self, prompt, working_dir, timeout_seconds=300.0):
                return CLITaskResult(success=True, output="done")

            def get_capabilities(self) -> list[str]:
                return ["code_generation"]

        agent = MockAgent()
        assert isinstance(agent, CLIAgentPort)

    def test_missing_method_fails_protocol(self) -> None:
        """Test that missing methods fail protocol check."""

        class IncompleteAgent:
            @property
            def name(self) -> str:
                return "incomplete"

        agent = IncompleteAgent()
        assert not isinstance(agent, CLIAgentPort)
