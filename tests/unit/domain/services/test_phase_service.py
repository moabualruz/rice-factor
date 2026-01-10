"""Unit tests for Phase Service."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.failures import MissingPrerequisiteError, PhaseError
from rice_factor.domain.services.phase_service import (
    COMMAND_PHASES,
    PHASE_DESCRIPTIONS,
    Phase,
    PhaseService,
)


class TestPhaseEnum:
    """Tests for Phase enum."""

    def test_phase_values(self) -> None:
        """Phase enum should have expected values."""
        assert Phase.UNINIT.value == "uninit"
        assert Phase.INIT.value == "init"
        assert Phase.PLANNING.value == "planning"
        assert Phase.SCAFFOLDED.value == "scaffolded"
        assert Phase.TEST_LOCKED.value == "test_locked"
        assert Phase.IMPLEMENTING.value == "implementing"

    def test_phase_order(self) -> None:
        """Phases should be in correct order."""
        phases = list(Phase)
        assert phases[0] == Phase.UNINIT
        assert phases[1] == Phase.INIT
        assert phases[2] == Phase.PLANNING
        assert phases[3] == Phase.SCAFFOLDED
        assert phases[4] == Phase.TEST_LOCKED
        assert phases[5] == Phase.IMPLEMENTING


class TestCommandPhases:
    """Tests for COMMAND_PHASES mapping."""

    def test_init_requires_uninit(self) -> None:
        """init command should require UNINIT phase."""
        assert COMMAND_PHASES["init"] == Phase.UNINIT

    def test_plan_project_requires_init(self) -> None:
        """plan project command should require INIT phase."""
        assert COMMAND_PHASES["plan project"] == Phase.INIT

    def test_scaffold_requires_planning(self) -> None:
        """scaffold command should require PLANNING phase."""
        assert COMMAND_PHASES["scaffold"] == Phase.PLANNING

    def test_impl_requires_test_locked(self) -> None:
        """impl command should require TEST_LOCKED phase."""
        assert COMMAND_PHASES["impl"] == Phase.TEST_LOCKED

    def test_approve_requires_init(self) -> None:
        """approve command should work at any phase after init."""
        assert COMMAND_PHASES["approve"] == Phase.INIT


class TestPhaseDescriptions:
    """Tests for PHASE_DESCRIPTIONS mapping."""

    def test_all_phases_have_descriptions(self) -> None:
        """All phases should have descriptions."""
        for phase in Phase:
            assert phase in PHASE_DESCRIPTIONS
            assert len(PHASE_DESCRIPTIONS[phase]) > 0


class TestPhaseServiceInit:
    """Tests for PhaseService initialization."""

    def test_init_with_project_root(self, tmp_path: Path) -> None:
        """PhaseService should accept project root."""
        service = PhaseService(project_root=tmp_path)
        assert service.project_root == tmp_path

    def test_init_with_artifact_service(self, tmp_path: Path) -> None:
        """PhaseService should accept artifact service."""
        mock_service = MagicMock()
        service = PhaseService(project_root=tmp_path, artifact_service=mock_service)
        assert service.artifact_service == mock_service


class TestIsInitialized:
    """Tests for is_initialized() method."""

    def test_returns_false_when_no_project_dir(self, tmp_path: Path) -> None:
        """is_initialized() should return False when .project/ doesn't exist."""
        service = PhaseService(project_root=tmp_path)
        assert service.is_initialized() is False

    def test_returns_true_when_project_dir_exists(self, tmp_path: Path) -> None:
        """is_initialized() should return True when .project/ exists."""
        (tmp_path / ".project").mkdir()
        service = PhaseService(project_root=tmp_path)
        assert service.is_initialized() is True

    def test_returns_false_when_project_is_file(self, tmp_path: Path) -> None:
        """is_initialized() should return False when .project is a file."""
        (tmp_path / ".project").write_text("not a directory")
        service = PhaseService(project_root=tmp_path)
        assert service.is_initialized() is False


class TestGetCurrentPhase:
    """Tests for get_current_phase() method."""

    def test_returns_uninit_when_no_project_dir(self, tmp_path: Path) -> None:
        """get_current_phase() should return UNINIT when not initialized."""
        service = PhaseService(project_root=tmp_path)
        assert service.get_current_phase() == Phase.UNINIT

    def test_returns_init_when_project_dir_exists_no_service(
        self, tmp_path: Path
    ) -> None:
        """get_current_phase() should return INIT when initialized but no service."""
        (tmp_path / ".project").mkdir()
        service = PhaseService(project_root=tmp_path)
        assert service.get_current_phase() == Phase.INIT

    def test_returns_init_when_no_artifacts(self, tmp_path: Path) -> None:
        """get_current_phase() should return INIT when no artifacts exist."""
        (tmp_path / ".project").mkdir()
        mock_service = MagicMock()
        mock_service.storage.list_by_type.return_value = []
        service = PhaseService(project_root=tmp_path, artifact_service=mock_service)
        assert service.get_current_phase() == Phase.INIT

    def test_returns_planning_when_project_plan_approved(self, tmp_path: Path) -> None:
        """get_current_phase() should return PLANNING when ProjectPlan approved."""
        (tmp_path / ".project").mkdir()
        mock_artifact = MagicMock()
        mock_artifact.status = ArtifactStatus.APPROVED
        mock_service = MagicMock()

        def list_by_type(artifact_type: ArtifactType) -> list:
            if artifact_type == ArtifactType.PROJECT_PLAN:
                return [mock_artifact]
            return []

        mock_service.storage.list_by_type.side_effect = list_by_type
        service = PhaseService(project_root=tmp_path, artifact_service=mock_service)
        assert service.get_current_phase() == Phase.PLANNING

    def test_returns_scaffolded_when_scaffold_plan_approved(
        self, tmp_path: Path
    ) -> None:
        """get_current_phase() should return SCAFFOLDED when ScaffoldPlan approved."""
        (tmp_path / ".project").mkdir()
        mock_artifact = MagicMock()
        mock_artifact.status = ArtifactStatus.APPROVED
        mock_service = MagicMock()

        def list_by_type(artifact_type: ArtifactType) -> list:
            if artifact_type == ArtifactType.SCAFFOLD_PLAN:
                return [mock_artifact]
            if artifact_type == ArtifactType.PROJECT_PLAN:
                return [mock_artifact]
            return []

        mock_service.storage.list_by_type.side_effect = list_by_type
        service = PhaseService(project_root=tmp_path, artifact_service=mock_service)
        assert service.get_current_phase() == Phase.SCAFFOLDED

    def test_returns_test_locked_when_test_plan_locked(self, tmp_path: Path) -> None:
        """get_current_phase() should return TEST_LOCKED when TestPlan locked."""
        (tmp_path / ".project").mkdir()
        mock_locked = MagicMock()
        mock_locked.status = ArtifactStatus.LOCKED
        mock_approved = MagicMock()
        mock_approved.status = ArtifactStatus.APPROVED
        mock_service = MagicMock()

        def list_by_type(artifact_type: ArtifactType) -> list:
            if artifact_type == ArtifactType.TEST_PLAN:
                return [mock_locked]
            if artifact_type in (
                ArtifactType.SCAFFOLD_PLAN,
                ArtifactType.PROJECT_PLAN,
            ):
                return [mock_approved]
            return []

        mock_service.storage.list_by_type.side_effect = list_by_type
        service = PhaseService(project_root=tmp_path, artifact_service=mock_service)
        assert service.get_current_phase() == Phase.TEST_LOCKED


class TestCanExecute:
    """Tests for can_execute() method."""

    def test_init_allowed_in_uninit(self, tmp_path: Path) -> None:
        """init should be allowed in UNINIT phase."""
        service = PhaseService(project_root=tmp_path)
        assert service.can_execute("init") is True

    def test_plan_project_not_allowed_in_uninit(self, tmp_path: Path) -> None:
        """plan project should not be allowed in UNINIT phase."""
        service = PhaseService(project_root=tmp_path)
        assert service.can_execute("plan project") is False

    def test_plan_project_allowed_in_init(self, tmp_path: Path) -> None:
        """plan project should be allowed in INIT phase."""
        (tmp_path / ".project").mkdir()
        service = PhaseService(project_root=tmp_path)
        assert service.can_execute("plan project") is True

    def test_scaffold_not_allowed_in_init(self, tmp_path: Path) -> None:
        """scaffold should not be allowed in INIT phase."""
        (tmp_path / ".project").mkdir()
        service = PhaseService(project_root=tmp_path)
        assert service.can_execute("scaffold") is False

    def test_impl_not_allowed_in_planning(self, tmp_path: Path) -> None:
        """impl should not be allowed before TEST_LOCKED phase."""
        (tmp_path / ".project").mkdir()
        mock_artifact = MagicMock()
        mock_artifact.status = ArtifactStatus.APPROVED
        mock_service = MagicMock()

        def list_by_type(artifact_type: ArtifactType) -> list:
            if artifact_type == ArtifactType.PROJECT_PLAN:
                return [mock_artifact]
            return []

        mock_service.storage.list_by_type.side_effect = list_by_type
        service = PhaseService(project_root=tmp_path, artifact_service=mock_service)
        assert service.can_execute("impl") is False

    def test_unknown_command_allowed(self, tmp_path: Path) -> None:
        """Unknown commands should be allowed (other validation catches issues)."""
        service = PhaseService(project_root=tmp_path)
        assert service.can_execute("unknown-command") is True


class TestGetBlockingReason:
    """Tests for get_blocking_reason() method."""

    def test_returns_none_when_allowed(self, tmp_path: Path) -> None:
        """get_blocking_reason() should return None when command is allowed."""
        service = PhaseService(project_root=tmp_path)
        assert service.get_blocking_reason("init") is None

    def test_returns_message_when_blocked(self, tmp_path: Path) -> None:
        """get_blocking_reason() should return message when command is blocked."""
        service = PhaseService(project_root=tmp_path)
        reason = service.get_blocking_reason("plan project")
        assert reason is not None
        assert "plan project" in reason
        assert "initialized" in reason.lower() or "init" in reason.lower()


class TestRequirePhase:
    """Tests for require_phase() method."""

    def test_passes_when_allowed(self, tmp_path: Path) -> None:
        """require_phase() should pass when command is allowed."""
        service = PhaseService(project_root=tmp_path)
        # Should not raise
        service.require_phase("init")

    def test_raises_missing_prerequisite_for_uninit(self, tmp_path: Path) -> None:
        """require_phase() should raise MissingPrerequisiteError for non-init in UNINIT."""
        service = PhaseService(project_root=tmp_path)
        with pytest.raises(MissingPrerequisiteError) as exc_info:
            service.require_phase("plan project")
        assert "init" in str(exc_info.value).lower()

    def test_raises_phase_error_when_blocked(self, tmp_path: Path) -> None:
        """require_phase() should raise PhaseError when command is blocked."""
        (tmp_path / ".project").mkdir()
        service = PhaseService(project_root=tmp_path)
        with pytest.raises(PhaseError) as exc_info:
            service.require_phase("scaffold")
        assert exc_info.value.command == "scaffold"
        assert exc_info.value.current_phase == "init"
        assert exc_info.value.required_phase == "planning"

    def test_passes_for_approve_in_init(self, tmp_path: Path) -> None:
        """require_phase() should pass for approve in INIT phase."""
        (tmp_path / ".project").mkdir()
        service = PhaseService(project_root=tmp_path)
        # Should not raise
        service.require_phase("approve")
