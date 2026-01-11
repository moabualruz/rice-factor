"""CI Pipeline Orchestrator.

This module provides the CIPipeline class that orchestrates the execution
of all CI validation stages in the correct order.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rice_factor.domain.ci.models import CIPipelineResult, CIStage, CIStageResult
from rice_factor.domain.ports.ci_validator import CIValidatorPort


@dataclass
class CIPipelineConfig:
    """Configuration for CI pipeline execution.

    Attributes:
        stop_on_failure: If True, stop executing stages after first failure.
        stages_to_run: If set, only run these stages. If None, run all.
        skip_stages: Stages to skip entirely.
    """

    stop_on_failure: bool = True
    stages_to_run: list[CIStage] | None = None
    skip_stages: list[CIStage] = field(default_factory=list)


class CIPipeline:
    """Orchestrates CI validation stages.

    The pipeline runs stages in a defined order and aggregates results.
    It can be configured to stop on first failure or run all stages.

    Stages are executed in this order:
    1. Artifact Validation - Check artifact status and schema
    2. Approval Verification - Check all required approvals
    3. Invariant Enforcement - Check test locks, architecture rules
    4. Test Execution - Run tests
    5. Audit Verification - Verify audit trail integrity

    Example:
        pipeline = CIPipeline()
        pipeline.register_stage(CIStage.ARTIFACT_VALIDATION, artifact_validator)
        pipeline.register_stage(CIStage.APPROVAL_VERIFICATION, approval_validator)
        result = pipeline.run(repo_root)
    """

    # Default stage execution order
    STAGE_ORDER = [
        CIStage.ARTIFACT_VALIDATION,
        CIStage.APPROVAL_VERIFICATION,
        CIStage.INVARIANT_ENFORCEMENT,
        CIStage.TEST_EXECUTION,
        CIStage.AUDIT_VERIFICATION,
    ]

    def __init__(self, config: CIPipelineConfig | None = None) -> None:
        """Initialize the pipeline.

        Args:
            config: Pipeline configuration. Defaults to stop_on_failure=True.
        """
        self.config = config or CIPipelineConfig()
        self._validators: dict[CIStage, CIValidatorPort] = {}

    def register_stage(self, stage: CIStage, validator: CIValidatorPort) -> None:
        """Register a validator for a stage.

        Args:
            stage: The stage to register.
            validator: The validator implementation.
        """
        self._validators[stage] = validator

    def run(
        self,
        repo_root: Path,
        branch: str | None = None,
        commit: str | None = None,
    ) -> CIPipelineResult:
        """Run the CI pipeline.

        Executes all registered stages in order and aggregates results.

        Args:
            repo_root: Path to the repository root.
            branch: Git branch being validated (optional).
            commit: Git commit SHA being validated (optional).

        Returns:
            CIPipelineResult with aggregate pass/fail status.
        """
        start_time = time.perf_counter()
        stage_results: list[CIStageResult] = []
        pipeline_passed = True

        # Determine which stages to run
        stages = self._get_stages_to_run()

        for stage in stages:
            # Check if stage should be skipped
            if stage in self.config.skip_stages:
                stage_results.append(
                    CIStageResult(
                        stage=stage,
                        passed=True,
                        skipped=True,
                        skip_reason="Skipped by configuration",
                    )
                )
                continue

            # Check if validator is registered
            if stage not in self._validators:
                stage_results.append(
                    CIStageResult(
                        stage=stage,
                        passed=True,
                        skipped=True,
                        skip_reason="No validator registered",
                    )
                )
                continue

            # Run the stage
            validator = self._validators[stage]
            stage_start = time.perf_counter()

            try:
                result = validator.validate(repo_root)
                result.duration_ms = (time.perf_counter() - stage_start) * 1000
            except Exception as e:
                # Catch any exceptions and convert to a failure
                from rice_factor.domain.ci.failure_codes import CIFailureCode
                from rice_factor.domain.ci.models import CIFailure

                result = CIStageResult(
                    stage=stage,
                    passed=False,
                    failures=[
                        CIFailure(
                            code=CIFailureCode.SCHEMA_VALIDATION_FAILED,
                            message=f"Stage execution error: {e}",
                            details={"exception": str(type(e).__name__)},
                        )
                    ],
                    duration_ms=(time.perf_counter() - stage_start) * 1000,
                )

            stage_results.append(result)

            # Check if pipeline should stop
            if not result.passed:
                pipeline_passed = False
                if self.config.stop_on_failure:
                    # Mark remaining stages as skipped
                    remaining = stages[stages.index(stage) + 1 :]
                    for remaining_stage in remaining:
                        stage_results.append(
                            CIStageResult(
                                stage=remaining_stage,
                                passed=True,
                                skipped=True,
                                skip_reason="Skipped due to earlier failure",
                            )
                        )
                    break

        total_duration = (time.perf_counter() - start_time) * 1000

        return CIPipelineResult(
            passed=pipeline_passed,
            stage_results=stage_results,
            total_duration_ms=total_duration,
            timestamp=datetime.now(),
            repo_root=repo_root,
            branch=branch,
            commit=commit,
        )

    def _get_stages_to_run(self) -> list[CIStage]:
        """Get the list of stages to run based on configuration."""
        if self.config.stages_to_run is not None:
            # Use specified stages, but maintain order
            return [s for s in self.STAGE_ORDER if s in self.config.stages_to_run]
        return self.STAGE_ORDER
