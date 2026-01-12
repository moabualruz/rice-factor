"""Lifecycle orchestrator for phase-driven execution.

This module provides the LifecycleOrchestrator service that drives
lifecycle phases programmatically (plan → approve → execute) with
state persistence for resume capability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class Phase(Enum):
    """Lifecycle phases."""

    INIT = "init"
    PLAN = "plan"
    SCAFFOLD = "scaffold"
    TEST = "test"
    IMPLEMENT = "implement"
    EXECUTE = "execute"
    VALIDATE = "validate"
    REFACTOR = "refactor"
    COMPLETE = "complete"


class PhaseStatus(Enum):
    """Status of a phase."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Result of a phase execution.

    Attributes:
        phase: The phase that was executed.
        status: Execution status.
        started_at: When phase started.
        completed_at: When phase finished.
        artifacts_created: List of artifact IDs created.
        error: Error message if failed.
    """

    phase: Phase
    status: PhaseStatus
    started_at: datetime
    completed_at: datetime | None = None
    artifacts_created: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase": self.phase.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "artifacts_created": self.artifacts_created,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhaseResult:
        """Create from dictionary."""
        return cls(
            phase=Phase(data["phase"]),
            status=PhaseStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            artifacts_created=data.get("artifacts_created", []),
            error=data.get("error"),
        )


@dataclass
class OrchestratorState:
    """State of the orchestrator for resume.

    Attributes:
        current_phase: Current phase.
        phase_results: Results of completed phases.
        started_at: When orchestration started.
        last_updated: When state was last updated.
        context: Additional context data.
    """

    current_phase: Phase
    phase_results: dict[str, PhaseResult]
    started_at: datetime
    last_updated: datetime
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_phase": self.current_phase.value,
            "phase_results": {
                k: v.to_dict() for k, v in self.phase_results.items()
            },
            "started_at": self.started_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrchestratorState:
        """Create from dictionary."""
        return cls(
            current_phase=Phase(data["current_phase"]),
            phase_results={
                k: PhaseResult.from_dict(v)
                for k, v in data.get("phase_results", {}).items()
            },
            started_at=datetime.fromisoformat(data["started_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            context=data.get("context", {}),
        )


PhaseHandler = Callable[[dict[str, Any]], PhaseResult]


@dataclass
class LifecycleOrchestrator:
    """Service for phase-driven lifecycle orchestration.

    Drives lifecycle phases programmatically with support for
    phase transition hooks and state persistence for resume.

    Attributes:
        repo_root: Root directory of the repository.
        state_path: Path to store orchestrator state.
    """

    repo_root: Path
    state_path: Path | None = None
    _state: OrchestratorState | None = field(default=None, init=False, repr=False)
    _handlers: dict[Phase, PhaseHandler] = field(
        default_factory=dict, init=False, repr=False
    )
    _hooks: dict[str, list[Callable[[Phase, PhaseResult], None]]] = field(
        default_factory=dict, init=False, repr=False
    )

    # Phase ordering
    PHASE_ORDER = [
        Phase.INIT,
        Phase.PLAN,
        Phase.SCAFFOLD,
        Phase.TEST,
        Phase.IMPLEMENT,
        Phase.EXECUTE,
        Phase.VALIDATE,
        Phase.REFACTOR,
        Phase.COMPLETE,
    ]

    def __post_init__(self) -> None:
        """Initialize paths."""
        if self.state_path is None:
            self.state_path = self.repo_root / ".rice_factor" / "orchestrator_state.json"
        self._hooks = {"pre": [], "post": []}
        self._load_state()

    def _load_state(self) -> None:
        """Load state from disk."""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                self._state = OrchestratorState.from_dict(data)
            except (json.JSONDecodeError, OSError, KeyError):
                self._state = None

    def _save_state(self) -> None:
        """Save state to disk."""
        if self._state is not None:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(
                json.dumps(self._state.to_dict(), indent=2),
                encoding="utf-8",
            )

    def register_handler(self, phase: Phase, handler: PhaseHandler) -> None:
        """Register a handler for a phase.

        Args:
            phase: Phase to handle.
            handler: Handler function.
        """
        self._handlers[phase] = handler

    def register_hook(
        self,
        hook_type: str,
        hook: Callable[[Phase, PhaseResult], None],
    ) -> None:
        """Register a phase transition hook.

        Args:
            hook_type: "pre" or "post".
            hook: Hook function.
        """
        if hook_type in self._hooks:
            self._hooks[hook_type].append(hook)

    def start(self, context: dict[str, Any] | None = None) -> OrchestratorState:
        """Start a new orchestration.

        Args:
            context: Initial context data.

        Returns:
            Initial state.
        """
        now = datetime.now(UTC)
        self._state = OrchestratorState(
            current_phase=Phase.INIT,
            phase_results={},
            started_at=now,
            last_updated=now,
            context=context or {},
        )
        self._save_state()
        return self._state

    def resume(self) -> OrchestratorState | None:
        """Resume from saved state.

        Returns:
            Loaded state or None if no state exists.
        """
        self._load_state()
        return self._state

    def execute_phase(
        self,
        phase: Phase,
        context: dict[str, Any] | None = None,
    ) -> PhaseResult:
        """Execute a specific phase.

        Args:
            phase: Phase to execute.
            context: Additional context.

        Returns:
            PhaseResult with details.
        """
        if self._state is None:
            self.start(context)

        started_at = datetime.now(UTC)

        # Run pre-hooks
        for hook in self._hooks.get("pre", []):
            try:
                hook(phase, PhaseResult(
                    phase=phase,
                    status=PhaseStatus.PENDING,
                    started_at=started_at,
                ))
            except Exception:
                pass

        # Update state
        self._state.current_phase = phase
        self._state.last_updated = datetime.now(UTC)
        if context:
            self._state.context.update(context)
        self._save_state()

        # Execute handler if registered
        handler = self._handlers.get(phase)
        if handler:
            try:
                result = handler(self._state.context)
                result.started_at = started_at
                result.completed_at = datetime.now(UTC)
            except Exception as e:
                result = PhaseResult(
                    phase=phase,
                    status=PhaseStatus.FAILED,
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                    error=str(e),
                )
        else:
            # Default handler - just mark complete
            result = PhaseResult(
                phase=phase,
                status=PhaseStatus.COMPLETED,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

        # Store result
        self._state.phase_results[phase.value] = result
        self._state.last_updated = datetime.now(UTC)
        self._save_state()

        # Run post-hooks
        for hook in self._hooks.get("post", []):
            try:
                hook(phase, result)
            except Exception:
                pass

        return result

    def advance(self, context: dict[str, Any] | None = None) -> PhaseResult | None:
        """Advance to the next phase.

        Args:
            context: Additional context.

        Returns:
            PhaseResult if advanced, None if complete.
        """
        if self._state is None:
            self.start(context)

        current_idx = self.PHASE_ORDER.index(self._state.current_phase)
        if current_idx >= len(self.PHASE_ORDER) - 1:
            return None

        next_phase = self.PHASE_ORDER[current_idx + 1]
        return self.execute_phase(next_phase, context)

    def run_to_phase(
        self,
        target_phase: Phase,
        context: dict[str, Any] | None = None,
    ) -> list[PhaseResult]:
        """Run all phases up to and including target.

        Args:
            target_phase: Target phase to reach.
            context: Additional context.

        Returns:
            List of phase results.
        """
        if self._state is None:
            self.start(context)

        results: list[PhaseResult] = []
        target_idx = self.PHASE_ORDER.index(target_phase)

        for phase in self.PHASE_ORDER[: target_idx + 1]:
            if phase.value in self._state.phase_results:
                existing = self._state.phase_results[phase.value]
                if existing.status == PhaseStatus.COMPLETED:
                    results.append(existing)
                    continue

            result = self.execute_phase(phase, context)
            results.append(result)

            if result.status == PhaseStatus.FAILED:
                break

        return results

    def skip_phase(self, phase: Phase, reason: str = "Skipped") -> PhaseResult:
        """Skip a phase.

        Args:
            phase: Phase to skip.
            reason: Reason for skipping.

        Returns:
            PhaseResult with SKIPPED status.
        """
        if self._state is None:
            self.start()

        now = datetime.now(UTC)
        result = PhaseResult(
            phase=phase,
            status=PhaseStatus.SKIPPED,
            started_at=now,
            completed_at=now,
            error=reason,
        )

        self._state.phase_results[phase.value] = result
        self._state.last_updated = now
        self._save_state()

        return result

    def get_state(self) -> OrchestratorState | None:
        """Get current state.

        Returns:
            Current state or None.
        """
        return self._state

    def get_phase_result(self, phase: Phase) -> PhaseResult | None:
        """Get result for a specific phase.

        Args:
            phase: Phase to get result for.

        Returns:
            PhaseResult if exists.
        """
        if self._state is None:
            return None
        return self._state.phase_results.get(phase.value)

    def is_phase_complete(self, phase: Phase) -> bool:
        """Check if a phase is complete.

        Args:
            phase: Phase to check.

        Returns:
            True if phase is complete.
        """
        result = self.get_phase_result(phase)
        return result is not None and result.status == PhaseStatus.COMPLETED

    def reset(self) -> None:
        """Reset orchestrator state."""
        self._state = None
        if self.state_path.exists():
            self.state_path.unlink()

    def get_progress(self) -> dict[str, Any]:
        """Get orchestration progress.

        Returns:
            Progress summary.
        """
        if self._state is None:
            return {
                "status": "not_started",
                "completed_phases": 0,
                "total_phases": len(self.PHASE_ORDER),
                "current_phase": None,
            }

        completed = sum(
            1
            for p in self.PHASE_ORDER
            if self.is_phase_complete(p)
        )

        return {
            "status": "in_progress" if completed < len(self.PHASE_ORDER) else "complete",
            "completed_phases": completed,
            "total_phases": len(self.PHASE_ORDER),
            "current_phase": self._state.current_phase.value,
            "progress_percent": round(completed / len(self.PHASE_ORDER) * 100, 1),
        }
