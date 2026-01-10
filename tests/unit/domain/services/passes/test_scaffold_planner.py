"""Unit tests for ScaffoldPlannerPass."""

from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.passes.scaffold_planner import ScaffoldPlannerPass


class TestScaffoldPlannerPassProperties:
    """Tests for ScaffoldPlannerPass properties."""

    @pytest.fixture
    def pass_instance(self) -> ScaffoldPlannerPass:
        """Create a ScaffoldPlannerPass instance."""
        return ScaffoldPlannerPass()

    def test_is_compiler_pass_subclass(
        self, pass_instance: ScaffoldPlannerPass
    ) -> None:
        """ScaffoldPlannerPass is a CompilerPass subclass."""
        assert isinstance(pass_instance, CompilerPass)

    def test_pass_type_is_scaffold(self, pass_instance: ScaffoldPlannerPass) -> None:
        """pass_type returns SCAFFOLD."""
        assert pass_instance.pass_type == CompilerPassType.SCAFFOLD

    def test_output_artifact_type_is_scaffold_plan(
        self, pass_instance: ScaffoldPlannerPass
    ) -> None:
        """output_artifact_type returns SCAFFOLD_PLAN."""
        assert pass_instance.output_artifact_type == ArtifactType.SCAFFOLD_PLAN


class TestScaffoldPlannerPassRequirements:
    """Tests for ScaffoldPlannerPass requirements."""

    @pytest.fixture
    def pass_instance(self) -> ScaffoldPlannerPass:
        """Create a ScaffoldPlannerPass instance."""
        return ScaffoldPlannerPass()

    def test_required_artifacts_includes_project_plan(
        self, pass_instance: ScaffoldPlannerPass
    ) -> None:
        """required_artifacts includes PROJECT_PLAN."""
        assert ArtifactType.PROJECT_PLAN in pass_instance.required_artifacts

    def test_required_artifacts_includes_architecture_plan(
        self, pass_instance: ScaffoldPlannerPass
    ) -> None:
        """required_artifacts includes ARCHITECTURE_PLAN."""
        assert ArtifactType.ARCHITECTURE_PLAN in pass_instance.required_artifacts

    def test_forbidden_inputs_is_empty(
        self, pass_instance: ScaffoldPlannerPass
    ) -> None:
        """forbidden_inputs is empty for scaffold pass."""
        assert len(pass_instance.forbidden_inputs) == 0


class TestScaffoldPlannerPassCompilation:
    """Tests for ScaffoldPlannerPass compilation."""

    @pytest.fixture
    def pass_instance(self) -> ScaffoldPlannerPass:
        """Create a ScaffoldPlannerPass instance."""
        return ScaffoldPlannerPass()

    @pytest.fixture
    def valid_context(self) -> CompilerContext:
        """Create a valid context for scaffold planning."""
        return CompilerContext(
            pass_type=CompilerPassType.SCAFFOLD,
            project_files={},
            artifacts={
                "project-plan-1": {
                    "domains": [{"name": "Core", "responsibility": "Core logic"}],
                    "modules": [{"name": "core", "domain": "Core"}],
                    "constraints": {"architecture": "hexagonal", "languages": ["python"]},
                },
                "architecture-plan-1": {
                    "layers": ["domain", "application", "infrastructure"],
                    "rules": [{"rule": "domain_no_imports"}],
                },
            },
        )

    @pytest.fixture
    def mock_llm_port(self) -> MagicMock:
        """Create a mock LLM port with successful response."""
        mock = MagicMock()
        mock.generate.return_value = CompilerResult(
            success=True,
            payload={
                "files": [
                    {"path": "src/domain/core.py", "description": "Core domain", "kind": "source"},
                    {"path": "tests/test_core.py", "description": "Core tests", "kind": "test"},
                ]
            },
        )
        return mock

    def test_compile_with_valid_context_succeeds(
        self,
        pass_instance: ScaffoldPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile succeeds with valid context."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.success is True

    def test_compile_passes_correct_pass_type_to_llm(
        self,
        pass_instance: ScaffoldPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile passes SCAFFOLD pass type to LLM."""
        pass_instance.compile(valid_context, mock_llm_port)
        call_args = mock_llm_port.generate.call_args
        assert call_args[0][0] == CompilerPassType.SCAFFOLD

    def test_compile_returns_payload_with_files(
        self,
        pass_instance: ScaffoldPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns payload with files."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.payload is not None
        assert "files" in result.payload
