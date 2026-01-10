"""Phase gating service for command execution control.

This module provides phase detection and command gating to enforce
the Rice-Factor workflow phases. Commands are only allowed to execute
when the project is in the appropriate phase.
"""

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.failures.cli_errors import MissingPrerequisiteError, PhaseError

if TYPE_CHECKING:
    from rice_factor.domain.services.artifact_service import ArtifactService


class Phase(str, Enum):
    """Project lifecycle phases.

    Phases represent the state of the project based on artifacts present
    and their status. Commands are gated based on the current phase.
    """

    UNINIT = "uninit"
    """No .project/ directory exists."""

    INIT = "init"
    """Project initialized but no artifacts created."""

    PLANNING = "planning"
    """ProjectPlan has been approved."""

    SCAFFOLDED = "scaffolded"
    """Scaffold has been executed (ScaffoldPlan approved + files created)."""

    TEST_LOCKED = "test_locked"
    """TestPlan has been locked (immutable)."""

    IMPLEMENTING = "implementing"
    """Active implementation phase (after TEST_LOCKED)."""


# Command to minimum phase mapping
# Commands can only execute at or after their required phase
COMMAND_PHASES: dict[str, Phase] = {
    # Always available
    "init": Phase.UNINIT,
    # Require initialized project
    "plan project": Phase.INIT,
    # Require ProjectPlan approved
    "plan architecture": Phase.PLANNING,
    "scaffold": Phase.PLANNING,
    # Require scaffold executed
    "plan tests": Phase.SCAFFOLDED,
    "lock": Phase.SCAFFOLDED,
    # Require TestPlan locked
    "plan impl": Phase.TEST_LOCKED,
    "impl": Phase.TEST_LOCKED,
    "review": Phase.TEST_LOCKED,
    "apply": Phase.TEST_LOCKED,
    "test": Phase.TEST_LOCKED,
    "diagnose": Phase.TEST_LOCKED,
    "approve": Phase.INIT,  # Can approve artifacts at any phase after init
    "plan refactor": Phase.TEST_LOCKED,
    "refactor check": Phase.TEST_LOCKED,
    "refactor dry-run": Phase.TEST_LOCKED,
    "refactor apply": Phase.TEST_LOCKED,
    "validate": Phase.INIT,  # Can validate at any phase after init
    "override": Phase.INIT,  # Override is an escape hatch
    "resume": Phase.INIT,  # Resume can work at any phase
}

# User-friendly phase descriptions
PHASE_DESCRIPTIONS: dict[Phase, str] = {
    Phase.UNINIT: "not initialized",
    Phase.INIT: "initialized (no artifacts)",
    Phase.PLANNING: "planning (ProjectPlan approved)",
    Phase.SCAFFOLDED: "scaffolded (structure created)",
    Phase.TEST_LOCKED: "tests locked (implementation phase)",
    Phase.IMPLEMENTING: "implementing (active development)",
}


class PhaseService:
    """Service for determining project phase and gating commands.

    The PhaseService analyzes the project state based on the existence
    of .project/ directory and artifact statuses to determine the
    current phase. Commands are then gated based on this phase.

    Attributes:
        project_root: Root directory of the project.
        artifact_service: Optional service for artifact status checks.
    """

    def __init__(
        self,
        project_root: Path,
        artifact_service: "ArtifactService | None" = None,
    ) -> None:
        """Initialize the phase service.

        Args:
            project_root: Root directory of the project.
            artifact_service: Service for artifact operations.
        """
        self._project_root = project_root
        self._artifact_service = artifact_service

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @property
    def artifact_service(self) -> "ArtifactService | None":
        """Get the artifact service."""
        return self._artifact_service

    def is_initialized(self) -> bool:
        """Check if the project has been initialized.

        Returns:
            True if .project/ directory exists.
        """
        project_dir = self._project_root / ".project"
        return project_dir.exists() and project_dir.is_dir()

    def get_current_phase(self) -> Phase:
        """Determine the current project phase.

        Analyzes the project state to determine which phase the project
        is currently in based on:
        - Existence of .project/ directory
        - Status of key artifacts (ProjectPlan, TestPlan, etc.)

        Returns:
            The current Phase.
        """
        # Check for .project/ directory
        if not self.is_initialized():
            return Phase.UNINIT

        # If no artifact service, can only determine INIT
        if self._artifact_service is None:
            return Phase.INIT

        # Check for locked TestPlan (highest phase)
        if self._has_locked_test_plan():
            return Phase.TEST_LOCKED

        # Check for approved ScaffoldPlan and executed scaffold
        if self._has_scaffolded():
            return Phase.SCAFFOLDED

        # Check for approved ProjectPlan
        if self._has_approved_project_plan():
            return Phase.PLANNING

        # Default to INIT if .project/ exists but no artifacts
        return Phase.INIT

    def _has_approved_project_plan(self) -> bool:
        """Check if ProjectPlan has been approved."""
        if self._artifact_service is None:
            return False

        try:
            storage = self._artifact_service.storage
            artifacts = storage.list_by_type(ArtifactType.PROJECT_PLAN)
            return any(
                a.status in (ArtifactStatus.APPROVED, ArtifactStatus.LOCKED)
                for a in artifacts
            )
        except Exception:
            return False

    def _has_scaffolded(self) -> bool:
        """Check if scaffold has been executed (ScaffoldPlan approved + files exist)."""
        if self._artifact_service is None:
            return False

        try:
            storage = self._artifact_service.storage
            artifacts = storage.list_by_type(ArtifactType.SCAFFOLD_PLAN)
            return any(
                a.status in (ArtifactStatus.APPROVED, ArtifactStatus.LOCKED)
                for a in artifacts
            )
        except Exception:
            return False

    def _has_locked_test_plan(self) -> bool:
        """Check if TestPlan has been locked."""
        if self._artifact_service is None:
            return False

        try:
            storage = self._artifact_service.storage
            artifacts = storage.list_by_type(ArtifactType.TEST_PLAN)
            return any(a.status == ArtifactStatus.LOCKED for a in artifacts)
        except Exception:
            return False

    def can_execute(self, command: str) -> bool:
        """Check if a command can be executed in the current phase.

        Args:
            command: The command name (e.g., "init", "plan project").

        Returns:
            True if the command can be executed.
        """
        current_phase = self.get_current_phase()
        required_phase = COMMAND_PHASES.get(command)

        if required_phase is None:
            # Unknown command, allow it (other validation will catch issues)
            return True

        # Compare phase order
        phase_order = list(Phase)
        current_index = phase_order.index(current_phase)
        required_index = phase_order.index(required_phase)

        return current_index >= required_index

    def get_blocking_reason(self, command: str) -> str | None:
        """Get a user-friendly message explaining why a command is blocked.

        Args:
            command: The command name.

        Returns:
            A message explaining why the command is blocked, or None if allowed.
        """
        if self.can_execute(command):
            return None

        current_phase = self.get_current_phase()
        required_phase = COMMAND_PHASES.get(command)

        if required_phase is None:
            return None

        current_desc = PHASE_DESCRIPTIONS.get(current_phase, current_phase.value)
        required_desc = PHASE_DESCRIPTIONS.get(required_phase, required_phase.value)

        return (
            f"Cannot run '{command}' in current phase: {current_desc}. "
            f"Required phase: {required_desc}."
        )

    def require_phase(self, command: str) -> None:
        """Raise an error if the command cannot be executed in the current phase.

        Args:
            command: The command name.

        Raises:
            PhaseError: If the command is not allowed in the current phase.
            MissingPrerequisiteError: If .project/ is missing for non-init commands.
        """
        current_phase = self.get_current_phase()
        required_phase = COMMAND_PHASES.get(command)

        # Special case: require .project/ for all commands except init
        if command != "init" and current_phase == Phase.UNINIT:
            raise MissingPrerequisiteError(
                command,
                "Project not initialized. Run 'rice-factor init' first.",
            )

        if required_phase is None:
            return

        if not self.can_execute(command):
            raise PhaseError(
                command=command,
                current_phase=current_phase.value,
                required_phase=required_phase.value,
            )
