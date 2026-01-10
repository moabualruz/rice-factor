"""Prompt management for artifact builders.

This module provides the PromptManager class for managing system prompts
for all compiler passes, as well as the individual pass prompts.
"""

from pathlib import Path
from typing import Any

from rice_factor.domain.artifacts.compiler_types import CompilerContext, CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.prompts.architecture_planner import ARCHITECTURE_PLANNER_PROMPT
from rice_factor.domain.prompts.base import (
    BASE_SYSTEM_PROMPT,
    FAILURE_FORMAT_INVALID_REQUEST,
    FAILURE_FORMAT_MISSING_INFO,
    HARD_CONTRACT_RULES,
)
from rice_factor.domain.prompts.implementation_planner import (
    IMPLEMENTATION_PLANNER_PROMPT,
)
from rice_factor.domain.prompts.project_planner import PROJECT_PLANNER_PROMPT
from rice_factor.domain.prompts.refactor_planner import REFACTOR_PLANNER_PROMPT
from rice_factor.domain.prompts.scaffold_planner import SCAFFOLD_PLANNER_PROMPT
from rice_factor.domain.prompts.schema_injector import (
    SchemaInjector,
    SchemaNotFoundError,
)
from rice_factor.domain.prompts.test_designer import TEST_DESIGNER_PROMPT

# Mapping from CompilerPassType to artifact type
PASS_TO_ARTIFACT: dict[CompilerPassType, ArtifactType] = {
    CompilerPassType.PROJECT: ArtifactType.PROJECT_PLAN,
    CompilerPassType.ARCHITECTURE: ArtifactType.ARCHITECTURE_PLAN,
    CompilerPassType.SCAFFOLD: ArtifactType.SCAFFOLD_PLAN,
    CompilerPassType.TEST: ArtifactType.TEST_PLAN,
    CompilerPassType.IMPLEMENTATION: ArtifactType.IMPLEMENTATION_PLAN,
    CompilerPassType.REFACTOR: ArtifactType.REFACTOR_PLAN,
}

# Mapping from CompilerPassType to pass-specific prompt
PASS_PROMPTS: dict[CompilerPassType, str] = {
    CompilerPassType.PROJECT: PROJECT_PLANNER_PROMPT,
    CompilerPassType.ARCHITECTURE: ARCHITECTURE_PLANNER_PROMPT,
    CompilerPassType.SCAFFOLD: SCAFFOLD_PLANNER_PROMPT,
    CompilerPassType.TEST: TEST_DESIGNER_PROMPT,
    CompilerPassType.IMPLEMENTATION: IMPLEMENTATION_PLANNER_PROMPT,
    CompilerPassType.REFACTOR: REFACTOR_PLANNER_PROMPT,
}


class PromptManager:
    """Manager for artifact builder prompts.

    Provides methods to access and combine prompts for compiler passes.
    """

    def __init__(self, schemas_dir: Path | None = None) -> None:
        """Initialize the prompt manager.

        Args:
            schemas_dir: Path to schemas directory. If None, uses default.
        """
        self._schema_injector = SchemaInjector(schemas_dir)

    def get_base_prompt(self) -> str:
        """Get the canonical base system prompt.

        This prompt applies to ALL artifact builder passes and NEVER changes.

        Returns:
            The base system prompt string.
        """
        return BASE_SYSTEM_PROMPT

    def get_pass_prompt(self, pass_type: CompilerPassType) -> str:
        """Get the pass-specific prompt for a compiler pass.

        Args:
            pass_type: The compiler pass type.

        Returns:
            The pass-specific prompt string.

        Raises:
            KeyError: If pass_type is not recognized.
        """
        return PASS_PROMPTS[pass_type]

    def get_system_prompt(self, pass_type: CompilerPassType) -> str:
        """Get the combined system prompt for a pass.

        Combines the base system prompt with the pass-specific prompt.

        Args:
            pass_type: The compiler pass type.

        Returns:
            Combined system prompt (base + pass-specific).
        """
        base = self.get_base_prompt()
        pass_prompt = self.get_pass_prompt(pass_type)
        return f"{base}\n\n{pass_prompt}"

    def get_full_prompt(
        self,
        pass_type: CompilerPassType,
        context: CompilerContext | None = None,
        include_schema: bool = True,
    ) -> str:
        """Get a complete prompt ready for LLM invocation.

        Combines:
        1. Base system prompt
        2. Pass-specific prompt
        3. Schema (if include_schema is True)
        4. Context (if provided)

        Args:
            pass_type: The compiler pass type.
            context: Optional compilation context with files and artifacts.
            include_schema: Whether to include the JSON schema.

        Returns:
            Complete prompt string ready for LLM invocation.
        """
        prompt = self.get_system_prompt(pass_type)

        # Add schema if requested
        if include_schema:
            artifact_type = PASS_TO_ARTIFACT.get(pass_type)
            if artifact_type is not None:
                try:
                    schema_str = self._schema_injector.format_schema_for_prompt(
                        artifact_type
                    )
                    prompt = f"{prompt}\n\nJSON SCHEMA:\n```json\n{schema_str}\n```\n\nYour output MUST conform exactly to this schema."
                except SchemaNotFoundError:
                    # Schema not available - continue without it
                    pass

        # Add context if provided
        if context is not None:
            prompt = f"{prompt}\n\n{self._format_context(context)}"

        return prompt

    def _format_context(self, context: CompilerContext) -> str:
        """Format compilation context for inclusion in prompt.

        Args:
            context: The compilation context.

        Returns:
            Formatted context string.
        """
        parts = ["CONTEXT:"]

        # Add project files
        if context.project_files:
            parts.append("\nPROJECT FILES:")
            for filename, content in context.project_files.items():
                parts.append(f"\n--- {filename} ---")
                parts.append(content)

        # Add artifacts
        if context.artifacts:
            parts.append("\nARTIFACTS:")
            for artifact_id, payload in context.artifacts.items():
                parts.append(f"\n--- Artifact: {artifact_id} ---")
                if isinstance(payload, dict):
                    import json

                    parts.append(json.dumps(payload, indent=2))
                else:
                    parts.append(str(payload))

        # Add target file if present
        if context.target_file:
            parts.append(f"\nTARGET FILE: {context.target_file}")

        return "\n".join(parts)

    def get_artifact_type_for_pass(
        self, pass_type: CompilerPassType
    ) -> ArtifactType | None:
        """Get the artifact type produced by a pass.

        Args:
            pass_type: The compiler pass type.

        Returns:
            The artifact type, or None if not mapped.
        """
        return PASS_TO_ARTIFACT.get(pass_type)


def format_context_section(
    project_files: dict[str, str] | None = None,
    artifacts: dict[str, Any] | None = None,
    target_file: str | None = None,
) -> str:
    """Format context information for inclusion in a prompt.

    This is a convenience function for building context sections.

    Args:
        project_files: Dict of filename to content.
        artifacts: Dict of artifact ID to payload.
        target_file: Optional target file path.

    Returns:
        Formatted context string.
    """
    context = CompilerContext(
        pass_type=CompilerPassType.PROJECT,  # Doesn't matter for formatting
        project_files=project_files or {},
        artifacts=artifacts or {},
        target_file=target_file,
    )
    manager = PromptManager()
    return manager._format_context(context)


__all__ = [
    "ARCHITECTURE_PLANNER_PROMPT",
    "BASE_SYSTEM_PROMPT",
    "FAILURE_FORMAT_INVALID_REQUEST",
    "FAILURE_FORMAT_MISSING_INFO",
    "HARD_CONTRACT_RULES",
    "IMPLEMENTATION_PLANNER_PROMPT",
    "PASS_PROMPTS",
    "PASS_TO_ARTIFACT",
    "PROJECT_PLANNER_PROMPT",
    "REFACTOR_PLANNER_PROMPT",
    "SCAFFOLD_PLANNER_PROMPT",
    "TEST_DESIGNER_PROMPT",
    "PromptManager",
    "SchemaInjector",
    "SchemaNotFoundError",
    "format_context_section",
]
