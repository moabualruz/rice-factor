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

__all__ = [
    "ArtifactDependencyError",
    "ArtifactError",
    "ArtifactNotFoundError",
    "ArtifactStatusError",
    "ArtifactValidationError",
    "CLIError",
    "CodeInOutputError",
    "ConfirmationRequired",
    "ExplanatoryTextError",
    "InvalidJSONError",
    "LLMAPIError",
    "LLMError",
    "LLMInvalidRequestError",
    "LLMMissingInformationError",
    "LLMOutputError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "MissingPrerequisiteError",
    "MultipleArtifactsError",
    "PhaseError",
    "RiceFactorError",
    "SchemaViolationError",
]
