"""Validator port for artifact validation.

This module defines the interface for artifact validation, following
the hexagonal architecture pattern where the domain defines ports
and adapters implement them.
"""

from typing import Any, Protocol

from pydantic import BaseModel

from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope


class ValidatorPort(Protocol):
    """Protocol for artifact validation.

    Implementations should validate artifacts using both Pydantic models
    (for Python type safety) and JSON Schema (for language-agnostic validation).
    """

    def validate(self, data: dict[str, Any]) -> ArtifactEnvelope[BaseModel]:
        """Validate artifact data and return an ArtifactEnvelope.

        Args:
            data: Raw artifact data dictionary.

        Returns:
            Validated ArtifactEnvelope instance.

        Raises:
            ArtifactValidationError: If validation fails.
        """
        ...

    def validate_payload(
        self, data: dict[str, Any], artifact_type: ArtifactType
    ) -> BaseModel:
        """Validate payload data for a specific artifact type.

        Args:
            data: Raw payload data dictionary.
            artifact_type: The type of artifact this payload belongs to.

        Returns:
            Validated payload model instance.

        Raises:
            ArtifactValidationError: If validation fails.
        """
        ...

    def validate_json_schema(
        self, data: dict[str, Any], artifact_type: ArtifactType | None = None
    ) -> None:
        """Validate data against JSON Schema only.

        Args:
            data: Data to validate.
            artifact_type: If provided, validates payload against payload schema.
                          If None, validates against envelope schema.

        Raises:
            ArtifactValidationError: If validation fails.
        """
        ...
