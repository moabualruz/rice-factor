"""OpenCode CLI adapter for Rice-Factor.

OpenCode is an open-source AI coding agent (opencode.ai) with 50k+ GitHub stars.
Supports multiple AI providers: Anthropic, OpenAI, Google, Groq, AWS Bedrock, etc.

References:
- Website: https://opencode.ai/
- Documentation: https://opencode.ai/docs/
- CLI Reference: https://opencode.ai/docs/cli/
- GitHub: https://github.com/sst/opencode
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import shutil
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rice_factor.adapters.llm.cli.base import CLITaskResult

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class OpenCodeAdapter:
    """Adapter for OpenCode CLI (opencode.ai).

    OpenCode is an open-source AI coding agent with 50k+ GitHub stars.
    Supports multiple AI providers (Claude, OpenAI, Gemini, Groq, etc.).

    Key features:
    - `opencode run "prompt"` for non-interactive execution
    - `--format json` for structured output
    - `--model provider/model` for model selection
    - `--attach url` for server mode (faster, avoids cold boot)
    - `--session` / `--continue` for session management
    """

    command: str = "opencode"
    default_args: list[str] = field(default_factory=lambda: ["run"])
    default_timeout: float = 300.0
    model: str | None = None
    attach_url: str | None = None
    session_id: str | None = None
    continue_session: bool = False
    output_format: str = "json"
    _priority: int = 15

    @property
    def name(self) -> str:
        """Agent identifier."""
        return "opencode"

    @property
    def priority(self) -> int:
        """Priority for agent selection (lower = higher priority)."""
        return self._priority

    async def is_available(self) -> bool:
        """Check if OpenCode CLI is installed."""
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float = 300.0,
    ) -> CLITaskResult:
        """Execute task via OpenCode CLI in non-interactive mode.

        Args:
            prompt: The task prompt to execute
            working_dir: Working directory for execution
            timeout_seconds: Maximum execution time

        Returns:
            CLITaskResult with execution results
        """
        timeout = timeout_seconds or self.default_timeout
        start_time = time.monotonic()

        cmd = self._build_command(prompt)

        try:
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

            duration = time.monotonic() - start_time
            output = stdout.decode("utf-8")
            error_output = stderr.decode("utf-8") if stderr else None

            return CLITaskResult(
                success=process.returncode == 0,
                output=output,
                error=error_output,
                files_modified=self._parse_modified_files(output),
                files_created=self._parse_created_files(output),
                duration_seconds=duration,
                agent_name=self.name,
                exit_code=process.returncode or 0,
                metadata=self._extract_metadata(output),
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
                error=f"OpenCode CLI not found: {self.command}",
                files_modified=[],
                files_created=[],
                duration_seconds=0.0,
                agent_name=self.name,
                exit_code=-1,
            )

    def _build_command(self, prompt: str) -> list[str]:
        """Build the OpenCode command with all arguments."""
        cmd = [self.command, *self.default_args]

        # Output format
        if self.output_format:
            cmd.extend(["--format", self.output_format])

        # Model selection (provider/model format)
        if self.model:
            cmd.extend(["--model", self.model])

        # Server attach mode for faster execution
        if self.attach_url:
            cmd.extend(["--attach", self.attach_url])

        # Session management
        if self.session_id:
            cmd.extend(["--session", self.session_id])
        elif self.continue_session:
            cmd.append("--continue")

        # Add the prompt
        cmd.append(prompt)

        return cmd

    def _parse_modified_files(self, output: str) -> list[str]:
        """Parse modified files from output."""
        files: list[str] = []

        # Try JSON parsing first
        with contextlib.suppress(json.JSONDecodeError):
            data = json.loads(output)
            if isinstance(data, dict):
                files.extend(data.get("files_modified", []))
                return files

        # Fallback: look for file modification patterns in text output
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Modified ") or line.startswith("Updated "):
                file_path = line.split(" ", 1)[-1].strip()
                if file_path:
                    files.append(file_path)

        return files

    def _parse_created_files(self, output: str) -> list[str]:
        """Parse created files from output."""
        files: list[str] = []

        # Try JSON parsing first
        with contextlib.suppress(json.JSONDecodeError):
            data = json.loads(output)
            if isinstance(data, dict):
                files.extend(data.get("files_created", []))
                return files

        # Fallback: look for file creation patterns in text output
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Created ") or line.startswith("Wrote "):
                file_path = line.split(" ", 1)[-1].strip()
                if file_path:
                    files.append(file_path)

        return files

    def _extract_metadata(self, output: str) -> dict[str, str]:
        """Extract metadata from output."""
        metadata: dict[str, str] = {}

        with contextlib.suppress(json.JSONDecodeError):
            data = json.loads(output)
            if isinstance(data, dict):
                if "session_id" in data:
                    metadata["session_id"] = str(data["session_id"])
                if "model" in data:
                    metadata["model"] = str(data["model"])
                if "provider" in data:
                    metadata["provider"] = str(data["provider"])

        return metadata

    def get_capabilities(self) -> list[str]:
        """Return list of capabilities."""
        return [
            "code_generation",
            "refactoring",
            "file_manipulation",
            "command_execution",
            "multi_file",
            "testing",
        ]


def create_opencode_adapter_from_config(config: dict[str, object]) -> OpenCodeAdapter:
    """Create an OpenCodeAdapter from configuration dictionary.

    Args:
        config: Configuration dictionary with optional keys:
            - command: OpenCode command name (default: "opencode")
            - model: Model in provider/model format (e.g., "anthropic/claude-4-sonnet")
            - attach_url: Server URL for attach mode (e.g., "http://localhost:4096")
            - timeout_seconds: Default timeout (default: 300)
            - session_id: Session ID to resume
            - continue_session: Whether to continue last session
            - output_format: Output format (default: "json")

    Returns:
        Configured OpenCodeAdapter instance.
    """
    timeout_raw = config.get("timeout_seconds", 300.0)
    timeout_val = float(str(timeout_raw)) if timeout_raw is not None else 300.0
    return OpenCodeAdapter(
        command=str(config.get("command", "opencode")),
        model=str(config["model"]) if config.get("model") else None,
        attach_url=str(config["attach_url"]) if config.get("attach_url") else None,
        default_timeout=timeout_val,
        session_id=str(config["session_id"]) if config.get("session_id") else None,
        continue_session=bool(config.get("continue_session", False)),
        output_format=str(config.get("output_format", "json")),
    )
