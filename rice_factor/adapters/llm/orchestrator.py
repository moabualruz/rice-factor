"""Unified LLM orchestrator for API and CLI modes.

This module provides the UnifiedOrchestrator that coordinates between
API-based LLM providers and CLI-based coding agents, selecting the
appropriate mode based on task type and availability.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rice_factor.adapters.llm.cli.base import CLIAgentPort, CLITaskResult
    from rice_factor.adapters.llm.provider_selector import (
        ProviderSelector,
        SelectionResult,
    )


class OrchestrationMode(Enum):
    """Mode for task execution."""

    API = "api"  # Use REST API providers only
    CLI = "cli"  # Use CLI agents only
    AUTO = "auto"  # Select based on task type


# Tasks that benefit from CLI agents (complex, multi-file, interactive)
CLI_PREFERRED_TASKS: set[str] = {
    "complex_refactor",
    "multi_file_change",
    "testing",
    "debugging",
    "code_review",
    "git_integration",
}

# Tasks that work well with API providers (simple, single-file)
API_PREFERRED_TASKS: set[str] = {
    "code_generation",
    "completion",
    "docstring",
    "explanation",
    "simple_fix",
}


class NoAgentAvailableError(Exception):
    """Raised when no CLI agent is available for a task."""

    def __init__(self, task_type: str) -> None:
        self.task_type = task_type
        super().__init__(f"No CLI agent available for task type: {task_type}")


@dataclass
class OrchestrationResult:
    """Result from orchestrated execution.

    Attributes:
        success: Whether execution succeeded.
        mode: The mode that was used (API or CLI).
        response: Text response (for API mode).
        cli_result: CLITaskResult (for CLI mode).
        provider_name: Name of provider/agent used.
        duration_seconds: Total execution time.
        metadata: Additional execution metadata.
    """

    success: bool
    mode: OrchestrationMode
    response: str | None = None
    cli_result: CLITaskResult | None = None
    provider_name: str = ""
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedOrchestrator:
    """Orchestrates between API providers and CLI agents.

    The orchestrator provides a unified interface for executing LLM tasks,
    automatically selecting between API providers and CLI agents based on
    task type, availability, and configuration.

    Example:
        >>> orchestrator = UnifiedOrchestrator(
        ...     api_selector=provider_selector,
        ...     cli_agents=[claude_code, aider],
        ... )
        >>> result = await orchestrator.execute(
        ...     prompt="Add unit tests for auth module",
        ...     task_type="testing",
        ...     working_dir=Path("/project"),
        ... )

    Attributes:
        api_selector: Provider selector for API mode.
        cli_agents: Dict of CLI agents by name.
        default_mode: Default orchestration mode.
        fallback_to_cli: Whether to fall back to CLI on API failure.
        fallback_to_api: Whether to fall back to API on CLI failure.
    """

    api_selector: ProviderSelector | None = None
    cli_agents: dict[str, CLIAgentPort] = field(default_factory=dict)
    default_mode: OrchestrationMode = OrchestrationMode.AUTO
    fallback_to_cli: bool = True
    fallback_to_api: bool = True

    @classmethod
    def from_agents_list(
        cls,
        api_selector: ProviderSelector | None = None,
        cli_agents: list[CLIAgentPort] | None = None,
        default_mode: OrchestrationMode = OrchestrationMode.AUTO,
        fallback_to_cli: bool = True,
        fallback_to_api: bool = True,
    ) -> UnifiedOrchestrator:
        """Create orchestrator from a list of CLI agents.

        Args:
            api_selector: Provider selector for API mode.
            cli_agents: List of CLI agents.
            default_mode: Default orchestration mode.
            fallback_to_cli: Fall back to CLI on API failure.
            fallback_to_api: Fall back to API on CLI failure.

        Returns:
            Configured UnifiedOrchestrator.
        """
        agents_dict = {a.name: a for a in (cli_agents or [])}
        return cls(
            api_selector=api_selector,
            cli_agents=agents_dict,
            default_mode=default_mode,
            fallback_to_cli=fallback_to_cli,
            fallback_to_api=fallback_to_api,
        )

    async def execute(
        self,
        prompt: str,
        task_type: str = "code_generation",
        mode: OrchestrationMode | None = None,
        working_dir: Path | None = None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """Execute a task using appropriate mode.

        Args:
            prompt: Task description or instruction.
            task_type: Type of task for mode selection.
            mode: Override mode (uses default if None).
            working_dir: Working directory for CLI agents.
            **kwargs: Additional arguments for providers/agents.

        Returns:
            OrchestrationResult with execution details.
        """
        mode = mode or self.default_mode

        if mode == OrchestrationMode.AUTO:
            mode = self._select_mode(task_type)

        if mode == OrchestrationMode.API:
            return await self._execute_api(prompt, task_type, working_dir, **kwargs)
        else:
            return await self._execute_cli(prompt, task_type, working_dir, **kwargs)

    async def _execute_api(
        self,
        prompt: str,
        task_type: str,
        working_dir: Path | None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """Execute via API provider with optional CLI fallback.

        Note: The orchestrator's API mode requires explicit pass_type, context,
        and schema in kwargs to use the ProviderSelector. For simple prompts,
        consider using CLI mode or calling adapters directly.

        Args:
            prompt: Task prompt.
            task_type: Task type.
            working_dir: Working directory for fallback.
            **kwargs: Must include pass_type, context, schema for API mode.

        Returns:
            OrchestrationResult.
        """
        if not self.api_selector:
            if self.fallback_to_cli:
                return await self._execute_cli(prompt, task_type, working_dir, **kwargs)
            return OrchestrationResult(
                success=False,
                mode=OrchestrationMode.API,
                metadata={"error": "No API selector configured"},
            )

        # Check for required compiler arguments
        pass_type = kwargs.get("pass_type")
        context = kwargs.get("context")
        schema = kwargs.get("schema")

        if not all([pass_type, context, schema]):
            # Missing compiler args - fall back to CLI or error
            if self.fallback_to_cli:
                return await self._execute_cli(prompt, task_type, working_dir, **kwargs)
            return OrchestrationResult(
                success=False,
                mode=OrchestrationMode.API,
                metadata={
                    "error": "API mode requires pass_type, context, and schema"
                },
            )

        try:
            # Type narrowing already done by all() check above
            result: SelectionResult = await self.api_selector.generate_async(
                pass_type=pass_type,  # type: ignore[arg-type]
                context=context,  # type: ignore[arg-type]
                schema=schema,  # type: ignore[arg-type]
            )

            # CompilerResult contains the artifact data
            response_text = str(result.result) if result.result else None

            return OrchestrationResult(
                success=True,
                mode=OrchestrationMode.API,
                response=response_text,
                provider_name=result.provider_name,
                duration_seconds=0.0,  # Not tracked in SelectionResult
                metadata={"attempts": result.attempts},
            )

        except Exception as e:
            if self.fallback_to_cli and working_dir:
                return await self._execute_cli(prompt, task_type, working_dir, **kwargs)

            return OrchestrationResult(
                success=False,
                mode=OrchestrationMode.API,
                metadata={"error": str(e)},
            )

    async def _execute_cli(
        self,
        prompt: str,
        task_type: str,
        working_dir: Path | None,
        **kwargs: Any,
    ) -> OrchestrationResult:
        """Execute via CLI agent with optional API fallback.

        Args:
            prompt: Task prompt.
            task_type: Task type.
            working_dir: Working directory.
            **kwargs: Additional arguments.

        Returns:
            OrchestrationResult.
        """
        if not working_dir:
            working_dir = Path.cwd()

        # Get available agents sorted by priority
        available_agents = await self._get_available_agents()

        if not available_agents:
            if self.fallback_to_api:
                return await self._execute_api(prompt, task_type, working_dir, **kwargs)
            return OrchestrationResult(
                success=False,
                mode=OrchestrationMode.CLI,
                metadata={"error": "No CLI agents available"},
            )

        # Try agents in priority order
        errors: list[str] = []
        for agent in available_agents:
            # Check if agent supports the task type
            if task_type not in agent.get_capabilities() and task_type not in {
                "code_generation"
            }:
                continue

            try:
                timeout = kwargs.pop("timeout_seconds", None)
                cli_result: CLITaskResult = await agent.execute_task(
                    prompt=prompt,
                    working_dir=working_dir,
                    timeout_seconds=timeout or 300.0,
                )

                if cli_result.success:
                    return OrchestrationResult(
                        success=True,
                        mode=OrchestrationMode.CLI,
                        cli_result=cli_result,
                        provider_name=agent.name,
                        duration_seconds=cli_result.duration_seconds,
                    )
                else:
                    errors.append(f"{agent.name}: {cli_result.error}")

            except Exception as e:
                errors.append(f"{agent.name}: {type(e).__name__}: {e}")

        # All agents failed
        if self.fallback_to_api:
            return await self._execute_api(prompt, task_type, working_dir, **kwargs)

        return OrchestrationResult(
            success=False,
            mode=OrchestrationMode.CLI,
            metadata={"errors": errors},
        )

    async def _get_available_agents(self) -> list[CLIAgentPort]:
        """Get available CLI agents sorted by priority.

        Returns:
            List of available agents.
        """
        available: list[CLIAgentPort] = []

        for agent in self.cli_agents.values():
            if await agent.is_available():
                available.append(agent)

        # Sort by priority (lower = higher priority)
        return sorted(available, key=lambda a: a.priority)

    def _select_mode(self, task_type: str) -> OrchestrationMode:
        """Select mode based on task type.

        Args:
            task_type: Type of task.

        Returns:
            Selected orchestration mode.
        """
        if task_type in CLI_PREFERRED_TASKS:
            return OrchestrationMode.CLI
        if task_type in API_PREFERRED_TASKS:
            return OrchestrationMode.API
        # Default to API for unknown task types
        return OrchestrationMode.API

    def add_agent(self, agent: CLIAgentPort) -> None:
        """Add a CLI agent.

        Args:
            agent: CLI agent to add.
        """
        self.cli_agents[agent.name] = agent

    def remove_agent(self, name: str) -> bool:
        """Remove a CLI agent.

        Args:
            name: Agent name.

        Returns:
            True if agent was found and removed.
        """
        if name in self.cli_agents:
            del self.cli_agents[name]
            return True
        return False

    def get_agent(self, name: str) -> CLIAgentPort | None:
        """Get a CLI agent by name.

        Args:
            name: Agent name.

        Returns:
            Agent if found, None otherwise.
        """
        return self.cli_agents.get(name)

    async def get_status(self) -> dict[str, Any]:
        """Get orchestrator status.

        Returns:
            Dict with status information.
        """
        api_available = self.api_selector is not None

        cli_status: dict[str, bool] = {}
        for name, agent in self.cli_agents.items():
            cli_status[name] = await agent.is_available()

        return {
            "api_available": api_available,
            "cli_agents": cli_status,
            "default_mode": self.default_mode.value,
            "fallback_to_cli": self.fallback_to_cli,
            "fallback_to_api": self.fallback_to_api,
        }


def create_orchestrator_from_config() -> UnifiedOrchestrator:
    """Create a UnifiedOrchestrator from application configuration.

    Returns:
        Configured UnifiedOrchestrator instance.
    """
    from rice_factor.adapters.llm.cli import (
        create_aider_adapter_from_config,
        create_claude_code_adapter_from_config,
        create_codex_adapter_from_config,
        create_gemini_cli_adapter_from_config,
        create_qwen_code_adapter_from_config,
    )
    from rice_factor.adapters.llm.provider_selector import (
        create_provider_selector_from_config,
    )
    from rice_factor.config.settings import settings

    # Create API selector
    api_selector = None
    with contextlib.suppress(Exception):
        api_selector = create_provider_selector_from_config()

    # Create CLI agents
    cli_agents: list[Any] = []

    if settings.get("cli_agents.claude_code.enabled", True):
        cli_agents.append(create_claude_code_adapter_from_config())

    if settings.get("cli_agents.codex.enabled", True):
        cli_agents.append(create_codex_adapter_from_config())

    if settings.get("cli_agents.gemini_cli.enabled", True):
        cli_agents.append(create_gemini_cli_adapter_from_config())

    if settings.get("cli_agents.qwen_code.enabled", True):
        cli_agents.append(create_qwen_code_adapter_from_config())

    if settings.get("cli_agents.aider.enabled", True):
        cli_agents.append(create_aider_adapter_from_config())

    # Get mode from config
    mode_str = settings.get("orchestration.default_mode", "auto").lower()
    mode_map = {
        "api": OrchestrationMode.API,
        "cli": OrchestrationMode.CLI,
        "auto": OrchestrationMode.AUTO,
    }
    default_mode = mode_map.get(mode_str, OrchestrationMode.AUTO)

    return UnifiedOrchestrator.from_agents_list(
        api_selector=api_selector,
        cli_agents=cli_agents,
        default_mode=default_mode,
        fallback_to_cli=settings.get("orchestration.fallback_to_cli", True),
        fallback_to_api=settings.get("orchestration.fallback_to_api", True),
    )
