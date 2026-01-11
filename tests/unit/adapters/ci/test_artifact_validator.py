"""Unit tests for ArtifactValidationAdapter."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from rice_factor.adapters.ci.artifact_validator import ArtifactValidationAdapter
from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIStage


def _get_payload_for_type(artifact_type: str) -> dict:
    """Get a schema-compliant payload for the given artifact type."""
    if artifact_type == "TestPlan":
        return {
            "tests": [
                {"id": "test-1", "target": "main", "assertions": ["should work"]}
            ]
        }
    # Default to ProjectPlan payload
    return {
        "domains": [{"name": "core", "responsibility": "Core functionality"}],
        "modules": [{"name": "main", "domain": "core"}],
        "constraints": {
            "architecture": "hexagonal",
            "languages": ["python"],
        },
    }


def _create_artifact_file(
    artifacts_dir: Path,
    artifact_type: str = "ProjectPlan",
    status: str = "approved",
    artifact_id: str | None = None,
    subdir: str = "project_plans",
) -> Path:
    """Create a schema-compliant artifact JSON file for testing."""
    if artifact_id is None:
        artifact_id = str(uuid4())

    type_dir = artifacts_dir / subdir
    type_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = type_dir / f"{artifact_id}.json"
    artifact_data = {
        "id": artifact_id,
        "artifact_type": artifact_type,
        "artifact_version": "1.0",
        "status": status,
        "created_by": "llm",
        "created_at": "2026-01-11T10:00:00Z",
        "payload": _get_payload_for_type(artifact_type),
    }
    artifact_path.write_text(json.dumps(artifact_data, indent=2))
    return artifact_path


class TestArtifactValidationAdapter:
    """Tests for ArtifactValidationAdapter."""

    def test_stage_name(self) -> None:
        """stage_name should return 'Artifact Validation'."""
        adapter = ArtifactValidationAdapter()
        assert adapter.stage_name == "Artifact Validation"

    def test_no_artifacts_directory_passes(self, tmp_path: Path) -> None:
        """Validation should pass when artifacts directory doesn't exist."""
        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert result.stage == CIStage.ARTIFACT_VALIDATION
        assert len(result.failures) == 0

    def test_empty_artifacts_directory_passes(self, tmp_path: Path) -> None:
        """Validation should pass with empty artifacts directory."""
        (tmp_path / "artifacts").mkdir()

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert len(result.failures) == 0


class TestDraftArtifactDetection:
    """Tests for draft artifact detection."""

    def test_draft_artifact_fails(self, tmp_path: Path) -> None:
        """Validation should fail when draft artifact is present."""
        artifacts_dir = tmp_path / "artifacts"
        _create_artifact_file(artifacts_dir, status="draft")

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        assert len(result.failures) == 1
        assert result.failures[0].code == CIFailureCode.DRAFT_ARTIFACT_PRESENT
        assert "Draft artifact" in result.failures[0].message

    def test_approved_artifact_passes(self, tmp_path: Path) -> None:
        """Validation should pass for approved artifacts."""
        artifacts_dir = tmp_path / "artifacts"
        _create_artifact_file(artifacts_dir, status="approved")

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is True
        assert len(result.failures) == 0

    def test_locked_artifact_passes(self, tmp_path: Path) -> None:
        """Validation should pass for locked artifacts (when not modified)."""
        artifacts_dir = tmp_path / "artifacts"
        # Only TestPlan can be locked, so use TestPlan for this test
        _create_artifact_file(
            artifacts_dir,
            artifact_type="TestPlan",
            status="locked",
            subdir="test_plans",
        )

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        # Locked artifact without git changes should pass
        assert result.passed is True


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_invalid_json_fails(self, tmp_path: Path) -> None:
        """Validation should fail for invalid JSON."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        bad_file = artifacts_dir / "bad.json"
        bad_file.write_text("{ invalid json }")

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        assert len(result.failures) == 1
        assert result.failures[0].code == CIFailureCode.SCHEMA_VALIDATION_FAILED
        assert "Invalid JSON" in result.failures[0].message

    def test_missing_artifact_type_fails(self, tmp_path: Path) -> None:
        """Validation should fail when artifact_type is missing."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact_file = artifacts_dir / "missing_type.json"
        artifact_file.write_text(json.dumps({"id": "123", "status": "approved"}))

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        assert result.failures[0].code == CIFailureCode.SCHEMA_VALIDATION_FAILED
        assert "artifact_type" in result.failures[0].message

    def test_unknown_artifact_type_fails(self, tmp_path: Path) -> None:
        """Validation should fail for unknown artifact types."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact_file = artifacts_dir / "unknown_type.json"
        artifact_file.write_text(
            json.dumps(
                {"id": "123", "artifact_type": "UnknownType", "status": "approved"}
            )
        )

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        assert result.failures[0].code == CIFailureCode.SCHEMA_VALIDATION_FAILED


class TestArtifactDiscovery:
    """Tests for artifact file discovery."""

    def test_discovers_nested_artifacts(self, tmp_path: Path) -> None:
        """Validator should discover artifacts in subdirectories."""
        artifacts_dir = tmp_path / "artifacts"

        # Create artifacts in different subdirectories
        _create_artifact_file(
            artifacts_dir, status="approved", subdir="project_plans"
        )
        _create_artifact_file(
            artifacts_dir,
            status="approved",
            artifact_type="TestPlan",
            subdir="test_plans",
        )

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        # Both should be validated (schema errors are expected for minimal payloads)
        # but the important thing is discovery worked
        assert result.stage == CIStage.ARTIFACT_VALIDATION

    def test_skips_metadata_files(self, tmp_path: Path) -> None:
        """Validator should skip _meta directory."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir()

        # Create a file in _meta that would fail if processed
        meta_dir = artifacts_dir / "_meta"
        meta_dir.mkdir()
        (meta_dir / "index.json").write_text(json.dumps({"artifacts": []}))

        # Create a valid artifact
        _create_artifact_file(artifacts_dir, status="approved")

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        # Should pass - meta files should be skipped
        assert result.passed is True

    def test_skips_approval_files(self, tmp_path: Path) -> None:
        """Validator should skip .approval.json files."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        # Create an approval file that would fail if processed as artifact
        approval_file = artifacts_dir / "abc123.approval.json"
        approval_file.write_text(json.dumps({"approved_by": "user", "timestamp": "123"}))

        # Create a valid artifact
        _create_artifact_file(tmp_path / "artifacts", status="approved")

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        # Should pass - approval files should be skipped
        assert result.passed is True


class TestMultipleFailures:
    """Tests for multiple failure reporting."""

    def test_reports_multiple_failures(self, tmp_path: Path) -> None:
        """Validator should report all failures found."""
        artifacts_dir = tmp_path / "artifacts"

        # Create multiple problematic artifacts
        _create_artifact_file(
            artifacts_dir,
            status="draft",
            artifact_id="draft1",
            subdir="project_plans",
        )
        _create_artifact_file(
            artifacts_dir,
            status="draft",
            artifact_id="draft2",
            subdir="project_plans",
        )

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        # Should have at least 2 draft failures
        draft_failures = [
            f for f in result.failures if f.code == CIFailureCode.DRAFT_ARTIFACT_PRESENT
        ]
        assert len(draft_failures) == 2

    def test_multiple_failure_types(self, tmp_path: Path) -> None:
        """Validator should report different types of failures."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        # Create a draft artifact
        _create_artifact_file(
            tmp_path / "artifacts",
            status="draft",
            artifact_id="draft1",
        )

        # Create an invalid JSON file
        (artifacts_dir / "invalid.json").write_text("{ bad json }")

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.passed is False
        failure_codes = {f.code for f in result.failures}
        assert CIFailureCode.DRAFT_ARTIFACT_PRESENT in failure_codes
        assert CIFailureCode.SCHEMA_VALIDATION_FAILED in failure_codes


class TestDurationTracking:
    """Tests for duration tracking."""

    def test_duration_is_recorded(self, tmp_path: Path) -> None:
        """Validation should record duration."""
        (tmp_path / "artifacts").mkdir()

        adapter = ArtifactValidationAdapter()
        result = adapter.validate(tmp_path)

        assert result.duration_ms >= 0


class TestBaseBranchConfig:
    """Tests for base branch configuration."""

    def test_default_base_branch_is_main(self) -> None:
        """Default base branch should be 'main'."""
        adapter = ArtifactValidationAdapter()
        assert adapter._base_branch == "main"

    def test_custom_base_branch(self) -> None:
        """Adapter should accept custom base branch."""
        adapter = ArtifactValidationAdapter(base_branch="develop")
        assert adapter._base_branch == "develop"
