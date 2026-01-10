"""Compiler pass base class.

This module provides the abstract base class for all compiler passes.
Each pass transforms inputs into a specific artifact type.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.ports.llm import LLMPort
from rice_factor.domain.prompts import PromptManager
from rice_factor.domain.prompts.schema_injector import SchemaInjector
from rice_factor.domain.services.context_builder import (
    ContextBuilder,
    ForbiddenInputError,
)
from rice_factor.domain.services.output_validator import OutputValidator


class CompilerPass(ABC):
    """Abstract base class for compiler passes.

    Each compiler pass transforms specific inputs into a single
    artifact type. Subclasses define their requirements and produce
    their specific output type.

    The compile() method is a template method that orchestrates:
    1. Context validation
    2. Prompt building
    3. LLM invocation
    4. Output validation
    """

    def __init__(
        self,
        schemas_dir: Path | None = None,
        *,
        check_code: bool = True,
    ) -> None:
        """Initialize the compiler pass.

        Args:
            schemas_dir: Path to JSON schemas directory.
            check_code: Whether to check for code in output.
        """
        self._schemas_dir = schemas_dir
        self._prompt_manager = PromptManager(schemas_dir)
        self._schema_injector = SchemaInjector(schemas_dir)
        self._output_validator = OutputValidator(schemas_dir, check_code=check_code)
        self._context_builder = ContextBuilder()

    @property
    @abstractmethod
    def pass_type(self) -> CompilerPassType:
        """Return the type of this compiler pass."""
        ...

    @property
    @abstractmethod
    def output_artifact_type(self) -> ArtifactType:
        """Return the artifact type produced by this pass."""
        ...

    @property
    def required_files(self) -> list[str]:
        """Return list of required project files.

        Override in subclasses to specify required files.
        """
        return self._context_builder.get_required_files(self.pass_type)

    @property
    def required_artifacts(self) -> list[ArtifactType]:
        """Return list of required artifact types.

        Override in subclasses to specify required artifacts.
        """
        return self._context_builder.get_required_artifacts(self.pass_type)

    @property
    def forbidden_inputs(self) -> list[str]:
        """Return list of forbidden input types.

        Override in subclasses to specify forbidden inputs.
        """
        return self._context_builder.get_forbidden_inputs(self.pass_type)

    def compile(
        self,
        context: CompilerContext,
        llm_port: LLMPort,
    ) -> CompilerResult:
        """Execute the compiler pass.

        This is the template method that orchestrates the compilation:
        1. Validate context
        2. Build prompt
        3. Get output schema
        4. Invoke LLM
        5. Validate output (if successful)

        Args:
            context: The compilation context.
            llm_port: The LLM port for generation.

        Returns:
            CompilerResult with payload or error.

        Raises:
            MissingRequiredInputError: If required inputs are missing.
            ForbiddenInputError: If forbidden inputs are detected.
        """
        # 1. Validate context
        self.validate_context(context)

        # 2. Build prompt (for logging/debugging)
        _prompt = self.build_prompt(context)

        # 3. Get output schema
        schema = self.get_output_schema()

        # 4. Invoke LLM
        result = llm_port.generate(self.pass_type, context, schema)

        # 5. Validate output if successful
        if result.success and result.payload is not None:
            self.validate_output(result.payload)

        return result

    def validate_context(self, context: CompilerContext) -> None:
        """Validate that context meets pass requirements.

        Args:
            context: The compilation context.

        Raises:
            MissingRequiredInputError: If required inputs are missing.
            ForbiddenInputError: If forbidden inputs are detected.
        """
        # Use ContextBuilder's validation
        self._context_builder.validate_inputs(self.pass_type, context)

        # Check forbidden inputs
        forbidden = self._context_builder.check_forbidden_inputs(
            self.pass_type, context
        )
        if forbidden:
            raise ForbiddenInputError(
                forbidden[0], f"Forbidden inputs found: {forbidden}"
            )

    def build_prompt(self, context: CompilerContext) -> str:
        """Build the complete prompt for this pass.

        Args:
            context: The compilation context.

        Returns:
            Complete prompt string.
        """
        return self._prompt_manager.get_full_prompt(
            self.pass_type, context, include_schema=True
        )

    def get_output_schema(self) -> dict[str, Any]:
        """Get the JSON schema for this pass's output.

        Returns:
            The JSON schema dictionary.
        """
        return self._schema_injector.load_schema(self.output_artifact_type)

    def validate_output(self, payload: dict[str, Any]) -> None:
        """Validate the output payload.

        Args:
            payload: The artifact payload to validate.

        Raises:
            SchemaViolationError: If payload doesn't match schema.
            CodeInOutputError: If payload contains code.
        """
        import json

        json_str = json.dumps(payload)
        self._output_validator.validate(json_str, self.output_artifact_type)
