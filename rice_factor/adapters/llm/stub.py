"""Stub LLM adapter for development and testing.

This adapter returns placeholder plan payloads without calling a real LLM.
Used during development to test the CLI workflow before LLM integration.
"""

from rice_factor.domain.artifacts.payloads.architecture_plan import (
    ArchitecturePlanPayload,
    ArchitectureRule,
    DependencyRule,
)
from rice_factor.domain.artifacts.payloads.implementation_plan import (
    ImplementationPlanPayload,
)
from rice_factor.domain.artifacts.payloads.project_plan import (
    Architecture,
    Constraints,
    Domain,
    Module,
    ProjectPlanPayload,
)
from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorConstraints,
    RefactorOperation,
    RefactorOperationType,
    RefactorPlanPayload,
)
from rice_factor.domain.artifacts.payloads.scaffold_plan import (
    FileEntry,
    FileKind,
    ScaffoldPlanPayload,
)
from rice_factor.domain.artifacts.payloads.test_plan import (
    TestDefinition,
    TestPlanPayload,
)


class StubLLMAdapter:
    """Stub LLM adapter that returns placeholder plan payloads.

    This adapter is used during development and testing to provide
    valid plan payloads without requiring a real LLM connection.
    All generated payloads include minimal but valid data.
    """

    def generate_project_plan(self) -> ProjectPlanPayload:
        """Generate a stub ProjectPlan payload.

        Returns:
            ProjectPlanPayload with placeholder domain, module, and constraints.
        """
        return ProjectPlanPayload(
            domains=[
                Domain(
                    name="core",
                    responsibility="Core business logic and domain models",
                ),
            ],
            modules=[
                Module(
                    name="main",
                    domain="core",
                ),
            ],
            constraints=Constraints(
                architecture=Architecture.HEXAGONAL,
                languages=["Python"],
            ),
        )

    def generate_architecture_plan(self) -> ArchitecturePlanPayload:
        """Generate a stub ArchitecturePlan payload.

        Returns:
            ArchitecturePlanPayload with placeholder layers and rules.
        """
        return ArchitecturePlanPayload(
            layers=["domain", "adapters", "entrypoints"],
            rules=[
                ArchitectureRule(
                    rule=DependencyRule.DOMAIN_CANNOT_IMPORT_INFRASTRUCTURE,
                ),
            ],
        )

    def generate_test_plan(self) -> TestPlanPayload:
        """Generate a stub TestPlan payload.

        Returns:
            TestPlanPayload with placeholder test definitions.
        """
        return TestPlanPayload(
            tests=[
                TestDefinition(
                    id="test_stub_001",
                    target="stub_module",
                    assertions=["Stub assertion - replace with actual tests"],
                ),
            ],
        )

    def generate_implementation_plan(self, target: str) -> ImplementationPlanPayload:
        """Generate a stub ImplementationPlan payload.

        Args:
            target: The target file to implement.

        Returns:
            ImplementationPlanPayload with placeholder steps for the target.
        """
        return ImplementationPlanPayload(
            target=target,
            steps=[
                f"Create {target} file structure",
                "Implement core functionality",
                "Add error handling",
                "Document public API",
            ],
            related_tests=[],
        )

    def generate_scaffold_plan(self) -> ScaffoldPlanPayload:
        """Generate a stub ScaffoldPlan payload.

        Returns:
            ScaffoldPlanPayload with placeholder file entries.
        """
        return ScaffoldPlanPayload(
            files=[
                FileEntry(
                    path="src/__init__.py",
                    description="Package initialization",
                    kind=FileKind.SOURCE,
                ),
                FileEntry(
                    path="src/main.py",
                    description="Application entry point",
                    kind=FileKind.SOURCE,
                ),
                FileEntry(
                    path="tests/__init__.py",
                    description="Test package initialization",
                    kind=FileKind.TEST,
                ),
                FileEntry(
                    path="tests/test_main.py",
                    description="Tests for main module",
                    kind=FileKind.TEST,
                ),
                FileEntry(
                    path="README.md",
                    description="Project documentation",
                    kind=FileKind.DOC,
                ),
            ],
        )

    def generate_refactor_plan(self, goal: str) -> RefactorPlanPayload:
        """Generate a stub RefactorPlan payload.

        Args:
            goal: The refactoring goal.

        Returns:
            RefactorPlanPayload with placeholder operations for the goal.
        """
        return RefactorPlanPayload(
            goal=goal,
            operations=[
                RefactorOperation(
                    type=RefactorOperationType.RENAME_SYMBOL,
                    symbol="placeholder_symbol",
                ),
            ],
            constraints=RefactorConstraints(
                preserve_behavior=True,
            ),
        )
