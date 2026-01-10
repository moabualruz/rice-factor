"""Unit tests for ProjectPlannerPass."""

from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.passes.project_planner import ProjectPlannerPass


class TestProjectPlannerPassProperties:
    """Tests for ProjectPlannerPass properties."""

    @pytest.fixture
    def pass_instance(self) -> ProjectPlannerPass:
        """Create a ProjectPlannerPass instance."""
        return ProjectPlannerPass()

    def test_is_compiler_pass_subclass(
        self, pass_instance: ProjectPlannerPass
    ) -> None:
        """ProjectPlannerPass is a CompilerPass subclass."""
        assert isinstance(pass_instance, CompilerPass)

    def test_pass_type_is_project(self, pass_instance: ProjectPlannerPass) -> None:
        """pass_type returns PROJECT."""
        assert pass_instance.pass_type == CompilerPassType.PROJECT

    def test_output_artifact_type_is_project_plan(
        self, pass_instance: ProjectPlannerPass
    ) -> None:
        """output_artifact_type returns PROJECT_PLAN."""
        assert pass_instance.output_artifact_type == ArtifactType.PROJECT_PLAN


class TestProjectPlannerPassRequirements:
    """Tests for ProjectPlannerPass requirements."""

    @pytest.fixture
    def pass_instance(self) -> ProjectPlannerPass:
        """Create a ProjectPlannerPass instance."""
        return ProjectPlannerPass()

    def test_required_files_includes_requirements(
        self, pass_instance: ProjectPlannerPass
    ) -> None:
        """required_files includes requirements.md."""
        assert "requirements.md" in pass_instance.required_files

    def test_required_files_includes_constraints(
        self, pass_instance: ProjectPlannerPass
    ) -> None:
        """required_files includes constraints.md."""
        assert "constraints.md" in pass_instance.required_files

    def test_required_files_includes_glossary(
        self, pass_instance: ProjectPlannerPass
    ) -> None:
        """required_files includes glossary.md."""
        assert "glossary.md" in pass_instance.required_files

    def test_forbidden_inputs_includes_source_code(
        self, pass_instance: ProjectPlannerPass
    ) -> None:
        """forbidden_inputs includes source_code."""
        assert "source_code" in pass_instance.forbidden_inputs

    def test_forbidden_inputs_includes_tests(
        self, pass_instance: ProjectPlannerPass
    ) -> None:
        """forbidden_inputs includes tests."""
        assert "tests" in pass_instance.forbidden_inputs

    def test_forbidden_inputs_includes_existing_artifacts(
        self, pass_instance: ProjectPlannerPass
    ) -> None:
        """forbidden_inputs includes existing_artifacts."""
        assert "existing_artifacts" in pass_instance.forbidden_inputs


class TestProjectPlannerPassCompilation:
    """Tests for ProjectPlannerPass compilation."""

    @pytest.fixture
    def pass_instance(self) -> ProjectPlannerPass:
        """Create a ProjectPlannerPass instance."""
        return ProjectPlannerPass()

    @pytest.fixture
    def valid_context(self) -> CompilerContext:
        """Create a valid context for project planning."""
        return CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "# Requirements\n\nBuild a todo app.",
                "constraints.md": "# Constraints\n\nUse Python.",
                "glossary.md": "# Glossary\n\nTodo: A task to complete.",
            },
            artifacts={},
        )

    @pytest.fixture
    def mock_llm_port(self) -> MagicMock:
        """Create a mock LLM port with successful response."""
        mock = MagicMock()
        mock.generate.return_value = CompilerResult(
            success=True,
            payload={
                "domains": [{"name": "Todo", "responsibility": "Task management"}],
                "modules": [{"name": "core", "domain": "Todo"}],
                "constraints": {"architecture": "hexagonal", "languages": ["python"]},
            },
        )
        return mock

    def test_compile_with_valid_context_succeeds(
        self,
        pass_instance: ProjectPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile succeeds with valid context."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.success is True

    def test_compile_calls_llm_generate(
        self,
        pass_instance: ProjectPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile calls llm_port.generate."""
        pass_instance.compile(valid_context, mock_llm_port)
        mock_llm_port.generate.assert_called_once()

    def test_compile_passes_correct_pass_type_to_llm(
        self,
        pass_instance: ProjectPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile passes PROJECT pass type to LLM."""
        pass_instance.compile(valid_context, mock_llm_port)
        call_args = mock_llm_port.generate.call_args
        assert call_args[0][0] == CompilerPassType.PROJECT

    def test_compile_returns_payload_on_success(
        self,
        pass_instance: ProjectPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns payload on success."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.payload is not None
        assert "domains" in result.payload

    def test_compile_returns_error_on_failure(
        self,
        pass_instance: ProjectPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns error on LLM failure."""
        mock_llm_port.generate.return_value = CompilerResult(
            success=False,
            error_type="missing_information",
            error_details="Could not determine domain boundaries",
        )
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.success is False
        assert result.error_type == "missing_information"
