"""Tests for InvariantChecker."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from rice_factor.adapters.validators.invariant_checker import InvariantChecker
from rice_factor.domain.artifacts.validation_types import ValidationContext


@pytest.fixture
def checker() -> InvariantChecker:
    """Create an InvariantChecker instance."""
    return InvariantChecker()


@pytest.fixture
def context() -> ValidationContext:
    """Create a validation context."""
    return ValidationContext(
        repo_root=Path("/test/repo"),
        language="python",
        config={},
    )


def create_artifact(
    artifacts_dir: Path,
    artifact_type: str,
    status: str = "draft",
    depends_on: list[str] | None = None,
) -> str:
    """Create a test artifact file and return its ID."""
    artifact_id = str(uuid4())
    type_dir = artifacts_dir / f"{artifact_type}s"
    type_dir.mkdir(parents=True, exist_ok=True)

    artifact_data = {
        "id": artifact_id,
        "artifact_type": artifact_type.replace("_", ""),
        "status": status,
        "depends_on": depends_on or [],
    }

    artifact_file = type_dir / f"{artifact_id}.json"
    artifact_file.write_text(json.dumps(artifact_data))
    return artifact_id


def create_approval(artifacts_dir: Path, artifact_id: str) -> None:
    """Create an approval record for an artifact."""
    meta_dir = artifacts_dir / "_meta"
    meta_dir.mkdir(parents=True, exist_ok=True)

    approvals_file = meta_dir / "approvals.json"
    data = (
        json.loads(approvals_file.read_text())
        if approvals_file.exists()
        else {"approvals": {}}
    )

    data["approvals"][artifact_id] = {
        "approved_at": "2024-01-01T00:00:00Z",
        "approved_by": "test",
    }

    approvals_file.write_text(json.dumps(data))


class TestInvariantChecker:
    """Tests for InvariantChecker."""

    def test_name_property(self, checker: InvariantChecker) -> None:
        """Test that name returns 'invariant_checker'."""
        assert checker.name == "invariant_checker"

    def test_validate_no_artifacts_dir(
        self, checker: InvariantChecker, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation when artifacts directory doesn't exist."""
        artifacts_dir = tmp_path / "artifacts"
        # Don't create the directory

        result = checker.validate(artifacts_dir, context)

        assert result.passed
        assert result.status == "passed"
        assert result.validator == "invariant_checker"

    def test_validate_empty_artifacts_dir(
        self, checker: InvariantChecker, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation with empty artifacts directory."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        result = checker.validate(artifacts_dir, context)

        assert result.passed

    def test_validate_all_invariants_pass(
        self, checker: InvariantChecker, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test validation when all invariants pass."""
        artifacts_dir = tmp_path / "artifacts"

        # Create a valid draft artifact with no dependencies
        create_artifact(artifacts_dir, "project_plan", status="draft")

        result = checker.validate(artifacts_dir, context)

        assert result.passed


class TestTestPlanLockCheck:
    """Tests for TestPlan lock checking."""

    @pytest.fixture
    def checker(self) -> InvariantChecker:
        """Create checker."""
        return InvariantChecker()

    def test_testplan_not_locked_no_impl(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that unlocked TestPlan is OK if no implementation exists."""
        artifacts_dir = tmp_path / "artifacts"
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={},
        )

        # Create draft TestPlan but no implementation plans
        create_artifact(artifacts_dir, "test_plan", status="draft")

        result = checker.validate(artifacts_dir, context)

        # Should pass - no implementation yet
        assert result.passed

    def test_testplan_not_locked_with_impl(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that unlocked TestPlan fails if implementation exists."""
        artifacts_dir = tmp_path / "artifacts"
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={},
        )

        # Create draft TestPlan AND implementation plan
        create_artifact(artifacts_dir, "test_plan", status="draft")
        create_artifact(artifacts_dir, "implementation_plan", status="draft")

        result = checker.validate(artifacts_dir, context)

        # Should fail - TestPlan must be locked before implementation
        assert result.failed
        assert any("locked" in e.lower() for e in result.errors)

    def test_testplan_locked_with_impl(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that locked TestPlan passes with implementation."""
        artifacts_dir = tmp_path / "artifacts"
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={},
        )

        # Create locked TestPlan AND implementation plan
        test_plan_id = create_artifact(artifacts_dir, "test_plan", status="locked")
        create_approval(artifacts_dir, test_plan_id)
        create_artifact(artifacts_dir, "implementation_plan", status="draft")

        result = checker.validate(artifacts_dir, context)

        # Should pass - TestPlan is locked
        assert result.passed

    def test_skip_testplan_lock_check(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that TestPlan lock check can be skipped via config."""
        artifacts_dir = tmp_path / "artifacts"
        context = ValidationContext(
            repo_root=tmp_path,
            language="python",
            config={"skip_testplan_lock_check": True},
        )

        # Create draft TestPlan AND implementation plan
        create_artifact(artifacts_dir, "test_plan", status="draft")
        create_artifact(artifacts_dir, "implementation_plan", status="draft")

        result = checker.validate(artifacts_dir, context)

        # Should pass - check is skipped
        assert result.passed


class TestStatusTransitions:
    """Tests for status transition checking."""

    @pytest.fixture
    def checker(self) -> InvariantChecker:
        """Create checker."""
        return InvariantChecker()

    def test_valid_status_draft(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that draft status is valid."""
        artifacts_dir = tmp_path / "artifacts"

        create_artifact(artifacts_dir, "project_plan", status="draft")

        violations = checker.check_status_transitions(artifacts_dir)
        assert len(violations) == 0

    def test_valid_status_approved(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that approved status is valid."""
        artifacts_dir = tmp_path / "artifacts"

        create_artifact(artifacts_dir, "project_plan", status="approved")

        violations = checker.check_status_transitions(artifacts_dir)
        assert len(violations) == 0

    def test_valid_status_locked(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that locked status is valid."""
        artifacts_dir = tmp_path / "artifacts"

        create_artifact(artifacts_dir, "test_plan", status="locked")

        violations = checker.check_status_transitions(artifacts_dir)
        assert len(violations) == 0

    def test_invalid_status(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that invalid status is caught."""
        artifacts_dir = tmp_path / "artifacts"

        # Create artifact with invalid status
        artifact_id = str(uuid4())
        type_dir = artifacts_dir / "project_plans"
        type_dir.mkdir(parents=True, exist_ok=True)

        artifact_data = {
            "id": artifact_id,
            "status": "invalid_status",
        }
        artifact_file = type_dir / f"{artifact_id}.json"
        artifact_file.write_text(json.dumps(artifact_data))

        violations = checker.check_status_transitions(artifacts_dir)
        assert len(violations) == 1
        assert "invalid_status" in violations[0].lower()


class TestApprovalChain:
    """Tests for approval chain checking."""

    @pytest.fixture
    def checker(self) -> InvariantChecker:
        """Create checker."""
        return InvariantChecker()

    def test_draft_no_approval_ok(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that draft artifacts don't need approval."""
        artifacts_dir = tmp_path / "artifacts"

        create_artifact(artifacts_dir, "project_plan", status="draft")

        violations = checker.check_approval_chain(artifacts_dir)
        assert len(violations) == 0

    def test_approved_with_approval_ok(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that approved artifacts with approval records pass."""
        artifacts_dir = tmp_path / "artifacts"

        artifact_id = create_artifact(
            artifacts_dir, "project_plan", status="approved"
        )
        create_approval(artifacts_dir, artifact_id)

        violations = checker.check_approval_chain(artifacts_dir)
        assert len(violations) == 0

    def test_approved_without_approval_fails(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that approved artifacts without approval records fail."""
        artifacts_dir = tmp_path / "artifacts"

        artifact_id = create_artifact(
            artifacts_dir, "project_plan", status="approved"
        )
        # Don't create approval record

        violations = checker.check_approval_chain(artifacts_dir)
        assert len(violations) == 1
        assert artifact_id in violations[0]
        assert "no approval record" in violations[0].lower()

    def test_locked_without_approval_fails(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that locked artifacts without approval records fail."""
        artifacts_dir = tmp_path / "artifacts"

        artifact_id = create_artifact(artifacts_dir, "test_plan", status="locked")
        # Don't create approval record

        violations = checker.check_approval_chain(artifacts_dir)
        assert len(violations) == 1
        assert artifact_id in violations[0]


class TestDependencyChecking:
    """Tests for dependency checking."""

    @pytest.fixture
    def checker(self) -> InvariantChecker:
        """Create checker."""
        return InvariantChecker()

    def test_no_dependencies_ok(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that artifacts without dependencies pass."""
        artifacts_dir = tmp_path / "artifacts"

        create_artifact(artifacts_dir, "project_plan", status="draft")

        violations = checker.check_dependencies(artifacts_dir)
        assert len(violations) == 0

    def test_existing_dependency_ok(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that existing dependencies pass."""
        artifacts_dir = tmp_path / "artifacts"

        dep_id = create_artifact(artifacts_dir, "project_plan", status="approved")
        create_artifact(
            artifacts_dir,
            "architecture_plan",
            status="draft",
            depends_on=[dep_id],
        )

        violations = checker.check_dependencies(artifacts_dir)
        assert len(violations) == 0

    def test_missing_dependency_fails(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test that missing dependencies fail."""
        artifacts_dir = tmp_path / "artifacts"

        missing_id = str(uuid4())
        artifact_id = create_artifact(
            artifacts_dir,
            "architecture_plan",
            status="draft",
            depends_on=[missing_id],
        )

        violations = checker.check_dependencies(artifacts_dir)
        assert len(violations) == 1
        assert missing_id in violations[0]
        assert artifact_id in violations[0]


class TestSingleInvariantCheck:
    """Tests for check_single_invariant method."""

    @pytest.fixture
    def checker(self) -> InvariantChecker:
        """Create checker."""
        return InvariantChecker()

    def test_check_single_testplan_lock(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test checking single invariant: testplan_lock."""
        artifacts_dir = tmp_path / "artifacts"
        context = ValidationContext(repo_root=tmp_path, language="python", config={})

        violations = checker.check_single_invariant(
            "testplan_lock", artifacts_dir, context
        )
        assert isinstance(violations, list)

    def test_check_single_status_transitions(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test checking single invariant: status_transitions."""
        artifacts_dir = tmp_path / "artifacts"
        context = ValidationContext(repo_root=tmp_path, language="python", config={})

        violations = checker.check_single_invariant(
            "status_transitions", artifacts_dir, context
        )
        assert isinstance(violations, list)

    def test_check_single_unknown_invariant(
        self, checker: InvariantChecker, tmp_path: Path
    ) -> None:
        """Test checking unknown invariant raises error."""
        artifacts_dir = tmp_path / "artifacts"
        context = ValidationContext(repo_root=tmp_path, language="python", config={})

        with pytest.raises(ValueError) as exc_info:
            checker.check_single_invariant("unknown", artifacts_dir, context)

        assert "unknown" in str(exc_info.value).lower()
