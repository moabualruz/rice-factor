"""Unit tests for CI domain models."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIFailure, CIPipelineResult, CIStage, CIStageResult


class TestCIFailure:
    """Tests for CIFailure dataclass."""

    def test_create_failure(self) -> None:
        """CIFailure should be created with required fields."""
        failure = CIFailure(
            code=CIFailureCode.DRAFT_ARTIFACT_PRESENT,
            message="Draft artifact found: project_plan.json",
        )
        assert failure.code == CIFailureCode.DRAFT_ARTIFACT_PRESENT
        assert "Draft artifact" in failure.message
        assert failure.file_path is None
        assert failure.remediation is None

    def test_create_failure_with_optional_fields(self) -> None:
        """CIFailure should accept optional fields."""
        failure = CIFailure(
            code=CIFailureCode.SCHEMA_VALIDATION_FAILED,
            message="Schema validation failed",
            file_path=Path("artifacts/project_plan.json"),
            remediation="Fix the schema errors",
            details={"field": "name", "error": "required"},
        )
        assert failure.file_path == Path("artifacts/project_plan.json")
        assert failure.remediation == "Fix the schema errors"
        assert failure.details == {"field": "name", "error": "required"}

    def test_failure_is_frozen(self) -> None:
        """CIFailure should be immutable."""
        failure = CIFailure(
            code=CIFailureCode.TEST_FAILURE,
            message="Tests failed",
        )
        with pytest.raises(AttributeError):
            failure.message = "new message"  # type: ignore

    def test_to_dict_serialization(self) -> None:
        """to_dict should produce valid dictionary."""
        failure = CIFailure(
            code=CIFailureCode.ARTIFACT_NOT_APPROVED,
            message="Artifact not approved",
            file_path=Path("artifacts/test.json"),
        )
        result = failure.to_dict()

        assert result["code"] == "ARTIFACT_NOT_APPROVED"
        assert result["message"] == "Artifact not approved"
        # Path serialization is platform-dependent
        assert "artifacts" in result["file_path"]
        assert "test.json" in result["file_path"]
        # Should use code's remediation if none provided
        assert result["remediation"] == CIFailureCode.ARTIFACT_NOT_APPROVED.remediation


class TestCIStageResult:
    """Tests for CIStageResult dataclass."""

    def test_create_passing_result(self) -> None:
        """CIStageResult should represent a passing stage."""
        result = CIStageResult(
            stage=CIStage.ARTIFACT_VALIDATION,
            passed=True,
        )
        assert result.stage == CIStage.ARTIFACT_VALIDATION
        assert result.passed is True
        assert len(result.failures) == 0
        assert result.skipped is False

    def test_create_failing_result(self) -> None:
        """CIStageResult should represent a failing stage."""
        failures = [
            CIFailure(
                code=CIFailureCode.DRAFT_ARTIFACT_PRESENT,
                message="Draft found",
            )
        ]
        result = CIStageResult(
            stage=CIStage.ARTIFACT_VALIDATION,
            passed=False,
            failures=failures,
            duration_ms=100.5,
        )
        assert result.passed is False
        assert len(result.failures) == 1
        assert result.duration_ms == 100.5

    def test_create_skipped_result(self) -> None:
        """CIStageResult should represent a skipped stage."""
        result = CIStageResult(
            stage=CIStage.AUDIT_VERIFICATION,
            passed=True,
            skipped=True,
            skip_reason="No validators registered",
        )
        assert result.skipped is True
        assert result.skip_reason == "No validators registered"

    def test_to_dict_serialization(self) -> None:
        """to_dict should produce valid dictionary."""
        result = CIStageResult(
            stage=CIStage.INVARIANT_ENFORCEMENT,
            passed=True,
            duration_ms=50.0,
        )
        data = result.to_dict()

        assert data["stage"] == "invariant_enforcement"
        assert data["passed"] is True
        assert data["failures"] == []
        assert data["duration_ms"] == 50.0


class TestCIPipelineResult:
    """Tests for CIPipelineResult dataclass."""

    def test_create_passing_pipeline(self) -> None:
        """CIPipelineResult should represent a passing pipeline."""
        result = CIPipelineResult(
            passed=True,
            stage_results=[
                CIStageResult(stage=CIStage.ARTIFACT_VALIDATION, passed=True),
                CIStageResult(stage=CIStage.APPROVAL_VERIFICATION, passed=True),
            ],
            total_duration_ms=200.0,
        )
        assert result.passed is True
        assert len(result.stage_results) == 2
        assert result.failure_count == 0

    def test_create_failing_pipeline(self) -> None:
        """CIPipelineResult should represent a failing pipeline."""
        failures = [
            CIFailure(code=CIFailureCode.TEST_FAILURE, message="Test failed"),
        ]
        result = CIPipelineResult(
            passed=False,
            stage_results=[
                CIStageResult(stage=CIStage.ARTIFACT_VALIDATION, passed=True),
                CIStageResult(
                    stage=CIStage.TEST_EXECUTION, passed=False, failures=failures
                ),
            ],
        )
        assert result.passed is False
        assert result.failure_count == 1

    def test_failure_count_property(self) -> None:
        """failure_count should sum failures across all stages."""
        result = CIPipelineResult(
            passed=False,
            stage_results=[
                CIStageResult(
                    stage=CIStage.ARTIFACT_VALIDATION,
                    passed=False,
                    failures=[
                        CIFailure(code=CIFailureCode.DRAFT_ARTIFACT_PRESENT, message="a"),
                        CIFailure(
                            code=CIFailureCode.SCHEMA_VALIDATION_FAILED, message="b"
                        ),
                    ],
                ),
                CIStageResult(
                    stage=CIStage.TEST_EXECUTION,
                    passed=False,
                    failures=[
                        CIFailure(code=CIFailureCode.TEST_FAILURE, message="c"),
                    ],
                ),
            ],
        )
        assert result.failure_count == 3

    def test_all_failures_property(self) -> None:
        """all_failures should return all failures from all stages."""
        failure1 = CIFailure(code=CIFailureCode.DRAFT_ARTIFACT_PRESENT, message="a")
        failure2 = CIFailure(code=CIFailureCode.TEST_FAILURE, message="b")
        result = CIPipelineResult(
            passed=False,
            stage_results=[
                CIStageResult(
                    stage=CIStage.ARTIFACT_VALIDATION,
                    passed=False,
                    failures=[failure1],
                ),
                CIStageResult(
                    stage=CIStage.TEST_EXECUTION,
                    passed=False,
                    failures=[failure2],
                ),
            ],
        )
        all_failures = result.all_failures
        assert len(all_failures) == 2
        assert failure1 in all_failures
        assert failure2 in all_failures

    def test_to_dict_serialization(self, tmp_path: Path) -> None:
        """to_dict should produce valid dictionary."""
        result = CIPipelineResult(
            passed=True,
            stage_results=[
                CIStageResult(stage=CIStage.ARTIFACT_VALIDATION, passed=True),
            ],
            total_duration_ms=100.0,
            repo_root=tmp_path,
            branch="main",
            commit="abc123",
        )
        data = result.to_dict()

        assert data["passed"] is True
        assert len(data["stage_results"]) == 1
        assert data["total_duration_ms"] == 100.0
        assert data["repo_root"] == str(tmp_path)
        assert data["branch"] == "main"
        assert data["commit"] == "abc123"
        assert "summary" in data
        assert data["summary"]["total_failures"] == 0

    def test_to_json_serialization(self) -> None:
        """to_json should produce valid JSON string."""
        result = CIPipelineResult(
            passed=True,
            stage_results=[],
        )
        json_str = result.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["passed"] is True

    def test_format_summary_passing(self) -> None:
        """format_summary should format passing pipeline nicely."""
        result = CIPipelineResult(
            passed=True,
            stage_results=[
                CIStageResult(
                    stage=CIStage.ARTIFACT_VALIDATION, passed=True, duration_ms=50.0
                ),
            ],
            total_duration_ms=50.0,
        )
        summary = result.format_summary()

        assert "PASSED" in summary
        assert "artifact_validation" in summary

    def test_format_summary_failing(self) -> None:
        """format_summary should show failures."""
        result = CIPipelineResult(
            passed=False,
            stage_results=[
                CIStageResult(
                    stage=CIStage.TEST_EXECUTION,
                    passed=False,
                    failures=[
                        CIFailure(
                            code=CIFailureCode.TEST_FAILURE,
                            message="5 tests failed",
                        )
                    ],
                ),
            ],
        )
        summary = result.format_summary()

        assert "FAILED" in summary
        assert "TEST_FAILURE" in summary
        assert "5 tests failed" in summary


class TestCIStage:
    """Tests for CIStage enum."""

    def test_all_stages_exist(self) -> None:
        """All CI stages should exist."""
        assert CIStage.ARTIFACT_VALIDATION.value == "artifact_validation"
        assert CIStage.APPROVAL_VERIFICATION.value == "approval_verification"
        assert CIStage.INVARIANT_ENFORCEMENT.value == "invariant_enforcement"
        assert CIStage.TEST_EXECUTION.value == "test_execution"
        assert CIStage.AUDIT_VERIFICATION.value == "audit_verification"

    def test_stage_count(self) -> None:
        """There should be exactly 5 stages."""
        assert len(CIStage) == 5
