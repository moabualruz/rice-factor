"""Context builder for compiler passes.

This module provides the ContextBuilder service that gathers the
appropriate inputs for each compiler pass, validating that required
inputs are present and forbidden inputs are excluded.
"""

from pathlib import Path
from typing import Any

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
)
from rice_factor.domain.artifacts.enums import ArtifactType

# Define required and forbidden inputs per pass type
PASS_REQUIREMENTS: dict[CompilerPassType, dict[str, Any]] = {
    CompilerPassType.PROJECT: {
        "required_files": ["requirements.md", "constraints.md", "glossary.md"],
        "forbidden_inputs": ["source_code", "tests", "existing_artifacts"],
        "required_artifacts": [],
    },
    CompilerPassType.ARCHITECTURE: {
        "required_files": ["constraints.md"],
        "forbidden_inputs": [],
        "required_artifacts": [ArtifactType.PROJECT_PLAN],
    },
    CompilerPassType.SCAFFOLD: {
        "required_files": [],
        "forbidden_inputs": [],
        "required_artifacts": [ArtifactType.PROJECT_PLAN, ArtifactType.ARCHITECTURE_PLAN],
    },
    CompilerPassType.TEST: {
        "required_files": ["requirements.md"],
        "forbidden_inputs": [],
        "required_artifacts": [
            ArtifactType.PROJECT_PLAN,
            ArtifactType.ARCHITECTURE_PLAN,
            ArtifactType.SCAFFOLD_PLAN,
        ],
    },
    CompilerPassType.IMPLEMENTATION: {
        "required_files": [],  # target_file is handled separately
        "forbidden_inputs": ["all_other_source_files"],  # TINY context
        "required_artifacts": [ArtifactType.TEST_PLAN, ArtifactType.SCAFFOLD_PLAN],
        "requires_target_file": True,
    },
    CompilerPassType.REFACTOR: {
        "required_files": [],
        "forbidden_inputs": [],
        "required_artifacts": [ArtifactType.ARCHITECTURE_PLAN, ArtifactType.TEST_PLAN],
        "requires_locked_test_plan": True,
    },
}


class ContextBuilderError(Exception):
    """Error raised when context building fails."""

    pass


class MissingRequiredInputError(ContextBuilderError):
    """Error raised when a required input is missing."""

    def __init__(self, input_type: str, input_name: str) -> None:
        self.input_type = input_type
        self.input_name = input_name
        super().__init__(f"Missing required {input_type}: {input_name}")


class ForbiddenInputError(ContextBuilderError):
    """Error raised when a forbidden input is detected."""

    def __init__(self, input_type: str, details: str) -> None:
        self.input_type = input_type
        self.details = details
        super().__init__(f"Forbidden input detected ({input_type}): {details}")


class ContextBuilder:
    """Service for building compilation context.

    Gathers inputs for compiler passes, validates requirements,
    and ensures forbidden inputs are excluded.
    """

    def __init__(self, storage_adapter: Any | None = None) -> None:
        """Initialize the context builder.

        Args:
            storage_adapter: Optional storage adapter for loading artifacts.
                             If None, artifacts must be provided directly.
        """
        self._storage = storage_adapter

    def build_context(
        self,
        pass_type: CompilerPassType,
        project_root: Path,
        target_file: str | None = None,
        artifacts: dict[str, Any] | None = None,
    ) -> CompilerContext:
        """Build compilation context for a pass.

        Args:
            pass_type: The type of compiler pass.
            project_root: Root directory of the project.
            target_file: Target file for implementation pass.
            artifacts: Pre-loaded artifacts (artifact_id -> payload).

        Returns:
            CompilerContext with gathered inputs.

        Raises:
            MissingRequiredInputError: If a required input is missing.
            ForbiddenInputError: If a forbidden input is detected.
        """
        requirements = PASS_REQUIREMENTS[pass_type]

        # Load project files
        project_files = self._load_project_files(project_root, requirements)

        # Handle artifacts
        if artifacts is None:
            artifacts = {}

        # Build context
        context = CompilerContext(
            pass_type=pass_type,
            project_files=project_files,
            artifacts=artifacts,
            target_file=target_file,
        )

        # Validate context
        self.validate_inputs(pass_type, context)

        # Check for forbidden inputs
        forbidden = self.check_forbidden_inputs(pass_type, context)
        if forbidden:
            raise ForbiddenInputError(forbidden[0], f"Found in context: {forbidden}")

        return context

    def _load_project_files(
        self, project_root: Path, requirements: dict[str, Any]
    ) -> dict[str, str]:
        """Load project files from .project/ directory.

        Args:
            project_root: Root directory of the project.
            requirements: Pass requirements.

        Returns:
            Dict mapping filename to content.
        """
        project_files: dict[str, str] = {}
        project_dir = project_root / ".project"

        for filename in requirements.get("required_files", []):
            file_path = project_dir / filename
            if file_path.exists():
                project_files[filename] = file_path.read_text(encoding="utf-8")

        return project_files

    def validate_inputs(
        self, pass_type: CompilerPassType, context: CompilerContext
    ) -> bool:
        """Validate that all required inputs are present.

        Args:
            pass_type: The type of compiler pass.
            context: The compilation context to validate.

        Returns:
            True if all required inputs are present.

        Raises:
            MissingRequiredInputError: If a required input is missing.
        """
        requirements = PASS_REQUIREMENTS[pass_type]

        # Check required files
        for filename in requirements.get("required_files", []):
            if not context.has_file(filename):
                raise MissingRequiredInputError("file", filename)

        # Check required artifacts
        for artifact_type in requirements.get("required_artifacts", []):
            # For now, check if any artifact of this type exists
            # In full implementation, would check for approved status
            found = False
            for _artifact_id, payload in context.artifacts.items():
                if self._is_artifact_type(payload, artifact_type):
                    found = True
                    break
            if not found:
                raise MissingRequiredInputError("artifact", artifact_type.value)

        # Check target file for implementation pass
        if requirements.get("requires_target_file") and not context.target_file:
            raise MissingRequiredInputError("target_file", "implementation target")

        return True

    def check_forbidden_inputs(
        self, pass_type: CompilerPassType, context: CompilerContext
    ) -> list[str]:
        """Check for forbidden inputs in the context.

        Args:
            pass_type: The type of compiler pass.
            context: The compilation context to check.

        Returns:
            List of forbidden input types found (empty if none).
        """
        requirements = PASS_REQUIREMENTS[pass_type]
        forbidden_found: list[str] = []

        forbidden_types = requirements.get("forbidden_inputs", [])

        for forbidden_type in forbidden_types:
            if forbidden_type == "source_code":
                # Check for source code patterns in project files
                if self._has_source_code(context):
                    forbidden_found.append("source_code")
            elif forbidden_type == "tests":
                # Check for test files in context
                if self._has_test_files(context):
                    forbidden_found.append("tests")
            elif forbidden_type == "existing_artifacts":
                # Check for non-empty artifacts dict
                if context.artifacts:
                    forbidden_found.append("existing_artifacts")
            elif forbidden_type == "all_other_source_files":
                # Implementation pass: only target file allowed
                # This is enforced by not loading other files
                pass

        return forbidden_found

    def _is_artifact_type(
        self, payload: Any, artifact_type: ArtifactType  # noqa: ARG002
    ) -> bool:
        """Check if a payload matches an artifact type.

        Args:
            payload: The artifact payload.
            artifact_type: The expected type (will be used in full implementation).

        Returns:
            True if the payload matches the type.
        """
        # Simple check - in full implementation would inspect payload structure
        # artifact_type will be used to verify payload matches expected schema
        return isinstance(payload, dict)

    def _has_source_code(self, context: CompilerContext) -> bool:
        """Check if context contains source code.

        Source code patterns: .py, .js, .ts, .go, .rs, etc.
        """
        source_extensions = {".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp"}
        for filename in context.project_files:
            if any(filename.endswith(ext) for ext in source_extensions):
                return True
        return False

    def _has_test_files(self, context: CompilerContext) -> bool:
        """Check if context contains test files."""
        test_patterns = ["test_", "_test.", ".test.", "tests/", "test/"]
        for filename in context.project_files:
            if any(pattern in filename.lower() for pattern in test_patterns):
                return True
        return False

    def get_required_files(self, pass_type: CompilerPassType) -> list[str]:
        """Get list of required files for a pass type.

        Args:
            pass_type: The compiler pass type.

        Returns:
            List of required file names.
        """
        result: list[str] = PASS_REQUIREMENTS[pass_type].get("required_files", [])
        return result

    def get_required_artifacts(self, pass_type: CompilerPassType) -> list[ArtifactType]:
        """Get list of required artifact types for a pass.

        Args:
            pass_type: The compiler pass type.

        Returns:
            List of required artifact types.
        """
        result: list[ArtifactType] = PASS_REQUIREMENTS[pass_type].get(
            "required_artifacts", []
        )
        return result

    def get_forbidden_inputs(self, pass_type: CompilerPassType) -> list[str]:
        """Get list of forbidden input types for a pass.

        Args:
            pass_type: The compiler pass type.

        Returns:
            List of forbidden input type names.
        """
        result: list[str] = PASS_REQUIREMENTS[pass_type].get("forbidden_inputs", [])
        return result
