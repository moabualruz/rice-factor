"""Unit tests for CI pipeline orchestrator."""

from pathlib import Path

import pytest

from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIFailure, CIStage, CIStageResult
from rice_factor.domain.ci.pipeline import CIPipeline, CIPipelineConfig
from rice_factor.domain.ports.ci_validator import CIValidatorPort


class MockValidator:
    """Mock CI validator for testing."""

    def __init__(
        self,
        stage: CIStage,
        passed: bool = True,
        failures: list[CIFailure] | None = None,
    ) -> None:
        self._stage = stage
        self._passed = passed
        self._failures = failures or []
        self.validate_called = False
        self.validate_count = 0

    @property
    def stage_name(self) -> str:
        return self._stage.value

    def validate(self, repo_root: Path) -> CIStageResult:
        self.validate_called = True
        self.validate_count += 1
        return CIStageResult(
            stage=self._stage,
            passed=self._passed,
            failures=self._failures,
        )


class FailingValidator:
    """Validator that raises an exception."""

    @property
    def stage_name(self) -> str:
        return "failing"

    def validate(self, repo_root: Path) -> CIStageResult:
        raise ValueError("Validator error")


class TestCIPipelineConfig:
    """Tests for CIPipelineConfig."""

    def test_default_config(self) -> None:
        """Default config should stop on failure."""
        config = CIPipelineConfig()
        assert config.stop_on_failure is True
        assert config.stages_to_run is None
        assert config.skip_stages == []

    def test_custom_config(self) -> None:
        """Config should accept custom values."""
        config = CIPipelineConfig(
            stop_on_failure=False,
            stages_to_run=[CIStage.ARTIFACT_VALIDATION],
            skip_stages=[CIStage.AUDIT_VERIFICATION],
        )
        assert config.stop_on_failure is False
        assert config.stages_to_run == [CIStage.ARTIFACT_VALIDATION]
        assert config.skip_stages == [CIStage.AUDIT_VERIFICATION]


class TestCIPipeline:
    """Tests for CIPipeline orchestrator."""

    def test_register_stage(self, tmp_path: Path) -> None:
        """Pipeline should register validators."""
        pipeline = CIPipeline()
        validator = MockValidator(CIStage.ARTIFACT_VALIDATION)
        pipeline.register_stage(CIStage.ARTIFACT_VALIDATION, validator)

        # Run pipeline
        result = pipeline.run(repo_root=tmp_path)

        assert validator.validate_called is True

    def test_run_all_stages_in_order(self, tmp_path: Path) -> None:
        """Pipeline should run all stages in correct order."""
        pipeline = CIPipeline()

        validators = []
        for stage in CIPipeline.STAGE_ORDER:
            validator = MockValidator(stage)
            pipeline.register_stage(stage, validator)
            validators.append(validator)

        result = pipeline.run(repo_root=tmp_path)

        # All validators should be called
        for validator in validators:
            assert validator.validate_called is True

        # Result should pass
        assert result.passed is True
        assert len(result.stage_results) == 5

    def test_stop_on_failure_default(self, tmp_path: Path) -> None:
        """Pipeline should stop on first failure by default."""
        pipeline = CIPipeline()

        # First stage passes
        validator1 = MockValidator(CIStage.ARTIFACT_VALIDATION, passed=True)
        pipeline.register_stage(CIStage.ARTIFACT_VALIDATION, validator1)

        # Second stage fails
        validator2 = MockValidator(
            CIStage.APPROVAL_VERIFICATION,
            passed=False,
            failures=[
                CIFailure(
                    code=CIFailureCode.ARTIFACT_NOT_APPROVED,
                    message="Not approved",
                )
            ],
        )
        pipeline.register_stage(CIStage.APPROVAL_VERIFICATION, validator2)

        # Third stage should not run
        validator3 = MockValidator(CIStage.INVARIANT_ENFORCEMENT, passed=True)
        pipeline.register_stage(CIStage.INVARIANT_ENFORCEMENT, validator3)

        result = pipeline.run(repo_root=tmp_path)

        assert result.passed is False
        assert validator1.validate_called is True
        assert validator2.validate_called is True
        assert validator3.validate_called is False

        # Third stage should be marked as skipped
        skipped_stages = [r for r in result.stage_results if r.skipped]
        assert len(skipped_stages) >= 1

    def test_continue_on_failure_config(self, tmp_path: Path) -> None:
        """Pipeline should continue when configured."""
        config = CIPipelineConfig(stop_on_failure=False)
        pipeline = CIPipeline(config=config)

        # First stage fails
        validator1 = MockValidator(
            CIStage.ARTIFACT_VALIDATION,
            passed=False,
            failures=[
                CIFailure(code=CIFailureCode.DRAFT_ARTIFACT_PRESENT, message="Draft")
            ],
        )
        pipeline.register_stage(CIStage.ARTIFACT_VALIDATION, validator1)

        # Second stage should still run
        validator2 = MockValidator(CIStage.APPROVAL_VERIFICATION, passed=True)
        pipeline.register_stage(CIStage.APPROVAL_VERIFICATION, validator2)

        result = pipeline.run(repo_root=tmp_path)

        assert result.passed is False
        assert validator1.validate_called is True
        assert validator2.validate_called is True

    def test_skip_stages_config(self, tmp_path: Path) -> None:
        """Pipeline should skip configured stages."""
        config = CIPipelineConfig(skip_stages=[CIStage.AUDIT_VERIFICATION])
        pipeline = CIPipeline(config=config)

        # Register all stages
        for stage in CIPipeline.STAGE_ORDER:
            pipeline.register_stage(stage, MockValidator(stage))

        result = pipeline.run(repo_root=tmp_path)

        # Find audit stage result
        audit_result = next(
            r for r in result.stage_results if r.stage == CIStage.AUDIT_VERIFICATION
        )
        assert audit_result.skipped is True
        assert audit_result.skip_reason == "Skipped by configuration"

    def test_stages_to_run_config(self, tmp_path: Path) -> None:
        """Pipeline should only run specified stages."""
        config = CIPipelineConfig(
            stages_to_run=[CIStage.ARTIFACT_VALIDATION, CIStage.TEST_EXECUTION]
        )
        pipeline = CIPipeline(config=config)

        # Register all validators
        validators = {}
        for stage in CIPipeline.STAGE_ORDER:
            validator = MockValidator(stage)
            pipeline.register_stage(stage, validator)
            validators[stage] = validator

        result = pipeline.run(repo_root=tmp_path)

        # Only specified stages should run
        assert validators[CIStage.ARTIFACT_VALIDATION].validate_called is True
        assert validators[CIStage.TEST_EXECUTION].validate_called is True
        assert validators[CIStage.APPROVAL_VERIFICATION].validate_called is False
        assert validators[CIStage.INVARIANT_ENFORCEMENT].validate_called is False
        assert validators[CIStage.AUDIT_VERIFICATION].validate_called is False

    def test_missing_validator_skipped(self, tmp_path: Path) -> None:
        """Stages without validators should be skipped."""
        pipeline = CIPipeline()

        # Only register one stage
        pipeline.register_stage(
            CIStage.ARTIFACT_VALIDATION,
            MockValidator(CIStage.ARTIFACT_VALIDATION),
        )

        result = pipeline.run(repo_root=tmp_path)

        # All other stages should be skipped
        skipped = [r for r in result.stage_results if r.skipped]
        assert len(skipped) == 4  # 5 stages - 1 registered = 4 skipped

    def test_pipeline_result_metadata(self, tmp_path: Path) -> None:
        """Pipeline should include metadata in result."""
        pipeline = CIPipeline()
        pipeline.register_stage(
            CIStage.ARTIFACT_VALIDATION,
            MockValidator(CIStage.ARTIFACT_VALIDATION),
        )

        result = pipeline.run(
            repo_root=tmp_path,
            branch="feature/test",
            commit="abc123",
        )

        assert result.repo_root == tmp_path
        assert result.branch == "feature/test"
        assert result.commit == "abc123"
        assert result.timestamp is not None
        assert result.total_duration_ms > 0

    def test_validator_exception_handled(self, tmp_path: Path) -> None:
        """Pipeline should handle validator exceptions gracefully."""
        pipeline = CIPipeline()
        pipeline.register_stage(CIStage.ARTIFACT_VALIDATION, FailingValidator())

        result = pipeline.run(repo_root=tmp_path)

        assert result.passed is False
        # Should have a failure from the exception
        assert result.failure_count == 1
        assert "Validator error" in result.all_failures[0].message


class TestCIPipelineStageOrder:
    """Tests for stage ordering."""

    def test_stage_order_constant(self) -> None:
        """STAGE_ORDER should define all stages in correct order."""
        expected = [
            CIStage.ARTIFACT_VALIDATION,
            CIStage.APPROVAL_VERIFICATION,
            CIStage.INVARIANT_ENFORCEMENT,
            CIStage.TEST_EXECUTION,
            CIStage.AUDIT_VERIFICATION,
        ]
        assert CIPipeline.STAGE_ORDER == expected

    def test_stages_run_in_order(self, tmp_path: Path) -> None:
        """Stages should run in the defined order."""
        pipeline = CIPipeline()
        order_tracker: list[CIStage] = []

        class OrderTrackingValidator:
            def __init__(self, stage: CIStage) -> None:
                self._stage = stage

            @property
            def stage_name(self) -> str:
                return self._stage.value

            def validate(self, repo_root: Path) -> CIStageResult:
                order_tracker.append(self._stage)
                return CIStageResult(stage=self._stage, passed=True)

        for stage in CIPipeline.STAGE_ORDER:
            pipeline.register_stage(stage, OrderTrackingValidator(stage))

        pipeline.run(repo_root=tmp_path)

        assert order_tracker == CIPipeline.STAGE_ORDER
