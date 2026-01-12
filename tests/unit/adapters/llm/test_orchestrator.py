"""Tests for unified LLM orchestrator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rice_factor.adapters.llm.cli.base import CLITaskResult
from rice_factor.adapters.llm.orchestrator import (
    API_PREFERRED_TASKS,
    CLI_PREFERRED_TASKS,
    NoAgentAvailableError,
    OrchestrationMode,
    OrchestrationResult,
    UnifiedOrchestrator,
    create_orchestrator_from_config,
)


class MockCLIAgent:
    """Mock CLI agent for testing."""

    def __init__(
        self,
        name: str = "mock",
        priority: int = 10,
        available: bool = True,
        success: bool = True,
        capabilities: list[str] | None = None,
    ) -> None:
        self._name = name
        self._priority = priority
        self._available = available
        self._success = success
        self._capabilities = capabilities or ["code_generation"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def command(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    async def is_available(self) -> bool:
        return self._available

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float = 300.0,
    ) -> CLITaskResult:
        return CLITaskResult(
            success=self._success,
            output="Task completed" if self._success else "",
            error=None if self._success else "Task failed",
            files_modified=["test.py"] if self._success else [],
            agent_name=self._name,
            duration_seconds=1.5,
        )

    def get_capabilities(self) -> list[str]:
        return self._capabilities


class TestOrchestrationMode:
    """Tests for OrchestrationMode enum."""

    def test_mode_values(self) -> None:
        """Test mode enum values."""
        assert OrchestrationMode.API.value == "api"
        assert OrchestrationMode.CLI.value == "cli"
        assert OrchestrationMode.AUTO.value == "auto"


class TestOrchestrationResult:
    """Tests for OrchestrationResult dataclass."""

    def test_create_api_result(self) -> None:
        """Test creating API mode result."""
        result = OrchestrationResult(
            success=True,
            mode=OrchestrationMode.API,
            response="Generated code",
            provider_name="claude",
            duration_seconds=2.5,
        )

        assert result.success is True
        assert result.mode == OrchestrationMode.API
        assert result.response == "Generated code"
        assert result.cli_result is None

    def test_create_cli_result(self) -> None:
        """Test creating CLI mode result."""
        cli_result = CLITaskResult(
            success=True,
            output="Done",
            agent_name="aider",
        )
        result = OrchestrationResult(
            success=True,
            mode=OrchestrationMode.CLI,
            cli_result=cli_result,
            provider_name="aider",
        )

        assert result.success is True
        assert result.mode == OrchestrationMode.CLI
        assert result.cli_result is not None
        assert result.response is None


class TestNoAgentAvailableError:
    """Tests for NoAgentAvailableError."""

    def test_error_message(self) -> None:
        """Test error message format."""
        error = NoAgentAvailableError("refactoring")

        assert "refactoring" in str(error)
        assert error.task_type == "refactoring"


class TestUnifiedOrchestrator:
    """Tests for UnifiedOrchestrator."""

    def test_init_defaults(self) -> None:
        """Test initialization with defaults."""
        orchestrator = UnifiedOrchestrator()

        assert orchestrator.api_selector is None
        assert orchestrator.cli_agents == {}
        assert orchestrator.default_mode == OrchestrationMode.AUTO
        assert orchestrator.fallback_to_cli is True
        assert orchestrator.fallback_to_api is True

    def test_from_agents_list(self) -> None:
        """Test creating from agents list."""
        agents = [
            MockCLIAgent(name="agent1", priority=10),
            MockCLIAgent(name="agent2", priority=11),
        ]

        orchestrator = UnifiedOrchestrator.from_agents_list(cli_agents=agents)

        assert "agent1" in orchestrator.cli_agents
        assert "agent2" in orchestrator.cli_agents

    def test_add_agent(self) -> None:
        """Test adding an agent."""
        orchestrator = UnifiedOrchestrator()
        agent = MockCLIAgent(name="test")

        orchestrator.add_agent(agent)

        assert "test" in orchestrator.cli_agents

    def test_remove_agent(self) -> None:
        """Test removing an agent."""
        agent = MockCLIAgent(name="test")
        orchestrator = UnifiedOrchestrator(cli_agents={"test": agent})

        result = orchestrator.remove_agent("test")

        assert result is True
        assert "test" not in orchestrator.cli_agents

    def test_remove_agent_not_found(self) -> None:
        """Test removing non-existent agent."""
        orchestrator = UnifiedOrchestrator()

        result = orchestrator.remove_agent("unknown")

        assert result is False

    def test_get_agent(self) -> None:
        """Test getting an agent."""
        agent = MockCLIAgent(name="test")
        orchestrator = UnifiedOrchestrator(cli_agents={"test": agent})

        result = orchestrator.get_agent("test")

        assert result is agent

    def test_get_agent_not_found(self) -> None:
        """Test getting non-existent agent."""
        orchestrator = UnifiedOrchestrator()

        result = orchestrator.get_agent("unknown")

        assert result is None

    def test_select_mode_cli_preferred(self) -> None:
        """Test mode selection for CLI-preferred tasks."""
        orchestrator = UnifiedOrchestrator()

        for task_type in CLI_PREFERRED_TASKS:
            mode = orchestrator._select_mode(task_type)
            assert mode == OrchestrationMode.CLI

    def test_select_mode_api_preferred(self) -> None:
        """Test mode selection for API-preferred tasks."""
        orchestrator = UnifiedOrchestrator()

        for task_type in API_PREFERRED_TASKS:
            mode = orchestrator._select_mode(task_type)
            assert mode == OrchestrationMode.API

    def test_select_mode_unknown_defaults_to_api(self) -> None:
        """Test mode selection for unknown task type."""
        orchestrator = UnifiedOrchestrator()

        mode = orchestrator._select_mode("unknown_task")

        assert mode == OrchestrationMode.API


class TestUnifiedOrchestratorExecution:
    """Tests for UnifiedOrchestrator execution methods."""

    @pytest.mark.asyncio
    async def test_execute_cli_success(self) -> None:
        """Test successful CLI execution."""
        agent = MockCLIAgent(name="test", success=True)
        orchestrator = UnifiedOrchestrator(
            cli_agents={"test": agent},
            default_mode=OrchestrationMode.CLI,
            fallback_to_api=False,
        )

        result = await orchestrator.execute(
            prompt="Test task",
            working_dir=Path("/project"),
        )

        assert result.success is True
        assert result.mode == OrchestrationMode.CLI
        assert result.provider_name == "test"
        assert result.cli_result is not None

    @pytest.mark.asyncio
    async def test_execute_cli_failure(self) -> None:
        """Test failed CLI execution."""
        agent = MockCLIAgent(name="test", success=False)
        orchestrator = UnifiedOrchestrator(
            cli_agents={"test": agent},
            default_mode=OrchestrationMode.CLI,
            fallback_to_api=False,
        )

        result = await orchestrator.execute(
            prompt="Test task",
            working_dir=Path("/project"),
        )

        assert result.success is False
        assert result.mode == OrchestrationMode.CLI

    @pytest.mark.asyncio
    async def test_execute_cli_no_agents_available(self) -> None:
        """Test CLI execution with no available agents."""
        agent = MockCLIAgent(name="test", available=False)
        orchestrator = UnifiedOrchestrator(
            cli_agents={"test": agent},
            default_mode=OrchestrationMode.CLI,
            fallback_to_api=False,
        )

        result = await orchestrator.execute(
            prompt="Test task",
            working_dir=Path("/project"),
        )

        assert result.success is False
        assert "No CLI agents available" in result.metadata["error"]

    @pytest.mark.asyncio
    async def test_execute_cli_agent_priority(self) -> None:
        """Test CLI agents are tried in priority order."""
        agent1 = MockCLIAgent(name="high", priority=5, success=True)
        agent2 = MockCLIAgent(name="low", priority=15, success=True)

        orchestrator = UnifiedOrchestrator(
            cli_agents={"low": agent2, "high": agent1},
            default_mode=OrchestrationMode.CLI,
        )

        result = await orchestrator.execute(
            prompt="Test",
            working_dir=Path("/project"),
        )

        # Should use higher priority agent (lower number)
        assert result.provider_name == "high"

    @pytest.mark.asyncio
    async def test_execute_api_no_selector(self) -> None:
        """Test API execution without selector falls back to CLI."""
        agent = MockCLIAgent(name="test", success=True)
        orchestrator = UnifiedOrchestrator(
            api_selector=None,
            cli_agents={"test": agent},
            default_mode=OrchestrationMode.API,
            fallback_to_cli=True,
        )

        result = await orchestrator.execute(
            prompt="Test",
            working_dir=Path("/project"),
        )

        # Should fall back to CLI
        assert result.mode == OrchestrationMode.CLI
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_api_no_selector_no_fallback(self) -> None:
        """Test API execution without selector and no fallback."""
        orchestrator = UnifiedOrchestrator(
            api_selector=None,
            cli_agents={},
            default_mode=OrchestrationMode.API,
            fallback_to_cli=False,
        )

        result = await orchestrator.execute(prompt="Test")

        assert result.success is False
        assert "No API selector configured" in result.metadata["error"]

    @pytest.mark.asyncio
    async def test_execute_api_missing_args_falls_back(self) -> None:
        """Test API execution without required args falls back to CLI."""
        mock_selector = MagicMock()
        agent = MockCLIAgent(name="test", success=True)
        orchestrator = UnifiedOrchestrator(
            api_selector=mock_selector,
            cli_agents={"test": agent},
            default_mode=OrchestrationMode.API,
            fallback_to_cli=True,
        )

        result = await orchestrator.execute(
            prompt="Test",
            working_dir=Path("/project"),
            # Missing pass_type, context, schema
        )

        # Should fall back to CLI since missing required args
        assert result.mode == OrchestrationMode.CLI

    @pytest.mark.asyncio
    async def test_execute_auto_mode_selects_api(self) -> None:
        """Test auto mode selects API for simple tasks."""
        orchestrator = UnifiedOrchestrator(
            default_mode=OrchestrationMode.AUTO,
            fallback_to_cli=False,
        )

        result = await orchestrator.execute(
            prompt="Test",
            task_type="completion",  # API-preferred task
        )

        assert result.mode == OrchestrationMode.API

    @pytest.mark.asyncio
    async def test_execute_auto_mode_selects_cli(self) -> None:
        """Test auto mode selects CLI for complex tasks."""
        agent = MockCLIAgent(
            name="test",
            success=True,
            capabilities=["code_generation", "complex_refactor"],
        )
        orchestrator = UnifiedOrchestrator(
            cli_agents={"test": agent},
            default_mode=OrchestrationMode.AUTO,
        )

        result = await orchestrator.execute(
            prompt="Refactor module",
            task_type="complex_refactor",  # CLI-preferred task
            working_dir=Path("/project"),
        )

        assert result.mode == OrchestrationMode.CLI

    @pytest.mark.asyncio
    async def test_get_status(self) -> None:
        """Test getting orchestrator status."""
        agent1 = MockCLIAgent(name="available", available=True)
        agent2 = MockCLIAgent(name="unavailable", available=False)

        orchestrator = UnifiedOrchestrator(
            cli_agents={"available": agent1, "unavailable": agent2},
            default_mode=OrchestrationMode.AUTO,
        )

        status = await orchestrator.get_status()

        assert status["api_available"] is False
        assert status["cli_agents"]["available"] is True
        assert status["cli_agents"]["unavailable"] is False
        assert status["default_mode"] == "auto"

    @pytest.mark.asyncio
    async def test_get_available_agents_sorted(self) -> None:
        """Test that available agents are sorted by priority."""
        agent1 = MockCLIAgent(name="mid", priority=10, available=True)
        agent2 = MockCLIAgent(name="high", priority=5, available=True)
        agent3 = MockCLIAgent(name="low", priority=15, available=True)
        agent4 = MockCLIAgent(name="off", priority=1, available=False)

        orchestrator = UnifiedOrchestrator(
            cli_agents={"mid": agent1, "high": agent2, "low": agent3, "off": agent4}
        )

        available = await orchestrator._get_available_agents()

        assert len(available) == 3
        assert available[0].name == "high"
        assert available[1].name == "mid"
        assert available[2].name == "low"


class TestCreateOrchestratorFromConfig:
    """Tests for create_orchestrator_from_config."""

    def test_create_with_defaults(self) -> None:
        """Test creating orchestrator with default config."""
        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = lambda key, default: default

            with patch(
                "rice_factor.adapters.llm.provider_selector.create_provider_selector_from_config",
                side_effect=Exception("No config"),
            ):
                orchestrator = create_orchestrator_from_config()

                assert orchestrator.api_selector is None
                assert len(orchestrator.cli_agents) == 5  # All 5 adapters
                assert orchestrator.default_mode == OrchestrationMode.AUTO

    def test_create_with_disabled_agents(self) -> None:
        """Test creating orchestrator with some agents disabled."""

        def mock_get(key: str, default: bool) -> bool:
            if key == "cli_agents.codex.enabled":
                return False
            if key == "cli_agents.gemini_cli.enabled":
                return False
            return default

        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = mock_get

            with patch(
                "rice_factor.adapters.llm.provider_selector.create_provider_selector_from_config",
                side_effect=Exception("No config"),
            ):
                orchestrator = create_orchestrator_from_config()

                assert "codex" not in orchestrator.cli_agents
                assert "gemini_cli" not in orchestrator.cli_agents
                assert "claude_code" in orchestrator.cli_agents

    def test_create_with_custom_mode(self) -> None:
        """Test creating orchestrator with custom default mode."""

        def mock_get(key: str, default):
            if key == "orchestration.default_mode":
                return "cli"
            return default

        with patch("rice_factor.config.settings.settings") as mock_settings:
            mock_settings.get.side_effect = mock_get

            with patch(
                "rice_factor.adapters.llm.provider_selector.create_provider_selector_from_config",
                side_effect=Exception("No config"),
            ):
                orchestrator = create_orchestrator_from_config()

                assert orchestrator.default_mode == OrchestrationMode.CLI
