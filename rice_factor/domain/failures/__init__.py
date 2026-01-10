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

__all__ = [
    "ArtifactDependencyError",
    "ArtifactError",
    "ArtifactNotFoundError",
    "ArtifactStatusError",
    "ArtifactValidationError",
    "CLIError",
    "ConfirmationRequired",
    "MissingPrerequisiteError",
    "PhaseError",
    "RiceFactorError",
]
