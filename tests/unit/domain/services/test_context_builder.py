"""Unit tests for context builder service."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from rice_factor.domain.artifacts.compiler_types import (
    CompilerContext,
    CompilerPassType,
)
from rice_factor.domain.artifacts.enums import ArtifactType
from rice_factor.domain.services.context_builder import (
    PASS_REQUIREMENTS,
    ContextBuilder,
    ContextBuilderError,
    ForbiddenInputError,
    MissingRequiredInputError,
)


class TestPassRequirements:
    """Tests for PASS_REQUIREMENTS configuration."""

    def test_all_pass_types_have_requirements(self) -> None:
        """All pass types should have defined requirements."""
        for pass_type in CompilerPassType:
            assert pass_type in PASS_REQUIREMENTS

    def test_project_pass_requirements(self) -> None:
        """Project pass requires 3 files and forbids source code."""
        reqs = PASS_REQUIREMENTS[CompilerPassType.PROJECT]
        assert "requirements.md" in reqs["required_files"]
        assert "constraints.md" in reqs["required_files"]
        assert "glossary.md" in reqs["required_files"]
        assert "source_code" in reqs["forbidden_inputs"]
        assert "tests" in reqs["forbidden_inputs"]

    def test_implementation_pass_requirements(self) -> None:
        """Implementation pass requires target file and has TINY context."""
        reqs = PASS_REQUIREMENTS[CompilerPassType.IMPLEMENTATION]
        assert reqs.get("requires_target_file") is True
        assert "all_other_source_files" in reqs["forbidden_inputs"]

    def test_refactor_pass_requirements(self) -> None:
        """Refactor pass requires locked test plan."""
        reqs = PASS_REQUIREMENTS[CompilerPassType.REFACTOR]
        assert reqs.get("requires_locked_test_plan") is True


class TestContextBuilder:
    """Tests for ContextBuilder class."""

    @pytest.fixture
    def builder(self) -> ContextBuilder:
        """Create a ContextBuilder instance."""
        return ContextBuilder()

    @pytest.fixture
    def project_with_files(self) -> Path:
        """Create a temporary project with required files."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            project_dir = project_root / ".project"
            project_dir.mkdir()

            # Create required files
            (project_dir / "requirements.md").write_text("# Requirements")
            (project_dir / "constraints.md").write_text("# Constraints")
            (project_dir / "glossary.md").write_text("# Glossary")

            yield project_root

    def test_build_context_for_project_pass(
        self, builder: ContextBuilder, project_with_files: Path
    ) -> None:
        """Build context for PROJECT pass with all required files."""
        context = builder.build_context(
            pass_type=CompilerPassType.PROJECT,
            project_root=project_with_files,
        )

        assert context.pass_type == CompilerPassType.PROJECT
        assert context.has_file("requirements.md")
        assert context.has_file("constraints.md")
        assert context.has_file("glossary.md")

    def test_build_context_missing_file(self, builder: ContextBuilder) -> None:
        """Build context should fail if required file is missing."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / ".project").mkdir()
            # Don't create required files

            with pytest.raises(MissingRequiredInputError) as exc_info:
                builder.build_context(
                    pass_type=CompilerPassType.PROJECT,
                    project_root=project_root,
                )

            assert exc_info.value.input_type == "file"

    def test_build_context_for_implementation_pass(
        self, builder: ContextBuilder
    ) -> None:
        """Implementation pass requires target file."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / ".project").mkdir()

            # Provide artifacts and target file
            artifacts = {
                "test-plan-id": {"test_cases": []},
                "scaffold-plan-id": {"files": []},
            }

            context = builder.build_context(
                pass_type=CompilerPassType.IMPLEMENTATION,
                project_root=project_root,
                target_file="src/main.py",
                artifacts=artifacts,
            )

            assert context.target_file == "src/main.py"

    def test_build_context_implementation_missing_target(
        self, builder: ContextBuilder
    ) -> None:
        """Implementation pass should fail without target file."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / ".project").mkdir()

            artifacts = {
                "test-plan-id": {"test_cases": []},
                "scaffold-plan-id": {"files": []},
            }

            with pytest.raises(MissingRequiredInputError) as exc_info:
                builder.build_context(
                    pass_type=CompilerPassType.IMPLEMENTATION,
                    project_root=project_root,
                    artifacts=artifacts,
                    # No target_file
                )

            assert "target_file" in exc_info.value.input_type


class TestContextValidation:
    """Tests for context validation."""

    @pytest.fixture
    def builder(self) -> ContextBuilder:
        return ContextBuilder()

    def test_validate_inputs_success(self, builder: ContextBuilder) -> None:
        """Validation passes with all required inputs."""
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "content",
                "constraints.md": "content",
                "glossary.md": "content",
            },
        )

        result = builder.validate_inputs(CompilerPassType.PROJECT, context)
        assert result is True

    def test_validate_inputs_missing_file(self, builder: ContextBuilder) -> None:
        """Validation fails with missing required file."""
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "content",
                # Missing constraints.md and glossary.md
            },
        )

        with pytest.raises(MissingRequiredInputError) as exc_info:
            builder.validate_inputs(CompilerPassType.PROJECT, context)

        assert exc_info.value.input_name in ["constraints.md", "glossary.md"]

    def test_check_forbidden_inputs_source_code(
        self, builder: ContextBuilder
    ) -> None:
        """Forbidden input check detects source code."""
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "content",
                "main.py": "print('hello')",  # Source code
            },
        )

        forbidden = builder.check_forbidden_inputs(CompilerPassType.PROJECT, context)
        assert "source_code" in forbidden

    def test_check_forbidden_inputs_tests(self, builder: ContextBuilder) -> None:
        """Forbidden input check detects test files."""
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "content",
                "test_main.py": "test content",  # Test file
            },
        )

        forbidden = builder.check_forbidden_inputs(CompilerPassType.PROJECT, context)
        assert "tests" in forbidden

    def test_check_forbidden_inputs_none(self, builder: ContextBuilder) -> None:
        """Forbidden input check returns empty for clean context."""
        context = CompilerContext(
            pass_type=CompilerPassType.PROJECT,
            project_files={
                "requirements.md": "content",
                "constraints.md": "content",
                "glossary.md": "content",
            },
        )

        forbidden = builder.check_forbidden_inputs(CompilerPassType.PROJECT, context)
        assert forbidden == []


class TestContextBuilderHelpers:
    """Tests for helper methods."""

    @pytest.fixture
    def builder(self) -> ContextBuilder:
        return ContextBuilder()

    def test_get_required_files(self, builder: ContextBuilder) -> None:
        """Get required files for a pass type."""
        files = builder.get_required_files(CompilerPassType.PROJECT)
        assert "requirements.md" in files
        assert "constraints.md" in files
        assert "glossary.md" in files

    def test_get_required_artifacts(self, builder: ContextBuilder) -> None:
        """Get required artifacts for a pass type."""
        artifacts = builder.get_required_artifacts(CompilerPassType.ARCHITECTURE)
        assert ArtifactType.PROJECT_PLAN in artifacts

    def test_get_forbidden_inputs(self, builder: ContextBuilder) -> None:
        """Get forbidden inputs for a pass type."""
        forbidden = builder.get_forbidden_inputs(CompilerPassType.PROJECT)
        assert "source_code" in forbidden
        assert "tests" in forbidden


class TestContextBuilderErrors:
    """Tests for error classes."""

    def test_missing_required_input_error(self) -> None:
        """MissingRequiredInputError has correct attributes."""
        error = MissingRequiredInputError("file", "requirements.md")
        assert error.input_type == "file"
        assert error.input_name == "requirements.md"
        assert "file" in str(error)
        assert "requirements.md" in str(error)

    def test_forbidden_input_error(self) -> None:
        """ForbiddenInputError has correct attributes."""
        error = ForbiddenInputError("source_code", "Found main.py")
        assert error.input_type == "source_code"
        assert error.details == "Found main.py"
        assert "source_code" in str(error)

    def test_context_builder_error_hierarchy(self) -> None:
        """Error classes inherit from ContextBuilderError."""
        assert issubclass(MissingRequiredInputError, ContextBuilderError)
        assert issubclass(ForbiddenInputError, ContextBuilderError)
