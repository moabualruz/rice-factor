"""Domain services containing business logic.

This module provides services that coordinate domain operations.
"""

from rice_factor.domain.services.artifact_builder import (
    ArtifactBuilder,
    ArtifactBuilderError,
)
from rice_factor.domain.services.artifact_resolver import ArtifactResolver
from rice_factor.domain.services.artifact_service import ArtifactService
from rice_factor.domain.services.capability_service import CapabilityService
from rice_factor.domain.services.code_detector import CodeDetector, detect_code
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.context_builder import (
    PASS_REQUIREMENTS,
    ContextBuilder,
    ContextBuilderError,
    ForbiddenInputError,
    MissingRequiredInputError,
)
from rice_factor.domain.services.diff_service import (
    Diff,
    DiffResult,
    DiffService,
    DiffStatus,
)
from rice_factor.domain.services.failure_parser import FailureParser
from rice_factor.domain.services.failure_service import FailureService
from rice_factor.domain.services.init_service import InitService
from rice_factor.domain.services.json_extractor import JSONExtractor, extract_json
from rice_factor.domain.services.lifecycle_service import (
    AgeReport,
    LifecycleBlockingError,
    LifecycleService,
    ReviewPrompt,
)
from rice_factor.domain.services.llm_error_handler import (
    LLMErrorHandler,
    handle_llm_errors,
)
from rice_factor.domain.services.output_validator import (
    OutputValidator,
    validate_llm_output,
)
from rice_factor.domain.services.override_service import Override, OverrideService
from rice_factor.domain.services.passes import (
    PassNotFoundError,
    PassRegistry,
    get_pass,
)
from rice_factor.domain.services.phase_service import (
    COMMAND_PHASES,
    PHASE_DESCRIPTIONS,
    Phase,
    PhaseService,
)
from rice_factor.domain.services.questionnaire import (
    INIT_QUESTIONS,
    Question,
    QuestionnaireResponse,
    QuestionnaireRunner,
)
from rice_factor.domain.services.reconciliation_service import (
    ReconciliationService,
    check_work_freeze,
)
from rice_factor.domain.services.refactor_executor import (
    RefactorDiff,
    RefactorExecutor,
    RefactorResult,
)
from rice_factor.domain.services.safety_enforcer import (
    LockVerificationResult as SafetyLockVerificationResult,
)
from rice_factor.domain.services.safety_enforcer import (
    SafetyEnforcer,
)
from rice_factor.domain.services.scaffold_service import (
    ScaffoldResult,
    ScaffoldService,
)
from rice_factor.domain.services.validation_orchestrator import (
    StepResult,
    ValidationOrchestrator,
    ValidationResult,
    ValidationStep,
)

__all__ = [
    "COMMAND_PHASES",
    "INIT_QUESTIONS",
    "PASS_REQUIREMENTS",
    "PHASE_DESCRIPTIONS",
    "AgeReport",
    "ArtifactBuilder",
    "ArtifactBuilderError",
    "ArtifactResolver",
    "ArtifactService",
    "CapabilityService",
    "CodeDetector",
    "CompilerPass",
    "ContextBuilder",
    "ContextBuilderError",
    "Diff",
    "DiffResult",
    "DiffService",
    "DiffStatus",
    "FailureParser",
    "FailureService",
    "ForbiddenInputError",
    "InitService",
    "JSONExtractor",
    "LLMErrorHandler",
    "LifecycleBlockingError",
    "LifecycleService",
    "MissingRequiredInputError",
    "OutputValidator",
    "Override",
    "OverrideService",
    "PassNotFoundError",
    "PassRegistry",
    "Phase",
    "PhaseService",
    "Question",
    "QuestionnaireResponse",
    "QuestionnaireRunner",
    "ReconciliationService",
    "RefactorDiff",
    "RefactorExecutor",
    "RefactorResult",
    "ReviewPrompt",
    "SafetyEnforcer",
    "SafetyLockVerificationResult",
    "ScaffoldResult",
    "ScaffoldService",
    "StepResult",
    "ValidationOrchestrator",
    "ValidationResult",
    "ValidationStep",
    "check_work_freeze",
    "detect_code",
    "extract_json",
    "get_pass",
    "handle_llm_errors",
    "validate_llm_output",
]
