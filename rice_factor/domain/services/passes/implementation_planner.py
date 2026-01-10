"""Implementation planner compiler pass.

This module provides the ImplementationPlannerPass for generating
ImplementationPlan artifacts.
"""

from pathlib import Path

from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass


class ImplementationPlannerPass(CompilerPass):
    """Compiler pass for generating ImplementationPlan artifacts.

    This pass takes approved test and scaffold plans plus a target file
    as input and produces an ImplementationPlan artifact defining the
    implementation steps for a single file.

    IMPORTANT: This pass uses TINY context (only target file + relevant
    tests) to ensure focused, correct implementations. It must NOT
    see other source files to avoid cross-contamination.

    Required inputs:
    - TestPlan (approved): Test specifications
    - ScaffoldPlan (approved): File structure
    - target_file: The specific file to implement

    Forbidden inputs:
    - all_other_source_files: Must not see other implementations
    """

    def __init__(
        self,
        schemas_dir: Path | None = None,
        *,
        check_code: bool = True,
    ) -> None:
        """Initialize the implementation planner pass.

        Args:
            schemas_dir: Path to JSON schemas directory.
            check_code: Whether to check for code in output.
        """
        super().__init__(schemas_dir, check_code=check_code)

    @property
    def pass_type(self) -> CompilerPassType:
        """Return the type of this compiler pass."""
        return CompilerPassType.IMPLEMENTATION

    @property
    def output_artifact_type(self) -> ArtifactType:
        """Return the artifact type produced by this pass."""
        return ArtifactType.IMPLEMENTATION_PLAN
