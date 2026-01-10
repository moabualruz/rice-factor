"""Project planner compiler pass.

This module provides the ProjectPlannerPass for generating ProjectPlan artifacts.
"""

from pathlib import Path

from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass


class ProjectPlannerPass(CompilerPass):
    """Compiler pass for generating ProjectPlan artifacts.

    This pass takes project requirements, constraints, and glossary
    as input and produces a ProjectPlan artifact defining domains,
    modules, and constraints.

    Required inputs:
    - requirements.md: Project requirements document
    - constraints.md: Project constraints document
    - glossary.md: Domain glossary document

    Forbidden inputs:
    - source_code: Should not see implementation details
    - tests: Should not be influenced by existing tests
    - existing_artifacts: Fresh generation required
    """

    def __init__(
        self,
        schemas_dir: Path | None = None,
        *,
        check_code: bool = True,
    ) -> None:
        """Initialize the project planner pass.

        Args:
            schemas_dir: Path to JSON schemas directory.
            check_code: Whether to check for code in output.
        """
        super().__init__(schemas_dir, check_code=check_code)

    @property
    def pass_type(self) -> CompilerPassType:
        """Return the type of this compiler pass."""
        return CompilerPassType.PROJECT

    @property
    def output_artifact_type(self) -> ArtifactType:
        """Return the artifact type produced by this pass."""
        return ArtifactType.PROJECT_PLAN
