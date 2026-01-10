"""Unit tests for ImplementationPlannerPass."""

from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.passes.implementation_planner import (
    ImplementationPlannerPass,
)


class TestImplementationPlannerPassProperties:
    """Tests for ImplementationPlannerPass properties."""

    @pytest.fixture
    def pass_instance(self) -> ImplementationPlannerPass:
        """Create an ImplementationPlannerPass instance."""
        return ImplementationPlannerPass()

    def test_is_compiler_pass_subclass(
        self, pass_instance: ImplementationPlannerPass
    ) -> None:
        """ImplementationPlannerPass is a CompilerPass subclass."""
        assert isinstance(pass_instance, CompilerPass)

    def test_pass_type_is_implementation(
        self, pass_instance: ImplementationPlannerPass
    ) -> None:
        """pass_type returns IMPLEMENTATION."""
        assert pass_instance.pass_type == CompilerPassType.IMPLEMENTATION

    def test_output_artifact_type_is_implementation_plan(
        self, pass_instance: ImplementationPlannerPass
    ) -> None:
        """output_artifact_type returns IMPLEMENTATION_PLAN."""
        assert pass_instance.output_artifact_type == ArtifactType.IMPLEMENTATION_PLAN


class TestImplementationPlannerPassRequirements:
    """Tests for ImplementationPlannerPass requirements."""

    @pytest.fixture
    def pass_instance(self) -> ImplementationPlannerPass:
        """Create an ImplementationPlannerPass instance."""
        return ImplementationPlannerPass()

    def test_required_artifacts_includes_test_plan(
        self, pass_instance: ImplementationPlannerPass
    ) -> None:
        """required_artifacts includes TEST_PLAN."""
        assert ArtifactType.TEST_PLAN in pass_instance.required_artifacts

    def test_required_artifacts_includes_scaffold_plan(
        self, pass_instance: ImplementationPlannerPass
    ) -> None:
        """required_artifacts includes SCAFFOLD_PLAN."""
        assert ArtifactType.SCAFFOLD_PLAN in pass_instance.required_artifacts

    def test_forbidden_inputs_includes_all_other_source_files(
        self, pass_instance: ImplementationPlannerPass
    ) -> None:
        """forbidden_inputs includes all_other_source_files (TINY context)."""
        assert "all_other_source_files" in pass_instance.forbidden_inputs


class TestImplementationPlannerPassCompilation:
    """Tests for ImplementationPlannerPass compilation."""

    @pytest.fixture
    def pass_instance(self) -> ImplementationPlannerPass:
        """Create an ImplementationPlannerPass instance."""
        return ImplementationPlannerPass()

    @pytest.fixture
    def valid_context(self) -> CompilerContext:
        """Create a valid context for implementation planning."""
        return CompilerContext(
            pass_type=CompilerPassType.IMPLEMENTATION,
            project_files={},
            artifacts={
                "test-plan-1": {
                    "tests": [
                        {"id": "test_1", "target": "core", "assertions": ["Works"]}
                    ]
                },
                "scaffold-plan-1": {"files": [{"path": "src/core.py", "description": "Core", "kind": "source"}]},
            },
            target_file="src/core.py",
        )

    @pytest.fixture
    def mock_llm_port(self) -> MagicMock:
        """Create a mock LLM port with successful response."""
        mock = MagicMock()
        mock.generate.return_value = CompilerResult(
            success=True,
            payload={
                "target": "src/core.py",
                "steps": ["Create class Core", "Add method process"],
                "related_tests": ["test_1"],
            },
        )
        return mock

    def test_compile_with_valid_context_succeeds(
        self,
        pass_instance: ImplementationPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile succeeds with valid context."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.success is True

    def test_compile_passes_correct_pass_type_to_llm(
        self,
        pass_instance: ImplementationPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile passes IMPLEMENTATION pass type to LLM."""
        pass_instance.compile(valid_context, mock_llm_port)
        call_args = mock_llm_port.generate.call_args
        assert call_args[0][0] == CompilerPassType.IMPLEMENTATION

    def test_compile_returns_payload_with_target(
        self,
        pass_instance: ImplementationPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns payload with target."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.payload is not None
        assert "target" in result.payload

    def test_compile_returns_payload_with_steps(
        self,
        pass_instance: ImplementationPlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns payload with steps."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.payload is not None
        assert "steps" in result.payload
