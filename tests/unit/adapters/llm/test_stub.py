"""Unit tests for StubLLMAdapter."""

from rice_factor.adapters.llm.stub import StubLLMAdapter
from rice_factor.domain.artifacts.payloads.architecture_plan import (
    ArchitecturePlanPayload,
    DependencyRule,
)
from rice_factor.domain.artifacts.payloads.implementation_plan import (
    ImplementationPlanPayload,
)
from rice_factor.domain.artifacts.payloads.project_plan import (
    Architecture,
    ProjectPlanPayload,
)
from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorOperationType,
    RefactorPlanPayload,
)
from rice_factor.domain.artifacts.payloads.scaffold_plan import (
    FileKind,
    ScaffoldPlanPayload,
)
from rice_factor.domain.artifacts.payloads.test_plan import TestPlanPayload


class TestStubLLMAdapterInit:
    """Tests for StubLLMAdapter initialization."""

    def test_can_instantiate(self) -> None:
        """StubLLMAdapter should be instantiable."""
        adapter = StubLLMAdapter()
        assert adapter is not None


class TestGenerateProjectPlan:
    """Tests for generate_project_plan method."""

    def test_returns_project_plan_payload(self) -> None:
        """generate_project_plan should return a ProjectPlanPayload."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_project_plan()
        assert isinstance(payload, ProjectPlanPayload)

    def test_has_at_least_one_domain(self) -> None:
        """generate_project_plan should include at least one domain."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_project_plan()
        assert len(payload.domains) >= 1

    def test_has_at_least_one_module(self) -> None:
        """generate_project_plan should include at least one module."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_project_plan()
        assert len(payload.modules) >= 1

    def test_has_constraints(self) -> None:
        """generate_project_plan should include constraints."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_project_plan()
        assert payload.constraints is not None
        assert isinstance(payload.constraints.architecture, Architecture)
        assert len(payload.constraints.languages) >= 1


class TestGenerateArchitecturePlan:
    """Tests for generate_architecture_plan method."""

    def test_returns_architecture_plan_payload(self) -> None:
        """generate_architecture_plan should return an ArchitecturePlanPayload."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_architecture_plan()
        assert isinstance(payload, ArchitecturePlanPayload)

    def test_has_at_least_one_layer(self) -> None:
        """generate_architecture_plan should include at least one layer."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_architecture_plan()
        assert len(payload.layers) >= 1

    def test_has_rules(self) -> None:
        """generate_architecture_plan should include rules."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_architecture_plan()
        assert len(payload.rules) >= 1

    def test_rules_have_valid_type(self) -> None:
        """generate_architecture_plan rules should have valid DependencyRule type."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_architecture_plan()
        for rule in payload.rules:
            assert isinstance(rule.rule, DependencyRule)


class TestGenerateTestPlan:
    """Tests for generate_test_plan method."""

    def test_returns_test_plan_payload(self) -> None:
        """generate_test_plan should return a TestPlanPayload."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_test_plan()
        assert isinstance(payload, TestPlanPayload)

    def test_has_at_least_one_test(self) -> None:
        """generate_test_plan should include at least one test."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_test_plan()
        assert len(payload.tests) >= 1

    def test_tests_have_required_fields(self) -> None:
        """generate_test_plan tests should have id, target, and assertions."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_test_plan()
        for test in payload.tests:
            assert test.id
            assert test.target
            assert len(test.assertions) >= 1


class TestGenerateImplementationPlan:
    """Tests for generate_implementation_plan method."""

    def test_returns_implementation_plan_payload(self) -> None:
        """generate_implementation_plan should return an ImplementationPlanPayload."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_implementation_plan("src/main.py")
        assert isinstance(payload, ImplementationPlanPayload)

    def test_includes_target(self) -> None:
        """generate_implementation_plan should include the target file."""
        adapter = StubLLMAdapter()
        target = "src/services/user_service.py"
        payload = adapter.generate_implementation_plan(target)
        assert payload.target == target

    def test_has_at_least_one_step(self) -> None:
        """generate_implementation_plan should include at least one step."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_implementation_plan("src/main.py")
        assert len(payload.steps) >= 1

    def test_steps_are_strings(self) -> None:
        """generate_implementation_plan steps should be strings."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_implementation_plan("src/main.py")
        for step in payload.steps:
            assert isinstance(step, str)
            assert len(step) > 0


class TestGenerateRefactorPlan:
    """Tests for generate_refactor_plan method."""

    def test_returns_refactor_plan_payload(self) -> None:
        """generate_refactor_plan should return a RefactorPlanPayload."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_refactor_plan("Extract interface for service")
        assert isinstance(payload, RefactorPlanPayload)

    def test_includes_goal(self) -> None:
        """generate_refactor_plan should include the goal."""
        adapter = StubLLMAdapter()
        goal = "Move utility functions to shared module"
        payload = adapter.generate_refactor_plan(goal)
        assert payload.goal == goal

    def test_has_at_least_one_operation(self) -> None:
        """generate_refactor_plan should include at least one operation."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_refactor_plan("Refactor code")
        assert len(payload.operations) >= 1

    def test_operations_have_valid_type(self) -> None:
        """generate_refactor_plan operations should have valid operation type."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_refactor_plan("Refactor code")
        for op in payload.operations:
            assert isinstance(op.type, RefactorOperationType)

    def test_has_constraints(self) -> None:
        """generate_refactor_plan should include constraints."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_refactor_plan("Refactor code")
        assert payload.constraints is not None
        assert payload.constraints.preserve_behavior is True


class TestGenerateScaffoldPlan:
    """Tests for generate_scaffold_plan method."""

    def test_returns_scaffold_plan_payload(self) -> None:
        """generate_scaffold_plan should return a ScaffoldPlanPayload."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_scaffold_plan()
        assert isinstance(payload, ScaffoldPlanPayload)

    def test_has_at_least_one_file(self) -> None:
        """generate_scaffold_plan should include at least one file."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_scaffold_plan()
        assert len(payload.files) >= 1

    def test_files_have_required_fields(self) -> None:
        """generate_scaffold_plan files should have path, description, and kind."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_scaffold_plan()
        for file in payload.files:
            assert file.path
            assert file.description
            assert isinstance(file.kind, FileKind)

    def test_includes_source_files(self) -> None:
        """generate_scaffold_plan should include source files."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_scaffold_plan()
        source_files = [f for f in payload.files if f.kind == FileKind.SOURCE]
        assert len(source_files) >= 1

    def test_includes_test_files(self) -> None:
        """generate_scaffold_plan should include test files."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_scaffold_plan()
        test_files = [f for f in payload.files if f.kind == FileKind.TEST]
        assert len(test_files) >= 1

    def test_includes_doc_file(self) -> None:
        """generate_scaffold_plan should include documentation files."""
        adapter = StubLLMAdapter()
        payload = adapter.generate_scaffold_plan()
        doc_files = [f for f in payload.files if f.kind == FileKind.DOC]
        assert len(doc_files) >= 1
