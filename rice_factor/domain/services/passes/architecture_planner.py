"""Architecture planner compiler pass.

This module provides the ArchitecturePlannerPass for generating
ArchitecturePlan artifacts.
"""

from pathlib import Path

from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass


class ArchitecturePlannerPass(CompilerPass):
    """Compiler pass for generating ArchitecturePlan artifacts.

    This pass takes an approved ProjectPlan and constraints as input
    and produces an ArchitecturePlan artifact defining layers,
    components, and architectural rules.

    Required inputs:
    - ProjectPlan (approved): Base project structure
    - constraints.md: Project constraints document

    Forbidden inputs:
    - None (inherits project context)
    """

    def __init__(
        self,
        schemas_dir: Path | None = None,
        *,
        check_code: bool = True,
    ) -> None:
        """Initialize the architecture planner pass.

        Args:
            schemas_dir: Path to JSON schemas directory.
            check_code: Whether to check for code in output.
        """
        super().__init__(schemas_dir, check_code=check_code)

    @property
    def pass_type(self) -> CompilerPassType:
        """Return the type of this compiler pass."""
        return CompilerPassType.ARCHITECTURE

    @property
    def output_artifact_type(self) -> ArtifactType:
        """Return the artifact type produced by this pass."""
        return ArtifactType.ARCHITECTURE_PLAN
