"""Hybrid mode coordinator (Mode E).

Hybrid mode combines multiple run modes and switches between them
based on workflow phases. Different phases can use different
coordination strategies.

Best for:
- Complex multi-phase projects
- Mixed methodology needs
- Adaptive workflows
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rice_factor.adapters.agents.base import BaseCoordinator
from rice_factor.adapters.agents.orchestrator_mode import OrchestratorCoordinator
from rice_factor.adapters.agents.role_locked_mode import RoleLockedCoordinator
from rice_factor.adapters.agents.solo_mode import SoloCoordinator
from rice_factor.adapters.agents.voting_mode import VotingCoordinator
from rice_factor.config.run_mode_config import RunMode
from rice_factor.domain.models.messages import (
    CoordinationResult,
)
from rice_factor.domain.ports.coordinator import CoordinationContext  # noqa: TC001

if TYPE_CHECKING:
    from rice_factor.config.run_mode_config import RunModeConfig


# Default phase-to-mode mapping
DEFAULT_PHASE_MODES: dict[str, RunMode] = {
    "planning": RunMode.ORCHESTRATOR,
    "design": RunMode.VOTING,
    "implementation": RunMode.ROLE_LOCKED,
    "review": RunMode.ROLE_LOCKED,
    "testing": RunMode.ORCHESTRATOR,
    "deployment": RunMode.SOLO,
}


class HybridCoordinator(BaseCoordinator):
    """Coordinator for hybrid mode (phase-based mode switching).

    In hybrid mode:
    - Different phases use different run modes
    - Mode is selected based on task type or explicit phase
    - All modes share the same agent pool
    - Seamless switching between coordination strategies

    Common phase mappings:
    - Planning: Orchestrator (delegate analysis)
    - Design: Voting (consensus on approach)
    - Implementation: Role-locked (structured workflow)
    - Review: Role-locked (mandatory critic)
    - Testing: Orchestrator (coordinate test runs)
    - Deployment: Solo (simple, low overhead)
    """

    def __init__(self, config: RunModeConfig) -> None:
        """Initialize the hybrid coordinator.

        Args:
            config: The run mode configuration.
        """
        super().__init__(config)
        self._phase_coordinators: dict[RunMode, BaseCoordinator] = {}
        self._current_phase: str | None = None
        self._phase_results: list[dict[str, Any]] = []

    @property
    def mode_name(self) -> str:
        """Get the mode name."""
        return "hybrid"

    def get_phase_mode(self, phase: str) -> RunMode:
        """Get the run mode for a specific phase.

        Args:
            phase: The phase name.

        Returns:
            RunMode to use for this phase.
        """
        # Check config first
        if phase in self._config.phase_modes:
            return self._config.phase_modes[phase]

        # Fall back to defaults
        return DEFAULT_PHASE_MODES.get(phase, RunMode.SOLO)

    def get_coordinator_for_mode(self, mode: RunMode) -> BaseCoordinator:
        """Get or create a coordinator for the specified mode.

        Args:
            mode: The run mode.

        Returns:
            Coordinator instance for that mode.
        """
        if mode not in self._phase_coordinators:
            coordinator = self._create_coordinator(mode)
            self._phase_coordinators[mode] = coordinator

        return self._phase_coordinators[mode]

    def _create_coordinator(self, mode: RunMode) -> BaseCoordinator:
        """Create a coordinator for the specified mode.

        Args:
            mode: The run mode.

        Returns:
            New coordinator instance.
        """
        if mode == RunMode.SOLO:
            return SoloCoordinator(self._config)
        elif mode == RunMode.ORCHESTRATOR:
            return OrchestratorCoordinator(self._config)
        elif mode == RunMode.VOTING:
            return VotingCoordinator(self._config)
        elif mode == RunMode.ROLE_LOCKED:
            return RoleLockedCoordinator(self._config)
        else:
            # Default to solo
            return SoloCoordinator(self._config)

    async def coordinate(
        self,
        context: CoordinationContext,
    ) -> CoordinationResult:
        """Execute coordination in hybrid mode.

        The coordination:
        1. Determines the phase from task type
        2. Selects appropriate run mode for phase
        3. Delegates to the phase-specific coordinator
        4. Collects and aggregates results

        Args:
            context: The coordination context with task details.

        Returns:
            CoordinationResult with the outcome.
        """
        start_time = time.time()
        session_id = self._generate_session_id()
        self._phase_results = []

        try:
            # Determine phase from task type or context
            phase = self._determine_phase(context)
            self._current_phase = phase

            # Get mode for this phase
            mode = self.get_phase_mode(phase)

            # Get coordinator for this mode
            coordinator = self.get_coordinator_for_mode(mode)

            # Delegate to phase-specific coordinator
            phase_result = await coordinator.coordinate(context)

            # Record phase result
            self._phase_results.append({
                "phase": phase,
                "mode": mode.value,
                "success": phase_result.success,
                "result": phase_result,
            })

            duration_ms = int((time.time() - start_time) * 1000)

            # Build aggregated reasoning
            reasoning = self._compile_hybrid_reasoning(phase, mode, phase_result)

            return CoordinationResult(
                session_id=session_id,
                success=phase_result.success,
                participating_agents=phase_result.participating_agents,
                messages_exchanged=phase_result.messages_exchanged,
                artifact_id=phase_result.artifact_id,
                final_decision=phase_result.final_decision,
                reasoning=reasoning,
                votes=phase_result.votes,
                errors=phase_result.errors,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CoordinationResult(
                session_id=session_id,
                success=False,
                participating_agents=tuple(self._agents.keys()),
                messages_exchanged=self._get_messages_sent(),
                errors=(str(e),),
                duration_ms=duration_ms,
            )

    async def coordinate_multi_phase(
        self,
        phases: list[tuple[str, CoordinationContext]],
    ) -> list[CoordinationResult]:
        """Execute coordination across multiple phases.

        This method allows explicit multi-phase coordination where
        each phase has its own context.

        Args:
            phases: List of (phase_name, context) tuples.

        Returns:
            List of CoordinationResult for each phase.
        """
        results: list[CoordinationResult] = []

        for phase, context in phases:
            self._current_phase = phase
            mode = self.get_phase_mode(phase)
            coordinator = self.get_coordinator_for_mode(mode)

            result = await coordinator.coordinate(context)
            results.append(result)

            self._phase_results.append({
                "phase": phase,
                "mode": mode.value,
                "success": result.success,
                "result": result,
            })

            # Stop if a phase fails
            if not result.success:
                break

        return results

    def _determine_phase(self, context: CoordinationContext) -> str:
        """Determine the phase from the context.

        Uses task_type to infer the appropriate phase.

        Args:
            context: The coordination context.

        Returns:
            Phase name string.
        """
        task_type = context.task_type.lower()

        # Map common task types to phases
        type_to_phase: dict[str, str] = {
            "plan": "planning",
            "planning": "planning",
            "project_plan": "planning",
            "design": "design",
            "architecture": "design",
            "architecture_plan": "design",
            "implement": "implementation",
            "implementation": "implementation",
            "implementation_plan": "implementation",
            "code": "implementation",
            "scaffold": "implementation",
            "review": "review",
            "critique": "review",
            "test": "testing",
            "testing": "testing",
            "test_plan": "testing",
            "deploy": "deployment",
            "deployment": "deployment",
            "refactor": "implementation",
            "refactor_plan": "implementation",
        }

        return type_to_phase.get(task_type, "implementation")

    def _compile_hybrid_reasoning(
        self,
        phase: str,
        mode: RunMode,
        result: CoordinationResult,
    ) -> str:
        """Compile reasoning for hybrid coordination.

        Args:
            phase: The executed phase.
            mode: The mode used for the phase.
            result: The coordination result.

        Returns:
            Combined reasoning string.
        """
        parts = [
            "Hybrid Mode Coordination:",
            f"  Phase: {phase}",
            f"  Mode: {mode.value}",
            f"  Success: {result.success}",
        ]

        if result.reasoning:
            parts.append(f"\nPhase Reasoning:\n{result.reasoning}")

        # Add phase history if multiple phases
        if len(self._phase_results) > 1:
            parts.append("\nPhase History:")
            for pr in self._phase_results:
                status = "OK" if pr["success"] else "FAILED"
                parts.append(f"  [{pr['mode']}] {pr['phase']}: {status}")

        return "\n".join(parts)

    def get_current_phase(self) -> str | None:
        """Get the current phase being executed.

        Returns:
            Current phase name or None.
        """
        return self._current_phase

    def get_phase_results(self) -> list[dict[str, Any]]:
        """Get results from all executed phases.

        Returns:
            List of phase result dictionaries.
        """
        return self._phase_results.copy()

    def get_available_modes(self) -> list[RunMode]:
        """Get all available run modes.

        Returns:
            List of available RunMode values.
        """
        return [RunMode.SOLO, RunMode.ORCHESTRATOR, RunMode.VOTING, RunMode.ROLE_LOCKED]

    def get_phase_mode_mapping(self) -> dict[str, RunMode]:
        """Get the complete phase-to-mode mapping.

        Merges config overrides with defaults.

        Returns:
            Dict mapping phase names to RunMode.
        """
        mapping = DEFAULT_PHASE_MODES.copy()
        mapping.update(self._config.phase_modes)
        return mapping
