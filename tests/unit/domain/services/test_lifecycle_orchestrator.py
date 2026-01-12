"""Unit tests for LifecycleOrchestrator service."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from rice_factor.domain.services.lifecycle_orchestrator import (
    LifecycleOrchestrator,
    OrchestratorState,
    Phase,
    PhaseResult,
    PhaseStatus,
)


class TestPhase:
    """Tests for Phase enum."""

    def test_all_phases_exist(self) -> None:
        """All expected phases should exist."""
        assert Phase.INIT.value == "init"
        assert Phase.PLAN.value == "plan"
        assert Phase.SCAFFOLD.value == "scaffold"
        assert Phase.TEST.value == "test"
        assert Phase.IMPLEMENT.value == "implement"
        assert Phase.EXECUTE.value == "execute"
        assert Phase.VALIDATE.value == "validate"
        assert Phase.REFACTOR.value == "refactor"
        assert Phase.COMPLETE.value == "complete"


class TestPhaseStatus:
    """Tests for PhaseStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """All expected statuses should exist."""
        assert PhaseStatus.PENDING.value == "pending"
        assert PhaseStatus.IN_PROGRESS.value == "in_progress"
        assert PhaseStatus.COMPLETED.value == "completed"
        assert PhaseStatus.FAILED.value == "failed"
        assert PhaseStatus.SKIPPED.value == "skipped"


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_creation(self) -> None:
        """PhaseResult should be creatable."""
        now = datetime.now(UTC)
        result = PhaseResult(
            phase=Phase.PLAN,
            status=PhaseStatus.COMPLETED,
            started_at=now,
            completed_at=now,
        )
        assert result.phase == Phase.PLAN
        assert result.status == PhaseStatus.COMPLETED

    def test_with_artifacts(self) -> None:
        """should include artifacts created."""
        now = datetime.now(UTC)
        result = PhaseResult(
            phase=Phase.PLAN,
            status=PhaseStatus.COMPLETED,
            started_at=now,
            artifacts_created=["plan-1", "plan-2"],
        )
        assert len(result.artifacts_created) == 2

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        result = PhaseResult(
            phase=Phase.TEST,
            status=PhaseStatus.COMPLETED,
            started_at=now,
            completed_at=now,
        )
        data = result.to_dict()
        assert data["phase"] == "test"
        assert data["status"] == "completed"

    def test_from_dict(self) -> None:
        """should deserialize from dictionary."""
        now = datetime.now(UTC)
        data = {
            "phase": "plan",
            "status": "completed",
            "started_at": now.isoformat(),
            "completed_at": now.isoformat(),
            "artifacts_created": ["a1"],
        }
        result = PhaseResult.from_dict(data)
        assert result.phase == Phase.PLAN
        assert result.status == PhaseStatus.COMPLETED


class TestOrchestratorState:
    """Tests for OrchestratorState dataclass."""

    def test_creation(self) -> None:
        """OrchestratorState should be creatable."""
        now = datetime.now(UTC)
        state = OrchestratorState(
            current_phase=Phase.INIT,
            phase_results={},
            started_at=now,
            last_updated=now,
        )
        assert state.current_phase == Phase.INIT

    def test_with_context(self) -> None:
        """should include context."""
        now = datetime.now(UTC)
        state = OrchestratorState(
            current_phase=Phase.PLAN,
            phase_results={},
            started_at=now,
            last_updated=now,
            context={"project_name": "test"},
        )
        assert state.context["project_name"] == "test"

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        state = OrchestratorState(
            current_phase=Phase.INIT,
            phase_results={},
            started_at=now,
            last_updated=now,
        )
        data = state.to_dict()
        assert data["current_phase"] == "init"

    def test_from_dict(self) -> None:
        """should deserialize from dictionary."""
        now = datetime.now(UTC)
        data = {
            "current_phase": "plan",
            "phase_results": {},
            "started_at": now.isoformat(),
            "last_updated": now.isoformat(),
            "context": {},
        }
        state = OrchestratorState.from_dict(data)
        assert state.current_phase == Phase.PLAN


class TestLifecycleOrchestrator:
    """Tests for LifecycleOrchestrator service."""

    def test_creation(self, tmp_path: Path) -> None:
        """LifecycleOrchestrator should be creatable."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        assert orchestrator.repo_root == tmp_path

    def test_custom_state_path(self, tmp_path: Path) -> None:
        """should accept custom state path."""
        state_path = tmp_path / "custom" / "state.json"
        orchestrator = LifecycleOrchestrator(
            repo_root=tmp_path,
            state_path=state_path,
        )
        assert orchestrator.state_path == state_path

    def test_start(self, tmp_path: Path) -> None:
        """should start orchestration."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        state = orchestrator.start({"project": "test"})
        assert state.current_phase == Phase.INIT
        assert state.context["project"] == "test"

    def test_start_saves_state(self, tmp_path: Path) -> None:
        """should save state on start."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        orchestrator.start()
        assert orchestrator.state_path.exists()

    def test_register_handler(self, tmp_path: Path) -> None:
        """should register phase handlers."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)

        def plan_handler(ctx: dict[str, Any]) -> PhaseResult:
            return PhaseResult(
                phase=Phase.PLAN,
                status=PhaseStatus.COMPLETED,
                started_at=datetime.now(UTC),
                artifacts_created=["project-plan"],
            )

        orchestrator.register_handler(Phase.PLAN, plan_handler)
        assert Phase.PLAN in orchestrator._handlers

    def test_register_hook(self, tmp_path: Path) -> None:
        """should register hooks."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        hook_called = []

        def pre_hook(phase: Phase, result: PhaseResult) -> None:
            hook_called.append(("pre", phase))

        orchestrator.register_hook("pre", pre_hook)
        assert len(orchestrator._hooks["pre"]) == 1

    def test_execute_phase(self, tmp_path: Path) -> None:
        """should execute a phase."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        orchestrator.start()

        result = orchestrator.execute_phase(Phase.INIT)
        assert result.phase == Phase.INIT
        assert result.status == PhaseStatus.COMPLETED

    def test_execute_phase_with_handler(self, tmp_path: Path) -> None:
        """should use registered handler."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)

        def custom_handler(ctx: dict[str, Any]) -> PhaseResult:
            return PhaseResult(
                phase=Phase.PLAN,
                status=PhaseStatus.COMPLETED,
                started_at=datetime.now(UTC),
                artifacts_created=["custom-artifact"],
            )

        orchestrator.register_handler(Phase.PLAN, custom_handler)
        orchestrator.start()

        result = orchestrator.execute_phase(Phase.PLAN)
        assert "custom-artifact" in result.artifacts_created

    def test_execute_phase_handler_failure(self, tmp_path: Path) -> None:
        """should handle handler failures."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)

        def failing_handler(ctx: dict[str, Any]) -> PhaseResult:
            raise ValueError("Handler failed")

        orchestrator.register_handler(Phase.PLAN, failing_handler)
        orchestrator.start()

        result = orchestrator.execute_phase(Phase.PLAN)
        assert result.status == PhaseStatus.FAILED
        assert "failed" in result.error.lower()

    def test_advance(self, tmp_path: Path) -> None:
        """should advance to next phase."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        orchestrator.start()

        result = orchestrator.advance()
        assert result is not None
        assert result.phase == Phase.PLAN

    def test_advance_at_end(self, tmp_path: Path) -> None:
        """should return None at end."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        state = orchestrator.start()
        state._state = orchestrator._state
        orchestrator._state.current_phase = Phase.COMPLETE

        result = orchestrator.advance()
        assert result is None

    def test_run_to_phase(self, tmp_path: Path) -> None:
        """should run to specified phase."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        orchestrator.start()

        results = orchestrator.run_to_phase(Phase.TEST)
        assert len(results) == 4  # INIT, PLAN, SCAFFOLD, TEST
        assert all(r.status == PhaseStatus.COMPLETED for r in results)

    def test_run_to_phase_stops_on_failure(self, tmp_path: Path) -> None:
        """should stop on failure."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)

        def failing_handler(ctx: dict[str, Any]) -> PhaseResult:
            raise ValueError("Planned failure")

        orchestrator.register_handler(Phase.SCAFFOLD, failing_handler)
        orchestrator.start()

        results = orchestrator.run_to_phase(Phase.TEST)
        # Should stop after SCAFFOLD fails
        assert any(r.status == PhaseStatus.FAILED for r in results)

    def test_skip_phase(self, tmp_path: Path) -> None:
        """should skip a phase."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        orchestrator.start()

        result = orchestrator.skip_phase(Phase.REFACTOR, "Not needed")
        assert result.status == PhaseStatus.SKIPPED
        assert result.error == "Not needed"

    def test_get_state(self, tmp_path: Path) -> None:
        """should get current state."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        assert orchestrator.get_state() is None

        orchestrator.start()
        assert orchestrator.get_state() is not None

    def test_get_phase_result(self, tmp_path: Path) -> None:
        """should get phase result."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        orchestrator.start()
        orchestrator.execute_phase(Phase.INIT)

        result = orchestrator.get_phase_result(Phase.INIT)
        assert result is not None
        assert result.phase == Phase.INIT

    def test_is_phase_complete(self, tmp_path: Path) -> None:
        """should check phase completion."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        orchestrator.start()

        assert orchestrator.is_phase_complete(Phase.INIT) is False
        orchestrator.execute_phase(Phase.INIT)
        assert orchestrator.is_phase_complete(Phase.INIT) is True

    def test_reset(self, tmp_path: Path) -> None:
        """should reset state."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        orchestrator.start()
        orchestrator.execute_phase(Phase.INIT)

        orchestrator.reset()
        assert orchestrator.get_state() is None
        assert not orchestrator.state_path.exists()

    def test_get_progress(self, tmp_path: Path) -> None:
        """should get progress."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)

        # Not started
        progress = orchestrator.get_progress()
        assert progress["status"] == "not_started"

        # In progress
        orchestrator.start()
        orchestrator.execute_phase(Phase.INIT)
        orchestrator.execute_phase(Phase.PLAN)

        progress = orchestrator.get_progress()
        assert progress["status"] == "in_progress"
        assert progress["completed_phases"] == 2

    def test_resume(self, tmp_path: Path) -> None:
        """should resume from saved state."""
        # First orchestrator
        orch1 = LifecycleOrchestrator(repo_root=tmp_path)
        orch1.start({"key": "value"})
        orch1.execute_phase(Phase.INIT)
        orch1.execute_phase(Phase.PLAN)

        # Second orchestrator - should load state
        orch2 = LifecycleOrchestrator(repo_root=tmp_path)
        state = orch2.resume()

        assert state is not None
        assert state.context["key"] == "value"
        assert orch2.is_phase_complete(Phase.INIT)
        assert orch2.is_phase_complete(Phase.PLAN)

    def test_hooks_execution(self, tmp_path: Path) -> None:
        """should execute hooks."""
        orchestrator = LifecycleOrchestrator(repo_root=tmp_path)
        hook_calls: list[str] = []

        def pre_hook(phase: Phase, result: PhaseResult) -> None:
            hook_calls.append(f"pre-{phase.value}")

        def post_hook(phase: Phase, result: PhaseResult) -> None:
            hook_calls.append(f"post-{phase.value}")

        orchestrator.register_hook("pre", pre_hook)
        orchestrator.register_hook("post", post_hook)
        orchestrator.start()
        orchestrator.execute_phase(Phase.INIT)

        assert "pre-init" in hook_calls
        assert "post-init" in hook_calls
