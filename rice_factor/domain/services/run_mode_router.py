"""Run mode router service.

This service routes coordination requests to the appropriate coordinator
based on the run mode configuration. It provides a unified interface for
CLI commands to invoke multi-agent coordination.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rice_factor.adapters.agents import (
    HybridCoordinator,
    OrchestratorCoordinator,
    RoleLockedCoordinator,
    SoloCoordinator,
    VotingCoordinator,
)
from rice_factor.adapters.agents.base import BaseCoordinator  # noqa: TC001
from rice_factor.config.run_mode_config import RunMode, RunModeConfig

if TYPE_CHECKING:
    from rice_factor.domain.models.messages import CoordinationResult
    from rice_factor.domain.ports.coordinator import CoordinationContext


class RunModeRouter:
    """Routes coordination to the appropriate coordinator.

    This service:
    - Loads run mode configuration
    - Creates the appropriate coordinator
    - Routes coordination requests

    Example:
        >>> router = RunModeRouter(project_root=Path("."))
        >>> result = await router.coordinate(context)
    """

    def __init__(
        self,
        project_root: Path | None = None,
        config: RunModeConfig | None = None,
        mode_override: RunMode | None = None,
    ) -> None:
        """Initialize the router.

        Args:
            project_root: Project root for loading config. Defaults to cwd.
            config: Optional pre-loaded configuration.
            mode_override: Optional mode to override config setting.
        """
        self._project_root = project_root or Path.cwd()
        self._mode_override = mode_override

        # Load or use provided config
        if config is not None:
            self._config = config
        else:
            self._config = RunModeConfig.from_project(self._project_root)

        # Apply mode override if provided
        if mode_override is not None:
            self._config = self._override_mode(self._config, mode_override)

        self._coordinator: BaseCoordinator | None = None

    @property
    def mode(self) -> RunMode:
        """Get the active run mode."""
        return self._config.mode

    @property
    def config(self) -> RunModeConfig:
        """Get the run mode configuration."""
        return self._config

    def _override_mode(
        self,
        config: RunModeConfig,
        mode: RunMode,
    ) -> RunModeConfig:
        """Create a new config with mode overridden.

        Args:
            config: Original configuration.
            mode: New mode to use.

        Returns:
            New configuration with updated mode.
        """
        # Create new config with same settings but different mode
        # Note: dataclass is frozen, so we create a new instance
        return RunModeConfig(
            mode=mode,
            authority_agent=config.authority_agent,
            agents=config.agents,
            rules=config.rules,
            voting_threshold=config.voting_threshold,
            max_rounds=config.max_rounds,
            phase_modes=config.phase_modes,
        )

    def get_coordinator(self) -> BaseCoordinator:
        """Get the coordinator for the configured mode.

        Returns:
            Coordinator instance.

        Raises:
            ValueError: If mode is not supported.
        """
        if self._coordinator is None:
            self._coordinator = self._create_coordinator()
        return self._coordinator

    def _create_coordinator(self) -> BaseCoordinator:
        """Create a coordinator for the current mode.

        Returns:
            Coordinator instance.

        Raises:
            ValueError: If mode is not supported.
        """
        mode = self._config.mode

        if mode == RunMode.SOLO:
            return SoloCoordinator(self._config)
        elif mode == RunMode.ORCHESTRATOR:
            return OrchestratorCoordinator(self._config)
        elif mode == RunMode.VOTING:
            return VotingCoordinator(self._config)
        elif mode == RunMode.ROLE_LOCKED:
            return RoleLockedCoordinator(self._config)
        elif mode == RunMode.HYBRID:
            return HybridCoordinator(self._config)
        else:
            raise ValueError(f"Unsupported run mode: {mode}")

    async def coordinate(
        self,
        context: CoordinationContext,
    ) -> CoordinationResult:
        """Route coordination to the appropriate coordinator.

        Args:
            context: The coordination context.

        Returns:
            Coordination result.
        """
        coordinator = self.get_coordinator()
        return await coordinator.coordinate(context)

    @classmethod
    def from_cli_mode(
        cls,
        mode_str: str | None,
        project_root: Path | None = None,
    ) -> RunModeRouter:
        """Create router from CLI mode string.

        Args:
            mode_str: Mode string from CLI (e.g., "solo", "orchestrator").
            project_root: Project root path.

        Returns:
            Configured router.
        """
        mode_override = None
        if mode_str:
            try:
                mode_override = RunMode(mode_str.lower())
            except ValueError as e:
                valid_modes = ", ".join(m.value for m in RunMode)
                raise ValueError(
                    f"Invalid mode '{mode_str}'. Valid modes: {valid_modes}"
                ) from e

        return cls(
            project_root=project_root,
            mode_override=mode_override,
        )

    def describe(self) -> str:
        """Get a description of the current mode.

        Returns:
            Human-readable description.
        """
        mode = self._config.mode
        mode_descriptions = {
            RunMode.SOLO: "Solo mode - single agent with full authority",
            RunMode.ORCHESTRATOR: "Orchestrator mode - delegation pattern",
            RunMode.VOTING: "Voting mode - consensus through voting",
            RunMode.ROLE_LOCKED: "Role-locked mode - fixed role workflow",
            RunMode.HYBRID: "Hybrid mode - phase-based mode switching",
        }
        return mode_descriptions.get(mode, f"Unknown mode: {mode}")
