"""Scaffold planner compiler pass.

This module provides the ScaffoldPlannerPass for generating
ScaffoldPlan artifacts.
"""

from pathlib import Path

from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass


class ScaffoldPlannerPass(CompilerPass):
    """Compiler pass for generating ScaffoldPlan artifacts.

    This pass takes approved ProjectPlan and ArchitecturePlan as input
    and produces a ScaffoldPlan artifact defining the file structure
    to be created.

    Required inputs:
    - ProjectPlan (approved): Base project structure
    - ArchitecturePlan (approved): Architectural decisions

    Forbidden inputs:
    - None (builds on previous artifacts)
    """

    def __init__(
        self,
        schemas_dir: Path | None = None,
        *,
        check_code: bool = True,
    ) -> None:
        """Initialize the scaffold planner pass.

        Args:
            schemas_dir: Path to JSON schemas directory.
            check_code: Whether to check for code in output.
        """
        super().__init__(schemas_dir, check_code=check_code)

    @property
    def pass_type(self) -> CompilerPassType:
        """Return the type of this compiler pass."""
        return CompilerPassType.SCAFFOLD

    @property
    def output_artifact_type(self) -> ArtifactType:
        """Return the artifact type produced by this pass."""
        return ArtifactType.SCAFFOLD_PLAN
