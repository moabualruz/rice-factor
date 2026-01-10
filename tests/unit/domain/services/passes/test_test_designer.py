"""Unit tests for TestDesignerPass."""

from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.passes.test_designer import TestDesignerPass


class TestTestDesignerPassProperties:
    """Tests for TestDesignerPass properties."""

    @pytest.fixture
    def pass_instance(self) -> TestDesignerPass:
        """Create a TestDesignerPass instance."""
        return TestDesignerPass()

    def test_is_compiler_pass_subclass(
        self, pass_instance: TestDesignerPass
    ) -> None:
        """TestDesignerPass is a CompilerPass subclass."""
        assert isinstance(pass_instance, CompilerPass)

    def test_pass_type_is_test(self, pass_instance: TestDesignerPass) -> None:
        """pass_type returns TEST."""
        assert pass_instance.pass_type == CompilerPassType.TEST

    def test_output_artifact_type_is_test_plan(
        self, pass_instance: TestDesignerPass
    ) -> None:
        """output_artifact_type returns TEST_PLAN."""
        assert pass_instance.output_artifact_type == ArtifactType.TEST_PLAN


class TestTestDesignerPassRequirements:
    """Tests for TestDesignerPass requirements."""

    @pytest.fixture
    def pass_instance(self) -> TestDesignerPass:
        """Create a TestDesignerPass instance."""
        return TestDesignerPass()

    def test_required_files_includes_requirements(
        self, pass_instance: TestDesignerPass
    ) -> None:
        """required_files includes requirements.md."""
        assert "requirements.md" in pass_instance.required_files

    def test_required_artifacts_includes_project_plan(
        self, pass_instance: TestDesignerPass
    ) -> None:
        """required_artifacts includes PROJECT_PLAN."""
        assert ArtifactType.PROJECT_PLAN in pass_instance.required_artifacts

    def test_required_artifacts_includes_architecture_plan(
        self, pass_instance: TestDesignerPass
    ) -> None:
        """required_artifacts includes ARCHITECTURE_PLAN."""
        assert ArtifactType.ARCHITECTURE_PLAN in pass_instance.required_artifacts

    def test_required_artifacts_includes_scaffold_plan(
        self, pass_instance: TestDesignerPass
    ) -> None:
        """required_artifacts includes SCAFFOLD_PLAN."""
        assert ArtifactType.SCAFFOLD_PLAN in pass_instance.required_artifacts

    def test_forbidden_inputs_is_empty(
        self, pass_instance: TestDesignerPass
    ) -> None:
        """forbidden_inputs is empty for test pass."""
        assert len(pass_instance.forbidden_inputs) == 0


class TestTestDesignerPassCompilation:
    """Tests for TestDesignerPass compilation."""

    @pytest.fixture
    def pass_instance(self) -> TestDesignerPass:
        """Create a TestDesignerPass instance."""
        return TestDesignerPass()

    @pytest.fixture
    def valid_context(self) -> CompilerContext:
        """Create a valid context for test design."""
        return CompilerContext(
            pass_type=CompilerPassType.TEST,
            project_files={
                "requirements.md": "# Requirements\n\nBuild a todo app.",
            },
            artifacts={
                "project-plan-1": {"domains": [], "modules": [], "constraints": {}},
                "architecture-plan-1": {"layers": [], "rules": []},
                "scaffold-plan-1": {"files": []},
            },
        )

    @pytest.fixture
    def mock_llm_port(self) -> MagicMock:
        """Create a mock LLM port with successful response."""
        mock = MagicMock()
        mock.generate.return_value = CompilerResult(
            success=True,
            payload={
                "tests": [
                    {
                        "id": "test_todo_create",
                        "target": "todo.create",
                        "assertions": ["Should create a new todo item"],
                    }
                ]
            },
        )
        return mock

    def test_compile_with_valid_context_succeeds(
        self,
        pass_instance: TestDesignerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile succeeds with valid context."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.success is True

    def test_compile_passes_correct_pass_type_to_llm(
        self,
        pass_instance: TestDesignerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile passes TEST pass type to LLM."""
        pass_instance.compile(valid_context, mock_llm_port)
        call_args = mock_llm_port.generate.call_args
        assert call_args[0][0] == CompilerPassType.TEST

    def test_compile_returns_payload_with_tests(
        self,
        pass_instance: TestDesignerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns payload with tests."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.payload is not None
        assert "tests" in result.payload
