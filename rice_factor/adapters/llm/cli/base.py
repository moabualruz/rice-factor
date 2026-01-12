"""Base protocol and types for CLI coding agents.

This module defines the CLIAgentPort protocol that all CLI agent
adapters must implement, along with related data types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class CLITaskResult:
    """Result from CLI agent task execution.

    Attributes:
        success: Whether the task completed successfully.
        output: Standard output from the CLI tool.
        error: Error message or stderr output if any.
        files_modified: List of file paths modified by the agent.
        files_created: List of file paths created by the agent.
        duration_seconds: Total execution time in seconds.
        agent_name: Name of the agent that executed the task.
        exit_code: Process exit code.
        metadata: Additional metadata from the agent output.
    """

    success: bool
    output: str
    error: str | None = None
    files_modified: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    agent_name: str = ""
    exit_code: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class DetectedAgent:
    """Information about a detected CLI agent.

    Attributes:
        name: Internal agent identifier (e.g., 'claude_code').
        command: CLI command name (e.g., 'claude').
        version: Version string if available.
        available: Whether the agent is installed and accessible.
        path: Full path to the executable if available.
    """

    name: str
    command: str
    version: str | None = None
    available: bool = False
    path: str | None = None


@runtime_checkable
class CLIAgentPort(Protocol):
    """Protocol for CLI-based coding agents.

    CLI agents are subprocess-based tools that can perform complex
    coding tasks like multi-file refactoring, test generation, and
    code review. They typically run in non-interactive modes and
    return structured output.

    Example:
        >>> adapter = ClaudeCodeAdapter()
        >>> if await adapter.is_available():
        ...     result = await adapter.execute_task(
        ...         "Add unit tests for auth module",
        ...         working_dir=Path("/project"),
        ...     )
        ...     print(f"Modified: {result.files_modified}")
    """

    @property
    def name(self) -> str:
        """Agent identifier (e.g., 'claude_code', 'codex', 'aider').

        Returns:
            Unique string identifier for this agent.
        """
        ...

    @property
    def command(self) -> str:
        """CLI command to invoke (e.g., 'claude', 'codex').

        Returns:
            The base command name.
        """
        ...

    @property
    def priority(self) -> int:
        """Priority for agent selection (lower = higher priority).

        CLI agents typically have priority 10-19 (after API providers 1-9).

        Returns:
            Priority value for fallback ordering.
        """
        ...

    async def is_available(self) -> bool:
        """Check if the CLI tool is installed and accessible.

        Returns:
            True if the command exists and can be executed.
        """
        ...

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float = 300.0,
    ) -> CLITaskResult:
        """Execute a coding task and return results.

        Args:
            prompt: Task description or instruction for the agent.
            working_dir: Directory to run the agent in.
            timeout_seconds: Maximum execution time before timeout.

        Returns:
            CLITaskResult with execution details and modified files.
        """
        ...

    def get_capabilities(self) -> list[str]:
        """Return list of supported capabilities.

        Common capabilities include:
        - code_generation: Generate new code
        - refactoring: Modify existing code structure
        - testing: Generate or run tests
        - git_integration: Git operations
        - multi_file: Handle changes across multiple files
        - code_review: Review and suggest improvements

        Returns:
            List of capability strings this agent supports.
        """
        ...
