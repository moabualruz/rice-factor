"""Unit tests for RefactorPlannerPass."""

from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.passes.refactor_planner import RefactorPlannerPass


class TestRefactorPlannerPassProperties:
    """Tests for RefactorPlannerPass properties."""

    @pytest.fixture
    def pass_instance(self) -> RefactorPlannerPass:
        """Create a RefactorPlannerPass instance."""
        return RefactorPlannerPass()

    def test_is_compiler_pass_subclass(
        self, pass_instance: RefactorPlannerPass
    ) -> None:
        """RefactorPlannerPass is a CompilerPass subclass."""
        assert isinstance(pass_instance, CompilerPass)

    def test_pass_type_is_refactor(self, pass_instance: RefactorPlannerPass) -> None:
        """pass_type returns REFACTOR."""
        assert pass_instance.pass_type == CompilerPassType.REFACTOR

    def test_output_artifact_type_is_refactor_plan(
        self, pass_instance: RefactorPlannerPass
    ) -> None:
        """output_artifact_type returns REFACTOR_PLAN."""
        assert pass_instance.output_artifact_type == ArtifactType.REFACTOR_PLAN


class TestRefactorPlannerPassRequirements:
    """Tests for RefactorPlannerPass requirements."""

    @pytest.fixture
    def pass_instance(self) -> RefactorPlannerPass:
        """Create a RefactorPlannerPass instance."""
        return RefactorPlannerPass()

    def test_required_artifacts_includes_architecture_plan(
        self, pass_instance: RefactorPlannerPass
    ) -> None:
        """required_artifacts includes ARCHITECTURE_PLAN."""
        assert ArtifactType.ARCHITECTURE_PLAN in pass_instance.required_artifacts

    def test_required_artifacts_includes_test_plan(
        self, pass_instance: RefactorPlannerPass
    ) -> None:
        """required_artifacts includes TEST_PLAN (locked)."""
        assert ArtifactType.TEST_PLAN in pass_instance.required_artifacts

    def test_forbidden_inputs_is_empty(
        self, pass_instance: RefactorPlannerPass
    ) -> None:
        """forbidden_inputs is empty for refactor pass."""
        assert len(pass_instance.forbidden_inputs) == 0


class TestRefactorPlannerPassCompilation:
    """Tests for RefactorPlannerPass compilation."""

    @pytest.fixture
    def pass_instance(self) -> RefactorPlannerPass:
        """Create a RefactorPlannerPass instance."""
        return RefactorPlannerPass()

    @pytest.fixture
    def valid_context(self) -> CompilerContext:
        """Create a valid context for refactor planning."""
        return CompilerContext(
            pass_type=CompilerPassType.REFACTOR,
            project_files={},
            artifacts={
                "architecture-plan-1": {
                    "layers": ["domain", "application", "infrastructure"],
                    "rules": [{"rule": "domain_no_imports"}],
                },
                "test-plan-1": {
                    "tests": [
                        {"id": "test_1", "target": "core", "assertions": ["Works"]}
                    ]
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
                "goal": "Extract utility functions to shared module",
                "operations": [
                    {"type": "move_file", "from": "src/utils.py", "to": "src/shared/utils.py"}
                ],
            },
        )
        return mock

    def test_compile_with_valid_context_succeeds(
        self,
        pass_instance: RefactorPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile succeeds with valid context."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.success is True

    def test_compile_passes_correct_pass_type_to_llm(
        self,
        pass_instance: RefactorPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile passes REFACTOR pass type to LLM."""
        pass_instance.compile(valid_context, mock_llm_port)
        call_args = mock_llm_port.generate.call_args
        assert call_args[0][0] == CompilerPassType.REFACTOR

    def test_compile_returns_payload_with_goal(
        self,
        pass_instance: RefactorPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns payload with goal."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.payload is not None
        assert "goal" in result.payload

    def test_compile_returns_payload_with_operations(
        self,
        pass_instance: RefactorPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns payload with operations."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.payload is not None
        assert "operations" in result.payload
