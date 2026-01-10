"""Artifact builder service.

This module provides the ArtifactBuilder service that orchestrates
the full compilation flow: building context, executing passes,
creating envelopes, and saving artifacts.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.payloads.failure_report import FailureReportPayload
from rice_factor.domain.ports.llm import LLMPort
from rice_factor.domain.ports.storage import StoragePort
from rice_factor.domain.services.context_builder import ContextBuilder
from rice_factor.domain.services.failure_service import FailureService
from rice_factor.domain.services.passes import PassRegistry, get_pass


class ArtifactBuilderError(Exception):
    """Error raised during artifact building."""

    def __init__(self, message: str, pass_type: CompilerPassType | None = None) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            pass_type: The pass type that failed, if applicable.
        """
        self.pass_type = pass_type
        super().__init__(message)


class ArtifactBuilder:
    """Service for orchestrating artifact compilation.

    Coordinates:
    1. Getting the appropriate compiler pass
    2. Building compilation context
    3. Executing the pass
    4. Creating artifact envelopes
    5. Saving to storage
    6. Handling failures

    Attributes:
        llm_port: LLM provider for generation.
        storage: Storage adapter for persistence.
        context_builder: Context builder for input gathering.
        failure_service: Service for failure handling.
    """

    def __init__(
        self,
        llm_port: LLMPort,
        storage: StoragePort,
        context_builder: ContextBuilder | None = None,
        failure_service: FailureService | None = None,
    ) -> None:
        """Initialize the artifact builder.

        Args:
            llm_port: LLM port implementation for generation.
            storage: Storage port implementation for persistence.
            context_builder: Context builder (created if not provided).
            failure_service: Failure service (created if not provided).
        """
        self._llm_port = llm_port
        self._storage = storage
        self._context_builder = context_builder or ContextBuilder(storage)
        self._failure_service = failure_service or FailureService()
        self._registry = PassRegistry.get_instance()

    def build(
        self,
        pass_type: CompilerPassType,
        project_root: Path,
        target_file: str | None = None,
        artifacts: dict[str, Any] | None = None,
    ) -> ArtifactEnvelope[BaseModel]:
        """Build an artifact using the specified compiler pass.

        Orchestrates the full compilation flow:
        1. Get pass from registry
        2. Build context via ContextBuilder
        3. Execute pass
        4. If success, create ArtifactEnvelope
        5. Save to storage
        6. If failure, create FailureReport

        Args:
            pass_type: The type of pass to execute.
            project_root: Root directory of the project.
            target_file: Target file for implementation pass.
            artifacts: Pre-loaded artifacts (artifact_id -> payload).

        Returns:
            ArtifactEnvelope with the generated artifact (or FailureReport on error).

        Raises:
            ArtifactBuilderError: If building fails without creating a FailureReport.
        """
        # 1. Get the pass
        compiler_pass = get_pass(pass_type)

        # 2. Build context
        context = self._context_builder.build_context(
            pass_type=pass_type,
            project_root=project_root,
            target_file=target_file,
            artifacts=artifacts,
        )

        # 3. Execute pass
        result = compiler_pass.compile(context, self._llm_port)

        # 4. Handle result
        if result.success and result.payload is not None:
            # Create envelope for successful artifact
            envelope = self._create_envelope(pass_type, result.payload)

            # 5. Save to storage
            self._save_artifact(envelope)

            return envelope
        else:
            # Create failure report
            failure_envelope: ArtifactEnvelope[BaseModel] = (
                self._create_failure_envelope(
                    pass_type=pass_type,
                    result=result,
                    context=context,
                )
            )

            # Save failure report
            self._save_artifact(failure_envelope)

            return failure_envelope

    def build_with_context(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext,
    ) -> ArtifactEnvelope[BaseModel]:
        """Build an artifact using pre-built context.

        For cases where context is already built externally.

        Args:
            pass_type: The type of pass to execute.
            context: Pre-built compilation context.

        Returns:
            ArtifactEnvelope with the generated artifact (or FailureReport on error).
        """
        # Get and execute pass
        compiler_pass = get_pass(pass_type)
        result = compiler_pass.compile(context, self._llm_port)

        # Handle result
        if result.success and result.payload is not None:
            envelope = self._create_envelope(pass_type, result.payload)
            self._save_artifact(envelope)
            return envelope
        else:
            failure_envelope: ArtifactEnvelope[BaseModel] = (
                self._create_failure_envelope(
                    pass_type=pass_type,
                    result=result,
                    context=context,
                )
            )
            self._save_artifact(failure_envelope)
            return failure_envelope

    def _create_envelope(
        self,
        pass_type: CompilerPassType,
        payload: dict[str, Any],
    ) -> ArtifactEnvelope[BaseModel]:
        """Create an artifact envelope for the payload.

        Args:
            pass_type: The pass type that produced the artifact.
            payload: The artifact payload.

        Returns:
            ArtifactEnvelope with DRAFT status.
        """
        # Get artifact type for this pass
        artifact_type = self._get_artifact_type(pass_type)

        # Create payload model from dict
        payload_model = self._create_payload_model(artifact_type, payload)

        # Create envelope with DRAFT status
        envelope: ArtifactEnvelope[BaseModel] = ArtifactEnvelope(
            artifact_type=artifact_type,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.LLM,
            payload=payload_model,
        )

        return envelope

    def _create_failure_envelope(
        self,
        pass_type: CompilerPassType,
        result: CompilerResult,
        context: CompilerContext,
    ) -> ArtifactEnvelope[BaseModel]:
        """Create a failure report envelope.

        Args:
            pass_type: The pass type that failed.
            result: The compiler result with error details.
            context: The context used for compilation.

        Returns:
            ArtifactEnvelope containing FailureReportPayload.
        """
        from datetime import UTC, datetime

        from rice_factor.domain.artifacts.payloads.failure_report import (
            FailureCategory,
            RecoveryAction,
        )

        # Determine failure category
        category = FailureCategory.INTERNAL_ERROR
        if result.error_type == "missing_information":
            category = FailureCategory.MISSING_INFORMATION
        elif result.error_type == "invalid_request":
            category = FailureCategory.INVALID_REQUEST
        elif result.error_type == "api_error":
            category = FailureCategory.API_ERROR

        # Build details
        details: dict[str, Any] = {
            "pass_type": pass_type.value,
            "error_type": result.error_type,
        }
        if context.target_file:
            details["target_file"] = context.target_file

        # Create payload
        payload = FailureReportPayload(
            phase=f"compile_{pass_type.value.lower()}",
            category=category,
            summary=result.error_details or f"Failed to compile {pass_type.value}",
            details=details,
            blocking=True,  # Compilation failures are blocking
            recovery_action=RecoveryAction.FIX_AND_RETRY,
            timestamp=datetime.now(UTC),
            raw_response=None,  # Could include raw LLM response if available
        )

        envelope: ArtifactEnvelope[BaseModel] = ArtifactEnvelope(
            artifact_type=ArtifactType.FAILURE_REPORT,
            status=ArtifactStatus.DRAFT,
            created_by=CreatedBy.SYSTEM,
            payload=payload,
        )

        return envelope

    def _get_artifact_type(self, pass_type: CompilerPassType) -> ArtifactType:
        """Map pass type to artifact type.

        Args:
            pass_type: The compiler pass type.

        Returns:
            The corresponding artifact type.
        """
        mapping = {
            CompilerPassType.PROJECT: ArtifactType.PROJECT_PLAN,
            CompilerPassType.ARCHITECTURE: ArtifactType.ARCHITECTURE_PLAN,
            CompilerPassType.SCAFFOLD: ArtifactType.SCAFFOLD_PLAN,
            CompilerPassType.TEST: ArtifactType.TEST_PLAN,
            CompilerPassType.IMPLEMENTATION: ArtifactType.IMPLEMENTATION_PLAN,
            CompilerPassType.REFACTOR: ArtifactType.REFACTOR_PLAN,
        }
        return mapping[pass_type]

    def _create_payload_model(
        self, artifact_type: ArtifactType, payload: dict[str, Any]
    ) -> BaseModel:
        """Create a Pydantic model from the payload dict.

        Args:
            artifact_type: The type of artifact.
            payload: The payload dictionary.

        Returns:
            A Pydantic BaseModel instance.
        """
        # Import payload models
        from rice_factor.domain.artifacts.payloads.architecture_plan import (
            ArchitecturePlanPayload,
        )
        from rice_factor.domain.artifacts.payloads.implementation_plan import (
            ImplementationPlanPayload,
        )
        from rice_factor.domain.artifacts.payloads.project_plan import (
            ProjectPlanPayload,
        )
        from rice_factor.domain.artifacts.payloads.refactor_plan import (
            RefactorPlanPayload,
        )
        from rice_factor.domain.artifacts.payloads.scaffold_plan import (
            ScaffoldPlanPayload,
        )
        from rice_factor.domain.artifacts.payloads.test_plan import TestPlanPayload
        from rice_factor.domain.artifacts.payloads.validation_result import (
            ValidationResultPayload,
        )

        model_map: dict[ArtifactType, type[BaseModel]] = {
            ArtifactType.PROJECT_PLAN: ProjectPlanPayload,
            ArtifactType.ARCHITECTURE_PLAN: ArchitecturePlanPayload,
            ArtifactType.SCAFFOLD_PLAN: ScaffoldPlanPayload,
            ArtifactType.TEST_PLAN: TestPlanPayload,
            ArtifactType.IMPLEMENTATION_PLAN: ImplementationPlanPayload,
            ArtifactType.REFACTOR_PLAN: RefactorPlanPayload,
            ArtifactType.VALIDATION_RESULT: ValidationResultPayload,
        }

        model_class = model_map.get(artifact_type)
        if model_class is None:
            raise ArtifactBuilderError(
                f"No payload model for artifact type: {artifact_type.value}"
            )

        return model_class.model_validate(payload)

    def _save_artifact(self, envelope: ArtifactEnvelope[BaseModel]) -> None:
        """Save an artifact to storage.

        Args:
            envelope: The artifact envelope to save.
        """
        path = self._storage.get_path_for_artifact(
            envelope.id, envelope.artifact_type
        )
        self._storage.save(envelope, path)
