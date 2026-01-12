"""Aider CLI adapter.

This module provides an adapter for the Aider CLI tool
(https://github.com/Aider-AI/aider), allowing integration
with the rice-factor orchestration layer.
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING

from rice_factor.adapters.llm.cli.base import CLITaskResult

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class AiderAdapter:
    """Adapter for Aider CLI (Aider-AI/aider).

    Aider is a powerful AI pair programming tool that works with
    many LLM providers (Claude, OpenAI, Ollama, etc.). It excels
    at multi-file changes and git integration.

    Example:
        >>> adapter = AiderAdapter()
        >>> if await adapter.is_available():
        ...     result = await adapter.execute_task(
        ...         "Add error handling to database layer",
        ...         working_dir=Path("/project"),
        ...     )

    Attributes:
        command: CLI command name (default: 'aider').
        model: Model to use (e.g., 'claude-3-5-sonnet', 'ollama/codestral').
        auto_commits: Whether to auto-commit changes.
        default_timeout: Default timeout in seconds.
    """

    command: str = "aider"
    model: str = "claude-sonnet-4-20250514"
    auto_commits: bool = False
    default_timeout: float = 600.0
    _priority: int = 14

    @property
    def name(self) -> str:
        """Agent identifier."""
        return "aider"

    @property
    def priority(self) -> int:
        """Priority for agent selection."""
        return self._priority

    async def is_available(self) -> bool:
        """Check if Aider CLI is installed.

        Returns:
            True if the aider command is in PATH.
        """
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float | None = None,
    ) -> CLITaskResult:
        """Execute a coding task via Aider CLI.

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
            # Build command: aider --yes --message "prompt" --model model
            cmd = [
                self.command,
                "--yes",  # Auto-accept changes (non-interactive)
                "--message",
                prompt,
                "--model",
                self.model,
            ]

            if not self.auto_commits:
                cmd.append("--no-auto-commits")

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

            # Parse Aider-specific output
            files_modified = self._parse_modified_files(stdout_text)

            return CLITaskResult(
                success=process.returncode == 0,
                output=stdout_text,
                error=stderr_text if process.returncode != 0 else None,
                files_modified=files_modified,
                files_created=[],  # Aider doesn't clearly separate created vs modified
                duration_seconds=duration,
                agent_name=self.name,
                exit_code=process.returncode or 0,
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
            "git_integration",
            "multi_file",
            "testing",
        ]

    def _parse_modified_files(self, output: str) -> list[str]:
        """Parse modified files from Aider output.

        Aider outputs lines like:
        - "Added file.py to the chat"
        - "Wrote file.py"

        Args:
            output: Raw stdout from Aider.

        Returns:
            List of modified file paths.
        """
        files: list[str] = []

        for line in output.split("\n"):
            line = line.strip()

            # Aider writes "Wrote filename" when saving changes
            if line.startswith("Wrote "):
                file_path = line.replace("Wrote ", "").strip()
                if file_path and file_path not in files:
                    files.append(file_path)

            # Also look for "Applied edit to filename"
            elif "Applied edit to " in line:
                parts = line.split("Applied edit to ")
                if len(parts) > 1:
                    file_path = parts[-1].strip()
                    if file_path and file_path not in files:
                        files.append(file_path)

        return files


def create_aider_adapter_from_config() -> AiderAdapter:
    """Create an AiderAdapter from application configuration.

    Returns:
        Configured AiderAdapter instance.
    """
    from rice_factor.config.settings import settings

    command = settings.get("cli_agents.aider.command", "aider")
    model = settings.get("cli_agents.aider.model", "claude-sonnet-4-20250514")
    auto_commits = settings.get("cli_agents.aider.auto_commits", False)
    timeout = settings.get("cli_agents.aider.timeout", 600.0)
    priority = settings.get("cli_agents.aider.priority", 14)

    return AiderAdapter(
        command=command,
        model=model,
        auto_commits=auto_commits,
        default_timeout=timeout,
        _priority=priority,
    )
