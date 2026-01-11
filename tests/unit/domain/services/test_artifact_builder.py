"""Unit tests for ArtifactBuilder."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
    CompilerResult,
)
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.services.artifact_builder import (
    ArtifactBuilder,
    ArtifactBuilderError,
)
from rice_factor.domain.services.passes import PassRegistry


class TestArtifactBuilderInstantiation:
    """Tests for ArtifactBuilder instantiation."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset pass registry before each test."""
        PassRegistry.reset_instance()

    def test_instantiation_with_required_args(self) -> None:
        """ArtifactBuilder can be instantiated with required args."""
        mock_llm = MagicMock()
        mock_storage = MagicMock()
        builder = ArtifactBuilder(mock_llm, mock_storage)
        assert builder is not None

    def test_instantiation_with_all_args(self) -> None:
        """ArtifactBuilder can be instantiated with all args."""
        mock_llm = MagicMock()
        mock_storage = MagicMock()
        mock_context_builder = MagicMock()
        mock_failure_service = MagicMock()
        builder = ArtifactBuilder(
            mock_llm, mock_storage, mock_context_builder, mock_failure_service
        )
        assert builder is not None


class TestArtifactBuilderBuild:
    """Tests for ArtifactBuilder.build method."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset pass registry before each test."""
        PassRegistry.reset_instance()

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

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create a mock storage port."""
        mock = MagicMock()
        mock.get_path_for_artifact.return_value = Path("/artifacts/test.json")
        return mock

    @pytest.fixture
    def mock_context_builder(self) -> MagicMock:
        """Create a mock context builder."""
        mock = MagicMock()
        mock.build_context.return_value = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "Test",
                "constraints.md": "Test",
                "glossary.md": "Test",
            },
            artifacts={},
        )
        return mock

    @pytest.fixture
    def builder(
        self,
        mock_llm_port: MagicMock,
        mock_storage: MagicMock,
        mock_context_builder: MagicMock,
    ) -> ArtifactBuilder:
        """Create an ArtifactBuilder with mocks."""
        return ArtifactBuilder(mock_llm_port, mock_storage, mock_context_builder)

    def test_build_calls_context_builder(
        self,
        builder: ArtifactBuilder,
        mock_context_builder: MagicMock,
    ) -> None:
        """build calls context_builder.build_context."""
        builder.build(CompilerPassType.PROJECT, Path("/project"))
        mock_context_builder.build_context.assert_called_once()

    def test_build_calls_llm_port_generate(
        self,
        builder: ArtifactBuilder,
        mock_llm_port: MagicMock,
    ) -> None:
        """build calls llm_port.generate (via pass.compile)."""
        builder.build(CompilerPassType.PROJECT, Path("/project"))
        mock_llm_port.generate.assert_called_once()

    def test_build_saves_artifact_on_success(
        self,
        builder: ArtifactBuilder,
        mock_storage: MagicMock,
    ) -> None:
        """build saves artifact to storage on success."""
        builder.build(CompilerPassType.PROJECT, Path("/project"))
        mock_storage.save.assert_called_once()

    def test_build_returns_envelope_with_draft_status(
        self,
        builder: ArtifactBuilder,
    ) -> None:
        """build returns envelope with DRAFT status."""
        result = builder.build(CompilerPassType.PROJECT, Path("/project"))
        assert result.status == ArtifactStatus.DRAFT

    def test_build_returns_envelope_with_correct_type(
        self,
        builder: ArtifactBuilder,
    ) -> None:
        """build returns envelope with correct artifact type."""
        result = builder.build(CompilerPassType.PROJECT, Path("/project"))
        assert result.artifact_type == ArtifactType.PROJECT_PLAN


class TestArtifactBuilderBuildFailure:
    """Tests for ArtifactBuilder failure handling."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset pass registry before each test."""
        PassRegistry.reset_instance()

    @pytest.fixture
    def mock_llm_port_failure(self) -> MagicMock:
        """Create a mock LLM port that returns failure."""
        mock = MagicMock()
        mock.generate.return_value = CompilerResult(
            success=False,
            error_type="missing_information",
            error_details="Could not determine domain boundaries",
        )
        return mock

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create a mock storage port."""
        mock = MagicMock()
        mock.get_path_for_artifact.return_value = Path("/artifacts/test.json")
        return mock

    @pytest.fixture
    def mock_context_builder(self) -> MagicMock:
        """Create a mock context builder."""
        mock = MagicMock()
        mock.build_context.return_value = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "Test",
                "constraints.md": "Test",
                "glossary.md": "Test",
            },
            artifacts={},
        )
        return mock

    @pytest.fixture
    def builder(
        self,
        mock_llm_port_failure: MagicMock,
        mock_storage: MagicMock,
        mock_context_builder: MagicMock,
    ) -> ArtifactBuilder:
        """Create an ArtifactBuilder with failure mock."""
        return ArtifactBuilder(
            mock_llm_port_failure, mock_storage, mock_context_builder
        )

    def test_build_returns_failure_report_on_failure(
        self,
        builder: ArtifactBuilder,
    ) -> None:
        """build returns FailureReport envelope on failure."""
        result = builder.build(CompilerPassType.PROJECT, Path("/project"))
        assert result.artifact_type == ArtifactType.FAILURE_REPORT

    def test_build_saves_failure_report_on_failure(
        self,
        builder: ArtifactBuilder,
        mock_storage: MagicMock,
    ) -> None:
        """build saves FailureReport to storage on failure."""
        builder.build(CompilerPassType.PROJECT, Path("/project"))
        mock_storage.save.assert_called_once()

    def test_failure_report_is_blocking(
        self,
        builder: ArtifactBuilder,
    ) -> None:
        """FailureReport has blocking=True for compilation failures."""
        result = builder.build(CompilerPassType.PROJECT, Path("/project"))
        assert result.payload.blocking is True  # type: ignore[union-attr]


class TestArtifactBuilderBuildWithContext:
    """Tests for ArtifactBuilder.build_with_context method."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset pass registry before each test."""
        PassRegistry.reset_instance()

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

    @pytest.fixture
    def mock_storage(self) -> MagicMock:
        """Create a mock storage port."""
        mock = MagicMock()
        mock.get_path_for_artifact.return_value = Path("/artifacts/test.json")
        return mock

    @pytest.fixture
    def builder(
        self,
        mock_llm_port: MagicMock,
        mock_storage: MagicMock,
    ) -> ArtifactBuilder:
        """Create an ArtifactBuilder with mocks."""
        return ArtifactBuilder(mock_llm_port, mock_storage)

    @pytest.fixture
    def context(self) -> CompilerContext:
        """Create a test context."""
        return CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "Test",
                "constraints.md": "Test",
                "glossary.md": "Test",
            },
            artifacts={},
        )

    def test_build_with_context_uses_provided_context(
        self,
        builder: ArtifactBuilder,
        context: CompilerContext,
        mock_llm_port: MagicMock,
    ) -> None:
        """build_with_context uses the provided context."""
        builder.build_with_context(CompilerPassType.PROJECT, context)
        # LLM should be called with the provided context
        call_args = mock_llm_port.generate.call_args
        assert call_args[0][1] == context

    def test_build_with_context_returns_envelope(
        self,
        builder: ArtifactBuilder,
        context: CompilerContext,
    ) -> None:
        """build_with_context returns an envelope."""
        result = builder.build_with_context(CompilerPassType.PROJECT, context)
        assert result.artifact_type == ArtifactType.PROJECT_PLAN


class TestArtifactBuilderError:
    """Tests for ArtifactBuilderError."""

    def test_error_stores_message(self) -> None:
        """ArtifactBuilderError stores message."""
        error = ArtifactBuilderError("Test error")
        assert str(error) == "Test error"

    def test_error_stores_pass_type(self) -> None:
        """ArtifactBuilderError stores pass_type."""
        error = ArtifactBuilderError("Test error", CompilerPassType.PROJECT)
        assert error.pass_type == CompilerPassType.PROJECT

    def test_error_pass_type_is_optional(self) -> None:
        """ArtifactBuilderError pass_type is optional."""
        error = ArtifactBuilderError("Test error")
        assert error.pass_type is None
