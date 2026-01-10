"""Unit tests for CompilerPass base class."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.context_builder import ForbiddenInputError


class ConcreteTestPass(CompilerPass):
    """Concrete implementation for testing."""

    @property
    def pass_type(self) -> CompilerPassType:
        return CompilerPassType.PROJECT

    @property
    def output_artifact_type(self) -> ArtifactType:
        return ArtifactType.PROJECT_PLAN


class TestCompilerPassInstantiation:
    """Tests for CompilerPass instantiation."""

    def test_cannot_instantiate_abstract_base_class(self) -> None:
        """CompilerPass cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            CompilerPass()  # type: ignore[abstract]
        assert "abstract" in str(exc_info.value).lower()

    def test_can_instantiate_concrete_subclass(self) -> None:
        """Concrete subclass can be instantiated."""
        pass_instance = ConcreteTestPass()
        assert pass_instance is not None

    def test_concrete_pass_has_correct_pass_type(self) -> None:
        """Concrete pass returns correct pass type."""
        pass_instance = ConcreteTestPass()
        assert pass_instance.pass_type == CompilerPassType.PROJECT

    def test_concrete_pass_has_correct_output_type(self) -> None:
        """Concrete pass returns correct output artifact type."""
        pass_instance = ConcreteTestPass()
        assert pass_instance.output_artifact_type == ArtifactType.PROJECT_PLAN


class TestCompilerPassRequirements:
    """Tests for requirement properties."""

    def test_required_files_returns_list(self) -> None:
        """required_files returns a list from context builder."""
        pass_instance = ConcreteTestPass()
        result = pass_instance.required_files
        assert isinstance(result, list)

    def test_required_artifacts_returns_list(self) -> None:
        """required_artifacts returns a list from context builder."""
        pass_instance = ConcreteTestPass()
        result = pass_instance.required_artifacts
        assert isinstance(result, list)

    def test_forbidden_inputs_returns_list(self) -> None:
        """forbidden_inputs returns a list from context builder."""
        pass_instance = ConcreteTestPass()
        result = pass_instance.forbidden_inputs
        assert isinstance(result, list)


class TestCompilerPassCompile:
    """Tests for the compile template method."""

    @pytest.fixture
    def pass_instance(self) -> ConcreteTestPass:
        """Create a test pass instance."""
        return ConcreteTestPass()

    @pytest.fixture
    def mock_context(self) -> CompilerContext:
        """Create a mock context."""
        return CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "Test requirements",
                "constraints.md": "Test constraints",
                "glossary.md": "Test glossary",
            },
            artifacts={},
        )

    @pytest.fixture
    def mock_llm_port(self) -> MagicMock:
        """Create a mock LLM port."""
        mock = MagicMock()
        mock.generate.return_value = CompilerResult(
            success=True,
            payload={
                "domains": [{"name": "Test", "responsibility": "Testing"}],
                "modules": [{"name": "test", "domain": "Test"}],
                "constraints": {"architecture": "hexagonal", "languages": ["python"]},
            },
        )
        return mock

    def test_compile_calls_validate_context(
        self,
        pass_instance: ConcreteTestPass,
        mock_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile calls validate_context."""
        with patch.object(
            pass_instance, "validate_context"
        ) as mock_validate:
            pass_instance.compile(mock_context, mock_llm_port)
            mock_validate.assert_called_once_with(mock_context)

    def test_compile_calls_build_prompt(
        self,
        pass_instance: ConcreteTestPass,
        mock_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile calls build_prompt."""
        with patch.object(
            pass_instance, "build_prompt", return_value="test prompt"
        ) as mock_build:
            pass_instance.compile(mock_context, mock_llm_port)
            mock_build.assert_called_once_with(mock_context)

    def test_compile_calls_get_output_schema(
        self,
        pass_instance: ConcreteTestPass,
        mock_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile calls get_output_schema."""
        with patch.object(
            pass_instance, "get_output_schema", return_value={}
        ) as mock_schema:
            pass_instance.compile(mock_context, mock_llm_port)
            mock_schema.assert_called_once()

    def test_compile_calls_llm_generate(
        self,
        pass_instance: ConcreteTestPass,
        mock_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile calls llm_port.generate."""
        pass_instance.compile(mock_context, mock_llm_port)
        mock_llm_port.generate.assert_called_once()

    def test_compile_calls_validate_output_on_success(
        self,
        pass_instance: ConcreteTestPass,
        mock_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile calls validate_output when successful."""
        with patch.object(pass_instance, "validate_output") as mock_validate:
            pass_instance.compile(mock_context, mock_llm_port)
            mock_validate.assert_called_once()

    def test_compile_skips_validate_output_on_failure(
        self,
        pass_instance: ConcreteTestPass,
        mock_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile skips validate_output when failed."""
        mock_llm_port.generate.return_value = CompilerResult(
            success=False,
            error_type="test_error",
            error_details="Test error details",
        )
        with patch.object(pass_instance, "validate_output") as mock_validate:
            pass_instance.compile(mock_context, mock_llm_port)
            mock_validate.assert_not_called()

    def test_compile_returns_llm_result(
        self,
        pass_instance: ConcreteTestPass,
        mock_context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """compile returns the LLM result."""
        result = pass_instance.compile(mock_context, mock_llm_port)
        assert result.success is True
        assert result.payload is not None


class TestCompilerPassValidateContext:
    """Tests for validate_context method."""

    @pytest.fixture
    def pass_instance(self) -> ConcreteTestPass:
        """Create a test pass instance."""
        return ConcreteTestPass()

    def test_validate_context_with_valid_inputs(
        self, pass_instance: ConcreteTestPass
    ) -> None:
        """validate_context passes with valid inputs."""
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "Test",
                "constraints.md": "Test",
                "glossary.md": "Test",
            },
            artifacts={},
        )
        # Should not raise
        pass_instance.validate_context(context)

    def test_validate_context_raises_on_forbidden_input(
        self, pass_instance: ConcreteTestPass
    ) -> None:
        """validate_context raises ForbiddenInputError on forbidden input."""
        # PROJECT pass forbids source_code
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "Test",
                "constraints.md": "Test",
                "glossary.md": "Test",
                "main.py": "# Python code",  # Forbidden
            },
            artifacts={},
        )
        with pytest.raises(ForbiddenInputError):
            pass_instance.validate_context(context)


class TestCompilerPassBuildPrompt:
    """Tests for build_prompt method."""

    @pytest.fixture
    def pass_instance(self) -> ConcreteTestPass:
        """Create a test pass instance."""
        return ConcreteTestPass()

    @pytest.fixture
    def mock_context(self) -> CompilerContext:
        """Create a mock context."""
        return CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "Test requirements",
                "constraints.md": "Test constraints",
                "glossary.md": "Test glossary",
            },
            artifacts={},
        )

    def test_build_prompt_returns_string(
        self, pass_instance: ConcreteTestPass, mock_context: CompilerContext
    ) -> None:
        """build_prompt returns a string."""
        result = pass_instance.build_prompt(mock_context)
        assert isinstance(result, str)

    def test_build_prompt_not_empty(
        self, pass_instance: ConcreteTestPass, mock_context: CompilerContext
    ) -> None:
        """build_prompt returns non-empty string."""
        result = pass_instance.build_prompt(mock_context)
        assert len(result) > 0


class TestCompilerPassGetOutputSchema:
    """Tests for get_output_schema method."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def pass_instance(self, schemas_dir: Path) -> ConcreteTestPass:
        """Create a test pass instance with schemas."""
        return ConcreteTestPass(schemas_dir)

    def test_get_output_schema_returns_dict(
        self, pass_instance: ConcreteTestPass
    ) -> None:
        """get_output_schema returns a dictionary."""
        result = pass_instance.get_output_schema()
        assert isinstance(result, dict)

    def test_get_output_schema_has_type(
        self, pass_instance: ConcreteTestPass
    ) -> None:
        """get_output_schema includes type field."""
        result = pass_instance.get_output_schema()
        # Schema should have basic structure
        assert len(result) > 0


class TestCompilerPassValidateOutput:
    """Tests for validate_output method."""

    @pytest.fixture
    def schemas_dir(self) -> Path:
        """Get the actual schemas directory."""
        return Path(__file__).parent.parent.parent.parent.parent / "schemas"

    @pytest.fixture
    def pass_instance(self, schemas_dir: Path) -> ConcreteTestPass:
        """Create a test pass instance with schemas."""
        return ConcreteTestPass(schemas_dir)

    def test_validate_output_with_valid_payload(
        self, pass_instance: ConcreteTestPass
    ) -> None:
        """validate_output passes with valid payload."""
        payload: dict[str, Any] = {
            "domains": [{"name": "Test", "responsibility": "Testing"}],
            "modules": [{"name": "test", "domain": "Test"}],
            "constraints": {"architecture": "hexagonal", "languages": ["python"]},
        }
        # Should not raise
        pass_instance.validate_output(payload)
