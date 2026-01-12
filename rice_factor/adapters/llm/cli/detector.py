"""CLI agent detection and discovery.

This module provides functionality to auto-detect available CLI
coding agents installed on the system.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

from rice_factor.adapters.llm.cli.base import DetectedAgent


@dataclass
class AgentConfig:
    """Configuration for detecting a CLI agent."""

    command: str
    version_flag: str = "--version"
    timeout_seconds: float = 5.0


# Default agent configurations
DEFAULT_AGENT_CONFIGS: dict[str, AgentConfig] = {
    "claude_code": AgentConfig(command="claude"),
    "codex": AgentConfig(command="codex"),
    "gemini_cli": AgentConfig(command="gemini"),
    "qwen_code": AgentConfig(command="qwen-code"),
    "aider": AgentConfig(command="aider"),
    "opencode": AgentConfig(command="opencode"),
    "cursor": AgentConfig(command="cursor"),
    "continue": AgentConfig(command="continue"),
}


@dataclass
class CLIAgentDetector:
    """Auto-detect available CLI coding agents.

    Scans the system PATH for known CLI coding tools and reports
    their availability and version information.

    Example:
        >>> detector = CLIAgentDetector()
        >>> agents = detector.detect_all()
        >>> for agent in agents:
        ...     if agent.available:
        ...         print(f"{agent.name}: {agent.version}")
    """

    configs: dict[str, AgentConfig] = field(default_factory=lambda: DEFAULT_AGENT_CONFIGS.copy())

    def detect_all(self) -> list[DetectedAgent]:
        """Detect all configured CLI agents.

        Returns:
            List of DetectedAgent objects with availability info.
        """
        results: list[DetectedAgent] = []

        for name, config in self.configs.items():
            agent = self.detect_agent(name, config)
            results.append(agent)

        return results

    def detect_agent(self, name: str, config: AgentConfig) -> DetectedAgent:
        """Detect a single CLI agent.

        Args:
            name: Agent identifier.
            config: Agent configuration.

        Returns:
            DetectedAgent with availability and version info.
        """
        path = shutil.which(config.command)
        available = path is not None

        version = None
        if available:
            version = self._get_version(config)

        return DetectedAgent(
            name=name,
            command=config.command,
            version=version,
            available=available,
            path=path,
        )

    def detect_available(self) -> list[DetectedAgent]:
        """Detect only available (installed) CLI agents.

        Returns:
            List of available DetectedAgent objects.
        """
        return [a for a in self.detect_all() if a.available]

    def is_agent_available(self, name: str) -> bool:
        """Check if a specific agent is available.

        Args:
            name: Agent identifier.

        Returns:
            True if the agent is installed.
        """
        config = self.configs.get(name)
        if not config:
            return False
        return shutil.which(config.command) is not None

    def add_agent_config(self, name: str, config: AgentConfig) -> None:
        """Add a custom agent configuration.

        Args:
            name: Agent identifier.
            config: Agent configuration.
        """
        self.configs[name] = config

    def remove_agent_config(self, name: str) -> bool:
        """Remove an agent configuration.

        Args:
            name: Agent identifier.

        Returns:
            True if agent was found and removed.
        """
        if name in self.configs:
            del self.configs[name]
            return True
        return False

    def _get_version(self, config: AgentConfig) -> str | None:
        """Get version string from CLI tool.

        Args:
            config: Agent configuration.

        Returns:
            Version string or None if unavailable.
        """
        try:
            result = subprocess.run(
                [config.command, config.version_flag],
                capture_output=True,
                text=True,
                timeout=config.timeout_seconds,
            )
            if result.returncode == 0 and result.stdout.strip():
                # Return first line of version output
                return result.stdout.strip().split("\n")[0]
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return None

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Export detection results as a dictionary.

        Returns:
            Dict mapping agent names to their detection info.
        """
        results: dict[str, dict[str, Any]] = {}
        for agent in self.detect_all():
            results[agent.name] = {
                "command": agent.command,
                "available": agent.available,
                "version": agent.version,
                "path": agent.path,
            }
        return results
