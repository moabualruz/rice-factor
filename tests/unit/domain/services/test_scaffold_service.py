"""Unit tests for ScaffoldService."""

from pathlib import Path

from rice_factor.domain.artifacts.payloads.scaffold_plan import (
    FileEntry,
    FileKind,
    ScaffoldPlanPayload,
)
from rice_factor.domain.services.scaffold_service import (
    ScaffoldResult,
    ScaffoldService,
)


class TestScaffoldServiceInit:
    """Tests for ScaffoldService initialization."""

    def test_can_instantiate(self, tmp_path: Path) -> None:
        """ScaffoldService should be instantiable."""
        service = ScaffoldService(project_root=tmp_path)
        assert service is not None

    def test_project_root_property(self, tmp_path: Path) -> None:
        """ScaffoldService should expose project_root property."""
        service = ScaffoldService(project_root=tmp_path)
        assert service.project_root == tmp_path


class TestGenerateTodoComment:
    """Tests for generate_todo_comment method."""

    def test_python_source_file(self, tmp_path: Path) -> None:
        """Should generate Python docstring TODO for .py files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE)
        comment = service.generate_todo_comment(entry)
        assert '"""TODO: Implement Main module."""' in comment

    def test_javascript_source_file(self, tmp_path: Path) -> None:
        """Should generate JS comment for .js files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="main.js", description="Main module", kind=FileKind.SOURCE)
        comment = service.generate_todo_comment(entry)
        assert "// TODO: Implement Main module" in comment

    def test_typescript_source_file(self, tmp_path: Path) -> None:
        """Should generate TS comment for .ts files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="main.ts", description="Main module", kind=FileKind.SOURCE)
        comment = service.generate_todo_comment(entry)
        assert "// TODO: Implement Main module" in comment

    def test_go_source_file(self, tmp_path: Path) -> None:
        """Should generate Go comment for .go files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="main.go", description="Main package", kind=FileKind.SOURCE)
        comment = service.generate_todo_comment(entry)
        assert "// TODO: Implement Main package" in comment

    def test_rust_source_file(self, tmp_path: Path) -> None:
        """Should generate Rust comment for .rs files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="main.rs", description="Main module", kind=FileKind.SOURCE)
        comment = service.generate_todo_comment(entry)
        assert "// TODO: Implement Main module" in comment

    def test_python_test_file(self, tmp_path: Path) -> None:
        """Should generate test-specific TODO for test files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="test_main.py", description="main module", kind=FileKind.TEST)
        comment = service.generate_todo_comment(entry)
        assert '"""TODO: Implement tests for main module."""' in comment

    def test_yaml_config_file(self, tmp_path: Path) -> None:
        """Should generate YAML comment for .yaml files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="config.yaml", description="App settings", kind=FileKind.CONFIG)
        comment = service.generate_todo_comment(entry)
        assert "# TODO: Configure App settings" in comment

    def test_toml_config_file(self, tmp_path: Path) -> None:
        """Should generate TOML comment for .toml files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="pyproject.toml", description="Build config", kind=FileKind.CONFIG)
        comment = service.generate_todo_comment(entry)
        assert "# TODO: Configure Build config" in comment

    def test_json_config_file(self, tmp_path: Path) -> None:
        """Should return empty string for .json files (no comments)."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="config.json", description="Settings", kind=FileKind.CONFIG)
        comment = service.generate_todo_comment(entry)
        assert comment == ""

    def test_markdown_doc_file(self, tmp_path: Path) -> None:
        """Should generate Markdown TODO for .md files."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="README.md", description="Project docs", kind=FileKind.DOC)
        comment = service.generate_todo_comment(entry)
        assert "<!-- TODO: Document Project docs -->" in comment
        assert "# Project docs" in comment

    def test_unknown_extension_uses_default(self, tmp_path: Path) -> None:
        """Should use default template for unknown extensions."""
        service = ScaffoldService(project_root=tmp_path)
        entry = FileEntry(path="file.xyz", description="Unknown file", kind=FileKind.SOURCE)
        comment = service.generate_todo_comment(entry)
        assert "# TODO: Implement Unknown file" in comment


class TestScaffold:
    """Tests for scaffold method."""

    def test_creates_single_file(self, tmp_path: Path) -> None:
        """Should create a single file."""
        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE),
            ]
        )
        result = service.scaffold(plan)
        assert result.success
        assert len(result.created) == 1
        assert "main.py" in result.created
        assert (tmp_path / "main.py").exists()

    def test_creates_multiple_files(self, tmp_path: Path) -> None:
        """Should create multiple files."""
        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE),
                FileEntry(path="utils.py", description="Utilities", kind=FileKind.SOURCE),
            ]
        )
        result = service.scaffold(plan)
        assert result.success
        assert len(result.created) == 2
        assert (tmp_path / "main.py").exists()
        assert (tmp_path / "utils.py").exists()

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """Should create nested directories as needed."""
        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="src/core/service.py", description="Service", kind=FileKind.SOURCE),
            ]
        )
        result = service.scaffold(plan)
        assert result.success
        assert (tmp_path / "src" / "core" / "service.py").exists()

    def test_skips_existing_files(self, tmp_path: Path) -> None:
        """Should skip files that already exist."""
        existing_file = tmp_path / "main.py"
        existing_file.write_text("existing content")

        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE),
            ]
        )
        result = service.scaffold(plan)
        assert result.success
        assert len(result.skipped) == 1
        assert "main.py" in result.skipped
        assert existing_file.read_text() == "existing content"

    def test_creates_files_with_todo_content(self, tmp_path: Path) -> None:
        """Should create files with TODO comment content."""
        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE),
            ]
        )
        result = service.scaffold(plan)
        assert result.success
        content = (tmp_path / "main.py").read_text()
        assert '"""TODO: Implement Main module."""' in content

    def test_dry_run_does_not_create_files(self, tmp_path: Path) -> None:
        """Should not create files in dry run mode."""
        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE),
            ]
        )
        result = service.scaffold(plan, dry_run=True)
        assert result.success
        assert len(result.created) == 1
        assert not (tmp_path / "main.py").exists()

    def test_dry_run_reports_skipped(self, tmp_path: Path) -> None:
        """Should report skipped files in dry run mode."""
        existing_file = tmp_path / "main.py"
        existing_file.write_text("existing content")

        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE),
            ]
        )
        result = service.scaffold(plan, dry_run=True)
        assert len(result.skipped) == 1
        assert "main.py" in result.skipped


class TestScaffoldResult:
    """Tests for ScaffoldResult dataclass."""

    def test_success_when_no_errors(self) -> None:
        """Should report success when no errors."""
        result = ScaffoldResult(created=["a.py"], skipped=[], errors=[])
        assert result.success is True

    def test_not_success_when_errors(self) -> None:
        """Should not report success when there are errors."""
        result = ScaffoldResult(created=[], skipped=[], errors=[("a.py", "error")])
        assert result.success is False

    def test_success_with_skipped_files(self) -> None:
        """Should still report success with skipped files (no errors)."""
        result = ScaffoldResult(created=[], skipped=["a.py"], errors=[])
        assert result.success is True


class TestPreview:
    """Tests for preview method."""

    def test_preview_new_file(self, tmp_path: Path) -> None:
        """Should indicate file would be created."""
        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE),
            ]
        )
        preview = service.preview(plan)
        assert len(preview) == 1
        path, kind, would_create = preview[0]
        assert path == "main.py"
        assert kind == FileKind.SOURCE
        assert would_create is True

    def test_preview_existing_file(self, tmp_path: Path) -> None:
        """Should indicate file would be skipped."""
        existing_file = tmp_path / "main.py"
        existing_file.write_text("existing content")

        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="main.py", description="Main module", kind=FileKind.SOURCE),
            ]
        )
        preview = service.preview(plan)
        assert len(preview) == 1
        path, _kind, would_create = preview[0]
        assert path == "main.py"
        assert would_create is False

    def test_preview_mixed_files(self, tmp_path: Path) -> None:
        """Should correctly identify new and existing files."""
        existing_file = tmp_path / "existing.py"
        existing_file.write_text("existing content")

        service = ScaffoldService(project_root=tmp_path)
        plan = ScaffoldPlanPayload(
            files=[
                FileEntry(path="existing.py", description="Existing", kind=FileKind.SOURCE),
                FileEntry(path="new.py", description="New", kind=FileKind.SOURCE),
            ]
        )
        preview = service.preview(plan)
        assert len(preview) == 2

        existing_preview = next(p for p in preview if p[0] == "existing.py")
        assert existing_preview[2] is False

        new_preview = next(p for p in preview if p[0] == "new.py")
        assert new_preview[2] is True
