"""Unit tests for ArchitecturePlannerPass."""

from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.passes.architecture_planner import (
    ArchitecturePlannerPass,
)


class TestArchitecturePlannerPassProperties:
    """Tests for ArchitecturePlannerPass properties."""

    @pytest.fixture
    def pass_instance(self) -> ArchitecturePlannerPass:
        """Create an ArchitecturePlannerPass instance."""
        return ArchitecturePlannerPass()

    def test_is_compiler_pass_subclass(
        self, pass_instance: ArchitecturePlannerPass
    ) -> None:
        """ArchitecturePlannerPass is a CompilerPass subclass."""
        assert isinstance(pass_instance, CompilerPass)

    def test_pass_type_is_architecture(
        self, pass_instance: ArchitecturePlannerPass
    ) -> None:
        """pass_type returns ARCHITECTURE."""
        assert pass_instance.pass_type == CompilerPassType.ARCHITECTURE

    def test_output_artifact_type_is_architecture_plan(
        self, pass_instance: ArchitecturePlannerPass
    ) -> None:
        """output_artifact_type returns ARCHITECTURE_PLAN."""
        assert pass_instance.output_artifact_type == ArtifactType.ARCHITECTURE_PLAN


class TestArchitecturePlannerPassRequirements:
    """Tests for ArchitecturePlannerPass requirements."""

    @pytest.fixture
    def pass_instance(self) -> ArchitecturePlannerPass:
        """Create an ArchitecturePlannerPass instance."""
        return ArchitecturePlannerPass()

    def test_required_files_includes_constraints(
        self, pass_instance: ArchitecturePlannerPass
    ) -> None:
        """required_files includes constraints.md."""
        assert "constraints.md" in pass_instance.required_files

    def test_required_artifacts_includes_project_plan(
        self, pass_instance: ArchitecturePlannerPass
    ) -> None:
        """required_artifacts includes PROJECT_PLAN."""
        assert ArtifactType.PROJECT_PLAN in pass_instance.required_artifacts

    def test_forbidden_inputs_is_empty(
        self, pass_instance: ArchitecturePlannerPass
    ) -> None:
        """forbidden_inputs is empty for architecture pass."""
        assert len(pass_instance.forbidden_inputs) == 0


class TestArchitecturePlannerPassCompilation:
    """Tests for ArchitecturePlannerPass compilation."""

    @pytest.fixture
    def pass_instance(self) -> ArchitecturePlannerPass:
        """Create an ArchitecturePlannerPass instance."""
        return ArchitecturePlannerPass()

    @pytest.fixture
    def valid_context(self) -> CompilerContext:
        """Create a valid context for architecture planning."""
        return CompilerContext(
            pass_type=CompilerPassType.ARCHITECTURE,
            project_files={
                "constraints.md": "# Constraints\n\nUse hexagonal architecture.",
            },
            artifacts={
                "project-plan-1": {
                    "domains": [{"name": "Core", "responsibility": "Core logic"}],
                    "modules": [{"name": "core", "domain": "Core"}],
                    "constraints": {"architecture": "hexagonal", "languages": ["python"]},
                }
            },
        )

    @pytest.fixture
    def mock_llm_port(self) -> MagicMock:
        """Create a mock LLM port with successful response."""
        mock = MagicMock()
        mock.generate.return_value = CompilerResult(
            success=True,
            payload={
                "layers": ["domain", "application", "infrastructure"],
                "rules": [{"rule": "domain_cannot_import_infrastructure"}],
            },
        )
        return mock

    def test_compile_with_valid_context_succeeds(
        self,
        pass_instance: ArchitecturePlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile succeeds with valid context."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.success is True

    def test_compile_passes_correct_pass_type_to_llm(
        self,
        pass_instance: ArchitecturePlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile passes ARCHITECTURE pass type to LLM."""
        pass_instance.compile(valid_context, mock_llm_port)
        call_args = mock_llm_port.generate.call_args
        assert call_args[0][0] == CompilerPassType.ARCHITECTURE

    def test_compile_returns_payload_with_layers(
        self,
        pass_instance: ArchitecturePlannerPass,
        valid_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns payload with layers."""
        result = pass_instance.compile(valid_context, mock_llm_port)
        assert result.payload is not None
        assert "layers" in result.payload
