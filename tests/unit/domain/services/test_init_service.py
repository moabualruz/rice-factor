"""Unit tests for InitService."""

from pathlib import Path

import pytest

from rice_factor.domain.services.init_service import InitService
from rice_factor.domain.services.questionnaire import QuestionnaireResponse


class TestInitServiceInit:
    """Tests for InitService initialization."""

    def test_init_with_project_root(self, tmp_path: Path) -> None:
        """InitService should accept project root path."""
        service = InitService(project_root=tmp_path)
        assert service.project_root == tmp_path

    def test_init_without_project_root_uses_cwd(self) -> None:
        """InitService should default to current working directory."""
        service = InitService()
        assert service.project_root == Path.cwd()

    def test_project_dir_property(self, tmp_path: Path) -> None:
        """project_dir should return .project/ under project_root."""
        service = InitService(project_root=tmp_path)
        assert service.project_dir == tmp_path / ".project"


class TestIsInitialized:
    """Tests for is_initialized() method."""

    def test_returns_false_when_no_project_dir(self, tmp_path: Path) -> None:
        """is_initialized() should return False when .project/ doesn't exist."""
        service = InitService(project_root=tmp_path)
        assert service.is_initialized() is False

    def test_returns_true_when_project_dir_exists(self, tmp_path: Path) -> None:
        """is_initialized() should return True when .project/ exists."""
        (tmp_path / ".project").mkdir()
        service = InitService(project_root=tmp_path)
        assert service.is_initialized() is True

    def test_returns_false_when_project_is_file(self, tmp_path: Path) -> None:
        """is_initialized() should return False when .project is a file."""
        (tmp_path / ".project").write_text("not a directory")
        service = InitService(project_root=tmp_path)
        assert service.is_initialized() is False


class TestInitialize:
    """Tests for initialize() method."""

    def test_creates_project_dir(self, tmp_path: Path) -> None:
        """initialize() should create .project/ directory."""
        service = InitService(project_root=tmp_path)
        service.initialize()
        assert (tmp_path / ".project").exists()
        assert (tmp_path / ".project").is_dir()

    def test_creates_all_template_files(self, tmp_path: Path) -> None:
        """initialize() should create all 5 template files."""
        service = InitService(project_root=tmp_path)
        created_files = service.initialize()

        assert len(created_files) == 5
        expected_files = [
            "requirements.md",
            "constraints.md",
            "glossary.md",
            "non_goals.md",
            "risks.md",
        ]
        for filename in expected_files:
            assert (tmp_path / ".project" / filename).exists()

    def test_returns_list_of_created_files(self, tmp_path: Path) -> None:
        """initialize() should return list of created file paths."""
        service = InitService(project_root=tmp_path)
        created_files = service.initialize()

        assert isinstance(created_files, list)
        assert all(isinstance(f, Path) for f in created_files)
        assert len(created_files) == 5

    def test_raises_error_when_already_initialized(self, tmp_path: Path) -> None:
        """initialize() should raise FileExistsError if already initialized."""
        (tmp_path / ".project").mkdir()
        service = InitService(project_root=tmp_path)

        with pytest.raises(FileExistsError) as exc_info:
            service.initialize()
        assert "already initialized" in str(exc_info.value)

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """initialize() with force=True should overwrite existing files."""
        # First initialization
        service = InitService(project_root=tmp_path)
        service.initialize()

        # Modify a file
        (tmp_path / ".project" / "requirements.md").write_text("modified")

        # Force re-initialization
        service.initialize(force=True)

        # File should be back to template
        content = (tmp_path / ".project" / "requirements.md").read_text()
        assert "modified" not in content
        assert "Project Requirements" in content

    def test_includes_questionnaire_responses_in_templates(
        self, tmp_path: Path
    ) -> None:
        """initialize() should include questionnaire responses in templates."""
        service = InitService(project_root=tmp_path)
        responses = QuestionnaireResponse()
        responses.set("problem", "Test problem statement")
        responses.set("failures", "Test failure modes")
        responses.set("architecture", "hexagonal")
        responses.set("languages", "Python")

        service.initialize(responses=responses)

        # Check requirements.md includes problem
        requirements = (tmp_path / ".project" / "requirements.md").read_text()
        assert "Test problem statement" in requirements

        # Check constraints.md includes architecture and languages
        constraints = (tmp_path / ".project" / "constraints.md").read_text()
        assert "hexagonal" in constraints
        assert "Python" in constraints

        # Check risks.md includes failures
        risks = (tmp_path / ".project" / "risks.md").read_text()
        assert "Test failure modes" in risks

    def test_empty_responses_use_defaults(self, tmp_path: Path) -> None:
        """initialize() with None responses should use default placeholders."""
        service = InitService(project_root=tmp_path)
        service.initialize(responses=None)

        requirements = (tmp_path / ".project" / "requirements.md").read_text()
        assert "[Not provided]" in requirements


class TestGetTemplateContent:
    """Tests for get_template_content() method."""

    def test_returns_requirements_template(self, tmp_path: Path) -> None:
        """get_template_content() should return requirements.md content."""
        service = InitService(project_root=tmp_path)
        content = service.get_template_content("requirements.md")
        assert "Project Requirements" in content

    def test_returns_constraints_template(self, tmp_path: Path) -> None:
        """get_template_content() should return constraints.md content."""
        service = InitService(project_root=tmp_path)
        content = service.get_template_content("constraints.md")
        assert "Technical Constraints" in content

    def test_returns_glossary_template(self, tmp_path: Path) -> None:
        """get_template_content() should return glossary.md content."""
        service = InitService(project_root=tmp_path)
        content = service.get_template_content("glossary.md")
        assert "Domain Glossary" in content

    def test_returns_non_goals_template(self, tmp_path: Path) -> None:
        """get_template_content() should return non_goals.md content."""
        service = InitService(project_root=tmp_path)
        content = service.get_template_content("non_goals.md")
        assert "Non-Goals" in content

    def test_returns_risks_template(self, tmp_path: Path) -> None:
        """get_template_content() should return risks.md content."""
        service = InitService(project_root=tmp_path)
        content = service.get_template_content("risks.md")
        assert "Risk Register" in content

    def test_includes_responses_in_content(self, tmp_path: Path) -> None:
        """get_template_content() should include responses in content."""
        service = InitService(project_root=tmp_path)
        responses = QuestionnaireResponse()
        responses.set("problem", "Custom problem")

        content = service.get_template_content("requirements.md", responses)
        assert "Custom problem" in content

    def test_raises_error_for_unknown_template(self, tmp_path: Path) -> None:
        """get_template_content() should raise ValueError for unknown file."""
        service = InitService(project_root=tmp_path)

        with pytest.raises(ValueError) as exc_info:
            service.get_template_content("unknown.md")
        assert "Unknown template file" in str(exc_info.value)


class TestTemplateFilesConstant:
    """Tests for TEMPLATE_FILES class variable."""

    def test_contains_all_expected_files(self) -> None:
        """TEMPLATE_FILES should contain all 5 template files."""
        expected = [
            "requirements.md",
            "constraints.md",
            "glossary.md",
            "non_goals.md",
            "risks.md",
        ]
        assert expected == InitService.TEMPLATE_FILES

    def test_project_dir_constant(self) -> None:
        """PROJECT_DIR should be '.project'."""
        assert InitService.PROJECT_DIR == ".project"
