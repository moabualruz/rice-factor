"""Claude Code CLI adapter.

This module provides an adapter for the Claude Code CLI tool
(https://github.com/anthropics/claude-code), allowing integration
with the rice-factor orchestration layer.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rice_factor.adapters.llm.cli.base import CLITaskResult

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ClaudeCodeAdapter:
    """Adapter for Claude Code CLI (anthropics/claude-code).

    Claude Code is an agentic coding tool that can perform complex
    multi-file operations. This adapter wraps it for non-interactive
    execution with structured JSON output.

    Example:
        >>> adapter = ClaudeCodeAdapter()
        >>> if await adapter.is_available():
        ...     result = await adapter.execute_task(
        ...         "Add error handling to auth module",
        ...         working_dir=Path("/project"),
        ...     )
        ...     print(f"Success: {result.success}")

    Attributes:
        command: CLI command name (default: 'claude').
        default_args: Default arguments for non-interactive mode.
        default_timeout: Default timeout in seconds.
        model: Model to use (optional, uses CLI default if None).
    """

    command: str = "claude"
    default_args: list[str] = field(
        default_factory=lambda: ["--print", "--output-format", "json"]
    )
    default_timeout: float = 300.0
    model: str | None = None
    _priority: int = 10

    @property
    def name(self) -> str:
        """Agent identifier."""
        return "claude_code"

    @property
    def priority(self) -> int:
        """Priority for agent selection (lower = higher priority)."""
        return self._priority

    async def is_available(self) -> bool:
        """Check if Claude Code CLI is installed.

        Returns:
            True if the claude command is in PATH.
        """
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float | None = None,
    ) -> CLITaskResult:
        """Execute a coding task via Claude Code CLI.

        Args:
            prompt: Task description or instruction.
            working_dir: Directory to run the command in.
            timeout_seconds: Timeout in seconds (uses default if None).

        Returns:
            CLITaskResult with execution details.
        """
        timeout = timeout_seconds or self.default_timeout
        start_time = asyncio.get_event_loop().time()

        try:
            # Build command: claude --print --output-format json -p "prompt"
            cmd = [self.command, *self.default_args]

            # Add model if specified
            if self.model:
                cmd.extend(["--model", self.model])

            # Add prompt
            cmd.extend(["-p", prompt])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            duration = asyncio.get_event_loop().time() - start_time
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else None

            # Parse structured output
            parsed = self._parse_output(stdout_text)

            return CLITaskResult(
                success=process.returncode == 0,
                output=stdout_text,
                error=stderr_text if process.returncode != 0 else None,
                files_modified=parsed.get("files_modified", []),
                files_created=parsed.get("files_created", []),
                duration_seconds=duration,
                agent_name=self.name,
                exit_code=process.returncode or 0,
                metadata=parsed.get("metadata", {}),
            )

        except TimeoutError:
            return CLITaskResult(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                files_modified=[],
                files_created=[],
                duration_seconds=timeout,
                agent_name=self.name,
                exit_code=-1,
            )
        except FileNotFoundError:
            return CLITaskResult(
                success=False,
                output="",
                error=f"Command not found: {self.command}",
                files_modified=[],
                files_created=[],
                duration_seconds=0.0,
                agent_name=self.name,
                exit_code=-1,
            )

    def get_capabilities(self) -> list[str]:
        """Return list of supported capabilities.

        Returns:
            List of capability strings.
        """
        return [
            "code_generation",
            "refactoring",
            "testing",
            "git_integration",
            "multi_file",
            "code_review",
        ]

    def _parse_output(self, output: str) -> dict[str, Any]:
        """Parse JSON output from Claude Code.

        Args:
            output: Raw stdout from the command.

        Returns:
            Parsed dictionary or empty dict if parsing fails.
        """
        try:
            data = json.loads(output)
            return {
                "files_modified": data.get("files_modified", []),
                "files_created": data.get("files_created", []),
                "metadata": {
                    k: v
                    for k, v in data.items()
                    if k not in ("files_modified", "files_created")
                },
            }
        except json.JSONDecodeError:
            # Try to extract file info from non-JSON output
            return self._parse_text_output(output)

    def _parse_text_output(self, output: str) -> dict[str, Any]:
        """Parse text output to extract file information.

        Args:
            output: Raw text output.

        Returns:
            Parsed dictionary with file lists.
        """
        files_modified: list[str] = []
        files_created: list[str] = []

        for line in output.split("\n"):
            line = line.strip()
            # Look for common patterns in Claude Code output
            if line.startswith("Modified:") or line.startswith("Updated:"):
                file_path = line.split(":", 1)[-1].strip()
                if file_path:
                    files_modified.append(file_path)
            elif line.startswith("Created:"):
                file_path = line.split(":", 1)[-1].strip()
                if file_path:
                    files_created.append(file_path)

        return {
            "files_modified": files_modified,
            "files_created": files_created,
            "metadata": {},
        }


def create_claude_code_adapter_from_config() -> ClaudeCodeAdapter:
    """Create a ClaudeCodeAdapter from application configuration.

    Reads settings from config and returns configured adapter.

    Returns:
        Configured ClaudeCodeAdapter instance.
    """
    from rice_factor.config.settings import settings

    command = settings.get("cli_agents.claude_code.command", "claude")
    timeout = settings.get("cli_agents.claude_code.timeout", 300.0)
    model = settings.get("cli_agents.claude_code.model", None)
    priority = settings.get("cli_agents.claude_code.priority", 10)

    return ClaudeCodeAdapter(
        command=command,
        default_timeout=timeout,
        model=model,
        _priority=priority,
    )
