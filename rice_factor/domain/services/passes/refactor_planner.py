"""Refactor planner compiler pass.

This module provides the RefactorPlannerPass for generating
RefactorPlan artifacts.
"""

from pathlib import Path

from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass


class RefactorPlannerPass(CompilerPass):
    """Compiler pass for generating RefactorPlan artifacts.

    This pass takes architectural context and repository layout as input
    and produces a RefactorPlan artifact defining refactoring operations.

    IMPORTANT: Refactoring must preserve locked tests. The TestPlan
    remains immutable throughout the refactoring process.

    Required inputs:
    - ArchitecturePlan (approved): Architectural rules to maintain
    - TestPlan (locked): Tests that must pass after refactor
    - repo_layout: Current repository structure

    Forbidden inputs:
    - None (needs full context for safe refactoring)
    """

    def __init__(
        self,
        schemas_dir: Path | None = None,
        *,
        check_code: bool = True,
    ) -> None:
        """Initialize the refactor planner pass.

        Args:
            schemas_dir: Path to JSON schemas directory.
            check_code: Whether to check for code in output.
        """
        super().__init__(schemas_dir, check_code=check_code)

    @property
    def pass_type(self) -> CompilerPassType:
        """Return the type of this compiler pass."""
        return CompilerPassType.REFACTOR

    @property
    def output_artifact_type(self) -> ArtifactType:
        """Return the artifact type produced by this pass."""
        return ArtifactType.REFACTOR_PLAN
