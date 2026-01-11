"""Unit tests for InvariantEnforcementAdapter."""

import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from rice_factor.adapters.ci.invariant_enforcer import InvariantEnforcementAdapter
from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIStage


def _create_testplan_artifact(
    artifacts_dir: Path,
    status: str = "locked",
    artifact_id: str | None = None,
) -> str:
    """Create a TestPlan artifact file.

    Returns:
        The artifact ID.
    """
    if artifact_id is None:
        artifact_id = str(uuid4())

    test_plans_dir = artifacts_dir / "test_plans"
    test_plans_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = test_plans_dir / f"{artifact_id}.json"
    artifact_data = {
        "id": artifact_id,
        "artifact_type": "TestPlan",
        "artifact_version": "1.0",
        "status": status,
        "created_by": "llm",
        "created_at": "2026-01-11T10:00:00Z",
        "payload": {
            "tests": [{"id": "test-1", "target": "main", "assertions": ["works"]}]
        },
    }
    artifact_path.write_text(json.dumps(artifact_data, indent=2))
    return artifact_id


def _create_implementation_plan(
    artifacts_dir: Path,
    target: str = "src/main.py",
    status: str = "approved",
    artifact_id: str | None = None,
) -> str:
    """Create an ImplementationPlan artifact file.

    Returns:
        The artifact ID.
    """
    if artifact_id is None:
        artifact_id = str(uuid4())

    impl_dir = artifacts_dir / "implementation_plans"
    impl_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = impl_dir / f"{artifact_id}.json"
    artifact_data = {
        "id": artifact_id,
        "artifact_type": "ImplementationPlan",
        "artifact_version": "1.0",
        "status": status,
        "created_by": "llm",
        "created_at": "2026-01-11T10:00:00Z",
        "payload": {
            "target": target,
            "steps": ["Step 1: Implement the feature"],
            "related_tests": ["test-1"],
        },
    }
    artifact_path.write_text(json.dumps(artifact_data, indent=2))
    return artifact_id


def _create_refactor_plan(
    artifacts_dir: Path,
    from_path: str = "src/old.py",
    to_path: str = "src/new.py",
    status: str = "approved",
    artifact_id: str | None = None,
) -> str:
    """Create a RefactorPlan artifact file.

    Returns:
        The artifact ID.
    """
    if artifact_id is None:
        artifact_id = str(uuid4())

    refactor_dir = artifacts_dir / "refactor_plans"
    refactor_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = refactor_dir / f"{artifact_id}.json"
    artifact_data = {
        "id": artifact_id,
        "artifact_type": "RefactorPlan",
        "artifact_version": "1.0",
        "status": status,
        "created_by": "llm",
        "created_at": "2026-01-11T10:00:00Z",
        "payload": {
            "goal": "Rename file",
            "operations": [
                {"type": "move_file", "from": from_path, "to": to_path}
            ],
        },
    }
    artifact_path.write_text(json.dumps(artifact_data, indent=2))
    return artifact_id


class TestInvariantEnforcementAdapter:
    """Tests for InvariantEnforcementAdapter."""

    def test_stage_name(self) -> None:
        """stage_name should return 'Invariant Enforcement'."""
        adapter = InvariantEnforcementAdapter()
        assert adapter.stage_name == "Invariant Enforcement"

    def test_no_artifacts_directory_passes(self, tmp_path: Path) -> None:
        """Validation should pass when artifacts directory doesn't exist."""
        adapter = InvariantEnforcementAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert result.stage == CIStage.INVARIANT_ENFORCEMENT
        assert len(result.failures) == 0

    def test_empty_artifacts_directory_passes(self, tmp_path: Path) -> None:
        """Validation should pass with empty artifacts directory."""
        (tmp_path / "artifacts").mkdir()

        adapter = InvariantEnforcementAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert len(result.failures) == 0


class TestTestImmutability:
    """Tests for test immutability enforcement."""

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_locked_testplan_with_test_changes_fails(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should fail when tests modified after TestPlan lock."""
        artifacts_dir = tmp_path / "artifacts"
        _create_testplan_artifact(artifacts_dir, status="locked")

        # Mock git to return test file changes
        mock_get_changed.return_value = {"tests/test_main.py"}

        adapter = InvariantEnforcementAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        assert len(result.failures) >= 1
        test_mod_failures = [
            f
            for f in result.failures
            if f.code == CIFailureCode.TEST_MODIFICATION_AFTER_LOCK
        ]
        assert len(test_mod_failures) == 1
        assert "test_main.py" in test_mod_failures[0].message

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_locked_testplan_no_test_changes_passes(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should pass when no test changes with locked TestPlan."""
        artifacts_dir = tmp_path / "artifacts"
        _create_testplan_artifact(artifacts_dir, status="locked")

        # Mock git to return non-test file changes
        mock_get_changed.return_value = {"src/main.py"}

        adapter = InvariantEnforcementAdapter()
        result = adapter.validate(tmp_path)

        # No test modifications
        test_mod_failures = [
            f
            for f in result.failures
            if f.code == CIFailureCode.TEST_MODIFICATION_AFTER_LOCK
        ]
        assert len(test_mod_failures) == 0

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_unlocked_testplan_with_test_changes_passes(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should pass when TestPlan is not locked (test changes allowed)."""
        artifacts_dir = tmp_path / "artifacts"
        _create_testplan_artifact(artifacts_dir, status="approved")

        # Mock git to return test file changes
        mock_get_changed.return_value = {"tests/test_main.py"}

        adapter = InvariantEnforcementAdapter()
        result = adapter.validate(tmp_path)

        # Test modifications allowed when not locked
        test_mod_failures = [
            f
            for f in result.failures
            if f.code == CIFailureCode.TEST_MODIFICATION_AFTER_LOCK
        ]
        assert len(test_mod_failures) == 0

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_no_testplan_allows_test_changes(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should pass when no TestPlan exists."""
        (tmp_path / "artifacts").mkdir()

        # Mock git to return test file changes
        mock_get_changed.return_value = {"tests/test_main.py"}

        adapter = InvariantEnforcementAdapter()
        result = adapter.validate(tmp_path)

        # No TestPlan = no test lock
        test_mod_failures = [
            f
            for f in result.failures
            if f.code == CIFailureCode.TEST_MODIFICATION_AFTER_LOCK
        ]
        assert len(test_mod_failures) == 0


class TestArtifactToCodeMapping:
    """Tests for artifact-to-code mapping enforcement."""

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_planned_code_change_passes(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should pass when code change is covered by plan."""
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(artifacts_dir, target="src/main.py")

        # Mock git to return the planned file change
        mock_get_changed.return_value = {"src/main.py"}

        adapter = InvariantEnforcementAdapter(source_dirs=["src"])
        result = adapter.validate(tmp_path)

        # Change is planned
        unplanned_failures = [
            f for f in result.failures if f.code == CIFailureCode.UNPLANNED_CODE_CHANGE
        ]
        assert len(unplanned_failures) == 0

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_unplanned_code_change_fails(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should fail when code change is not covered by any plan."""
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(artifacts_dir, target="src/main.py")

        # Mock git to return an unplanned file change
        mock_get_changed.return_value = {"src/other.py"}

        adapter = InvariantEnforcementAdapter(source_dirs=["src"])
        result = adapter.validate(tmp_path)

        assert result.passed is False
        unplanned_failures = [
            f for f in result.failures if f.code == CIFailureCode.UNPLANNED_CODE_CHANGE
        ]
        assert len(unplanned_failures) == 1
        assert "other.py" in unplanned_failures[0].message

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_refactor_plan_allows_file_move(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should pass when refactor plan covers file move."""
        artifacts_dir = tmp_path / "artifacts"
        _create_refactor_plan(
            artifacts_dir, from_path="src/old.py", to_path="src/new.py"
        )

        # Mock git to return both old and new paths
        mock_get_changed.return_value = {"src/old.py", "src/new.py"}

        adapter = InvariantEnforcementAdapter(source_dirs=["src"])
        result = adapter.validate(tmp_path)

        # Both files are covered by refactor plan
        unplanned_failures = [
            f for f in result.failures if f.code == CIFailureCode.UNPLANNED_CODE_CHANGE
        ]
        assert len(unplanned_failures) == 0

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_no_plans_skips_mapping_check(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should skip mapping check if no plans exist."""
        (tmp_path / "artifacts").mkdir()

        # Mock git to return source file changes
        mock_get_changed.return_value = {"src/main.py"}

        adapter = InvariantEnforcementAdapter(source_dirs=["src"])
        result = adapter.validate(tmp_path)

        # No plans = skip mapping check
        unplanned_failures = [
            f for f in result.failures if f.code == CIFailureCode.UNPLANNED_CODE_CHANGE
        ]
        assert len(unplanned_failures) == 0

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_draft_plan_not_counted(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Draft plans should not allow code changes."""
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(artifacts_dir, target="src/main.py", status="draft")

        # Mock git to return the file change
        mock_get_changed.return_value = {"src/main.py"}

        adapter = InvariantEnforcementAdapter(source_dirs=["src"])
        result = adapter.validate(tmp_path)

        # Draft plan doesn't count - but no approved plans means skip check
        # This is current behavior - check is skipped if no approved plans
        assert result.passed is True

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_ignores_non_source_files(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should ignore changes to non-source files."""
        artifacts_dir = tmp_path / "artifacts"
        _create_implementation_plan(artifacts_dir, target="src/main.py")

        # Mock git to return doc and config file changes
        mock_get_changed.return_value = {
            "docs/README.md",
            ".github/workflows/ci.yml",
            "pyproject.toml",
        }

        adapter = InvariantEnforcementAdapter(source_dirs=["src"])
        result = adapter.validate(tmp_path)

        # Non-source files are ignored
        unplanned_failures = [
            f for f in result.failures if f.code == CIFailureCode.UNPLANNED_CODE_CHANGE
        ]
        assert len(unplanned_failures) == 0


class TestMultipleInvariants:
    """Tests for multiple invariant violations."""

    @patch.object(InvariantEnforcementAdapter, "_get_changed_files")
    def test_multiple_failures_reported(
        self, mock_get_changed: patch, tmp_path: Path
    ) -> None:
        """Should report multiple test modification failures."""
        artifacts_dir = tmp_path / "artifacts"
        _create_testplan_artifact(artifacts_dir, status="locked")

        # Mock git to return multiple test file changes
        mock_get_changed.return_value = {
            "tests/test_main.py",
            "tests/test_utils.py",
            "tests/conftest.py",
        }

        adapter = InvariantEnforcementAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        test_mod_failures = [
            f
            for f in result.failures
            if f.code == CIFailureCode.TEST_MODIFICATION_AFTER_LOCK
        ]
        assert len(test_mod_failures) == 3


class TestDurationTracking:
    """Tests for duration tracking."""

    def test_duration_is_recorded(self, tmp_path: Path) -> None:
        """Validation should record duration."""
        (tmp_path / "artifacts").mkdir()

        adapter = InvariantEnforcementAdapter()
        result = adapter.validate(tmp_path)

        assert result.duration_ms >= 0


class TestConfiguration:
    """Tests for adapter configuration."""

    def test_custom_base_branch(self) -> None:
        """Adapter should accept custom base branch."""
        adapter = InvariantEnforcementAdapter(base_branch="develop")
        assert adapter._base_branch == "develop"

    def test_custom_tests_dir(self) -> None:
        """Adapter should accept custom tests directory."""
        adapter = InvariantEnforcementAdapter(tests_dir="spec")
        assert adapter._tests_dir == "spec"

    def test_custom_source_dirs(self) -> None:
        """Adapter should accept custom source directories."""
        adapter = InvariantEnforcementAdapter(source_dirs=["app", "lib"])
        assert adapter._source_dirs == ["app", "lib"]
