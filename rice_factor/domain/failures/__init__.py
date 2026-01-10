"""Domain failure types and error handling.

This module provides the exception hierarchy for Rice-Factor including:
- RiceFactorError: Base exception
- ArtifactError: Artifact-related errors
- ArtifactStatusError: Invalid status transitions
- ArtifactValidationError: Schema validation failures
- ArtifactNotFoundError: Artifact not found
- ArtifactDependencyError: Dependency not satisfied
"""

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
    "RiceFactorError",
]
