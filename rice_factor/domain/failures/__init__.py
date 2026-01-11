"""Domain failure types and error handling.

This module provides the exception hierarchy for Rice-Factor including:
- RiceFactorError: Base exception
- ArtifactError: Artifact-related errors
- ArtifactStatusError: Invalid status transitions
- ArtifactValidationError: Schema validation failures
- ArtifactNotFoundError: Artifact not found
- ArtifactDependencyError: Dependency not satisfied
- CLIError: CLI-related errors
- PhaseError: Invalid phase for command
- MissingPrerequisiteError: Missing required prerequisite
- ConfirmationRequired: User confirmation not provided
- LLMError: Base LLM error
- LLMAPIError: Provider API failures
- LLMTimeoutError: Request timeout
- LLMRateLimitError: Rate limiting
- LLMMissingInformationError: Explicit missing info error
- LLMInvalidRequestError: Explicit invalid request error
- LLMOutputError: Base output validation error
- InvalidJSONError: LLM returned non-JSON
- SchemaViolationError: LLM output doesn't match schema
- CodeInOutputError: LLM returned source code
- MultipleArtifactsError: LLM returned multiple artifacts
- ExplanatoryTextError: LLM included text outside JSON
- ExecutorError: Base executor error
- ExecutorPreconditionError: Preconditions not met
- ExecutorCapabilityError: Operation not supported
- ExecutorArtifactError: Invalid artifact
- ExecutorApplyError: Apply failed
- ValidationError: Validation engine errors
"""

from rice_factor.domain.failures.cli_errors import (
    CLIError,
    ConfirmationRequired,
    MissingPrerequisiteError,
    PhaseError,
)
from rice_factor.domain.failures.errors import (
    ArtifactDependencyError,
    ArtifactError,
    ArtifactNotFoundError,
    ArtifactStatusError,
    ArtifactValidationError,
    RiceFactorError,
)
from rice_factor.domain.failures.executor_errors import (
    ArtifactNotApprovedError,
    ArtifactSchemaError,
    ArtifactTypeError,
    DestinationExistsError,
    DiffNotApprovedError,
    ExecutorApplyError,
    ExecutorArtifactError,
    ExecutorCapabilityError,
    ExecutorError,
    ExecutorPreconditionError,
    FileAlreadyExistsError,
    FileWriteError,
    GitApplyError,
    PathEscapesRepoError,
    SourceFileNotFoundError,
    TestsLockedError,
    UnauthorizedFileModificationError,
    UnsupportedOperationError,
)
from rice_factor.domain.failures.llm_errors import (
    CodeInOutputError,
    ExplanatoryTextError,
    InvalidJSONError,
    LLMAPIError,
    LLMError,
    LLMInvalidRequestError,
    LLMMissingInformationError,
    LLMOutputError,
    LLMRateLimitError,
    LLMTimeoutError,
    MultipleArtifactsError,
    SchemaViolationError,
)
from rice_factor.domain.failures.validation_errors import (
    CommandNotFoundError,
    InvalidStatusError,
    InvariantViolationError,
    LanguageNotSupportedError,
    MissingApprovalError,
    MissingDependencyError,
    ProcessError,
    TestPlanNotLockedError,
    ValidationError,
    ValidationTimeoutError,
    ValidatorConfigError,
    ValidatorExecutionError,
    ValidatorNotFoundError,
)

__all__ = [
    "ArtifactDependencyError",
    "ArtifactError",
    "ArtifactNotApprovedError",
    "ArtifactNotFoundError",
    "ArtifactSchemaError",
    "ArtifactStatusError",
    "ArtifactTypeError",
    "ArtifactValidationError",
    "CLIError",
    "CodeInOutputError",
    "CommandNotFoundError",
    "ConfirmationRequired",
    "DestinationExistsError",
    "DiffNotApprovedError",
    "ExecutorApplyError",
    "ExecutorArtifactError",
    "ExecutorCapabilityError",
    "ExecutorError",
    "ExecutorPreconditionError",
    "ExplanatoryTextError",
    "FileAlreadyExistsError",
    "FileWriteError",
    "GitApplyError",
    "InvalidJSONError",
    "InvalidStatusError",
    "InvariantViolationError",
    "LLMAPIError",
    "LLMError",
    "LLMInvalidRequestError",
    "LLMMissingInformationError",
    "LLMOutputError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LanguageNotSupportedError",
    "MissingApprovalError",
    "MissingDependencyError",
    "MissingPrerequisiteError",
    "MultipleArtifactsError",
    "PathEscapesRepoError",
    "PhaseError",
    "ProcessError",
    "RiceFactorError",
    "SchemaViolationError",
    "SourceFileNotFoundError",
    "TestPlanNotLockedError",
    "TestsLockedError",
    "UnauthorizedFileModificationError",
    "UnsupportedOperationError",
    "ValidationError",
    "ValidationTimeoutError",
    "ValidatorConfigError",
    "ValidatorExecutionError",
    "ValidatorNotFoundError",
]
