"""Google Gemini CLI adapter.

This module provides an adapter for the Google Gemini CLI tool,
allowing integration with the rice-factor orchestration layer.
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
class GeminiCLIAdapter:
    """Adapter for Google Gemini CLI.

    Gemini CLI is an agentic coding tool from Google that can perform
    code generation, file operations, and other coding tasks.

    Example:
        >>> adapter = GeminiCLIAdapter()
        >>> if await adapter.is_available():
        ...     result = await adapter.execute_task(
        ...         "Create a REST API endpoint for users",
        ...         working_dir=Path("/project"),
        ...     )

    Attributes:
        command: CLI command name (default: 'gemini').
        default_args: Default arguments for execution.
        default_timeout: Default timeout in seconds.
        model: Model to use (optional).
    """

    command: str = "gemini"
    default_args: list[str] = field(default_factory=lambda: ["--json"])
    default_timeout: float = 300.0
    model: str | None = None
    _priority: int = 12

    @property
    def name(self) -> str:
        """Agent identifier."""
        return "gemini_cli"

    @property
    def priority(self) -> int:
        """Priority for agent selection."""
        return self._priority

    async def is_available(self) -> bool:
        """Check if Gemini CLI is installed.

        Returns:
            True if the gemini command is in PATH.
        """
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float | None = None,
    ) -> CLITaskResult:
        """Execute a coding task via Gemini CLI.

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
            # Build command
            cmd = [self.command, *self.default_args]

            if self.model:
                cmd.extend(["--model", self.model])

            cmd.extend(["--prompt", prompt])

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
            "file_operations",
            "multi_file",
        ]

    def _parse_output(self, output: str) -> dict[str, Any]:
        """Parse JSON output from Gemini CLI.

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


def create_gemini_cli_adapter_from_config() -> GeminiCLIAdapter:
    """Create a GeminiCLIAdapter from application configuration.

    Returns:
        Configured GeminiCLIAdapter instance.
    """
    from rice_factor.config.settings import settings

    command = settings.get("cli_agents.gemini_cli.command", "gemini")
    timeout = settings.get("cli_agents.gemini_cli.timeout", 300.0)
    model = settings.get("cli_agents.gemini_cli.model", None)
    priority = settings.get("cli_agents.gemini_cli.priority", 12)

    return GeminiCLIAdapter(
        command=command,
        default_timeout=timeout,
        model=model,
        _priority=priority,
    )
