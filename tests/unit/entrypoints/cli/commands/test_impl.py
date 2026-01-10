"""Unit tests for impl command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestImplCommandHelp:
    """Tests for impl command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["impl", "--help"])
        assert result.exit_code == 0
        assert "implementation" in result.stdout.lower()

    def test_help_shows_file_argument(self) -> None:
        """--help should show file argument."""
        result = runner.invoke(app, ["impl", "--help"])
        assert result.exit_code == 0
        assert "FILE_PATH" in result.stdout or "file" in result.stdout.lower()

    def test_help_shows_dry_run_option(self) -> None:
        """--help should show --dry-run option."""
        result = runner.invoke(app, ["impl", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout


class TestImplRequiresInit:
    """Tests for impl phase requirements."""

    def test_impl_requires_init(self, tmp_path: Path) -> None:
        """impl should fail if project not initialized."""
        result = runner.invoke(
            app, ["impl", "main.py", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    def test_impl_requires_test_locked_phase(self, tmp_path: Path) -> None:
        """impl should require TEST_LOCKED phase."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["impl", "main.py", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        # Should fail because we need TEST_LOCKED phase
        assert "phase" in result.stdout.lower() or "cannot" in result.stdout.lower()


class TestImplExecution:
    """Tests for impl execution."""

    def test_impl_generates_diff(self, tmp_path: Path) -> None:
        """impl should generate a diff."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.impl._check_phase"
        ):
            result = runner.invoke(
                app, ["impl", "main.py", "--path", str(tmp_path)]
            )

        assert result.exit_code == 0
        assert "diff" in result.stdout.lower()

    def test_impl_saves_diff(self, tmp_path: Path) -> None:
        """impl should save diff to audit/diffs."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.impl._check_phase"
        ):
            result = runner.invoke(
                app, ["impl", "main.py", "--path", str(tmp_path)]
            )

        assert result.exit_code == 0
        diffs_dir = tmp_path / "audit" / "diffs"
        assert diffs_dir.exists()
        diff_files = list(diffs_dir.glob("*.diff"))
        assert len(diff_files) >= 1

    def test_impl_creates_audit_entry(self, tmp_path: Path) -> None:
        """impl should create an audit trail entry."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.impl._check_phase"
        ):
            result = runner.invoke(
                app, ["impl", "main.py", "--path", str(tmp_path)]
            )

        assert result.exit_code == 0
        trail_file = tmp_path / "audit" / "trail.json"
        assert trail_file.exists()


class TestImplDryRun:
    """Tests for impl --dry-run mode."""

    def test_dry_run_does_not_save_diff(self, tmp_path: Path) -> None:
        """--dry-run should not save diff."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.impl._check_phase"
        ):
            result = runner.invoke(
                app, ["impl", "main.py", "--path", str(tmp_path), "--dry-run"]
            )

        assert result.exit_code == 0
        diffs_dir = tmp_path / "audit" / "diffs"
        # Directory might exist but should have no diff files
        if diffs_dir.exists():
            diff_files = list(diffs_dir.glob("*.diff"))
            assert len(diff_files) == 0

    def test_dry_run_shows_preview(self, tmp_path: Path) -> None:
        """--dry-run should show what would happen."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.impl._check_phase"
        ):
            result = runner.invoke(
                app, ["impl", "main.py", "--path", str(tmp_path), "--dry-run"]
            )

        assert result.exit_code == 0
        assert "dry run" in result.stdout.lower()
