"""OpenAI Codex CLI adapter.

This module provides an adapter for the OpenAI Codex CLI tool
(https://github.com/openai/codex), allowing integration with
the rice-factor orchestration layer.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from rice_factor.adapters.llm.cli.base import CLITaskResult

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class CodexAdapter:
    """Adapter for OpenAI Codex CLI (openai/codex).

    Codex CLI is an agentic coding tool that can perform code
    generation, refactoring, and code review tasks.

    Example:
        >>> adapter = CodexAdapter()
        >>> if await adapter.is_available():
        ...     result = await adapter.execute_task(
        ...         "Generate unit tests for utils.py",
        ...         working_dir=Path("/project"),
        ...     )

    Attributes:
        command: CLI command name (default: 'codex').
        approval_mode: Approval mode (suggest, auto-edit, full-auto).
        default_timeout: Default timeout in seconds.
    """

    command: str = "codex"
    approval_mode: str = "suggest"
    default_timeout: float = 300.0
    _priority: int = 11

    @property
    def name(self) -> str:
        """Agent identifier."""
        return "codex"

    @property
    def priority(self) -> int:
        """Priority for agent selection."""
        return self._priority

    async def is_available(self) -> bool:
        """Check if Codex CLI is installed.

        Returns:
            True if the codex command is in PATH.
        """
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float | None = None,
    ) -> CLITaskResult:
        """Execute a coding task via Codex CLI.

        Args:
            prompt: Task description or instruction.
            working_dir: Directory to run the command in.
            timeout_seconds: Timeout in seconds.

        Returns:
            CLITaskResult with execution details.
        """
        timeout = timeout_seconds or self.default_timeout
        start_time = asyncio.get_event_loop().time()

        try:
            # Build command: codex exec --approval-mode suggest --output-format json "prompt"
            cmd = [
                self.command,
                "exec",
                "--approval-mode",
                self.approval_mode,
                "--output-format",
                "json",
                prompt,
            ]

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
        """Return list of supported capabilities."""
        return [
            "code_generation",
            "refactoring",
            "code_review",
        ]

    def _parse_output(self, output: str) -> dict[str, Any]:
        """Parse JSON output from Codex.

        Args:
            output: Raw stdout from the command.

        Returns:
            Parsed dictionary.
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
            return {"files_modified": [], "files_created": [], "metadata": {}}


def create_codex_adapter_from_config() -> CodexAdapter:
    """Create a CodexAdapter from application configuration.

    Returns:
        Configured CodexAdapter instance.
    """
    from rice_factor.config.settings import settings

    command = settings.get("cli_agents.codex.command", "codex")
    approval_mode = settings.get("cli_agents.codex.approval_mode", "suggest")
    timeout = settings.get("cli_agents.codex.timeout", 300.0)
    priority = settings.get("cli_agents.codex.priority", 11)

    return CodexAdapter(
        command=command,
        approval_mode=approval_mode,
        default_timeout=timeout,
        _priority=priority,
    )
