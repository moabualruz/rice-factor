"""Test designer compiler pass.

This module provides the TestDesignerPass for generating
TestPlan artifacts.
"""

from pathlib import Path

from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass


class TestDesignerPass(CompilerPass):
    """Compiler pass for generating TestPlan artifacts.

    This pass takes approved project artifacts and requirements as input
    and produces a TestPlan artifact defining test specifications.

    IMPORTANT: TestPlan is LOCKED after approval and cannot be modified
    by automation. This ensures tests remain the source of truth.

    Required inputs:
    - ProjectPlan (approved): Base project structure
    - ArchitecturePlan (approved): Architectural decisions
    - ScaffoldPlan (approved): File structure
    - requirements.md: Original requirements

    Forbidden inputs:
    - None (needs full context for comprehensive tests)
    """

    def __init__(
        self,
        schemas_dir: Path | None = None,
        *,
        check_code: bool = True,
    ) -> None:
        """Initialize the test designer pass.

        Args:
            schemas_dir: Path to JSON schemas directory.
            check_code: Whether to check for code in output.
        """
        super().__init__(schemas_dir, check_code=check_code)

    @property
    def pass_type(self) -> CompilerPassType:
        """Return the type of this compiler pass."""
        return CompilerPassType.TEST

    @property
    def output_artifact_type(self) -> ArtifactType:
        """Return the artifact type produced by this pass."""
        return ArtifactType.TEST_PLAN
