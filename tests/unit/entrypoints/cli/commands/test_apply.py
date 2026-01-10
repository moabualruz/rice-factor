"""Unit tests for apply command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestApplyCommandHelp:
    """Tests for apply command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["apply", "--help"])
        assert result.exit_code == 0
        assert "apply" in result.stdout.lower()

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["apply", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout

    def test_help_shows_dry_run_option(self) -> None:
        """--help should show --dry-run option."""
        result = runner.invoke(app, ["apply", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout

    def test_help_shows_yes_option(self) -> None:
        """--help should show --yes option."""
        result = runner.invoke(app, ["apply", "--help"])
        assert result.exit_code == 0
        assert "--yes" in result.stdout


class TestApplyRequiresInit:
    """Tests for apply phase requirements."""

    def test_apply_requires_init(self, tmp_path: Path) -> None:
        """apply should fail if project not initialized."""
        result = runner.invoke(app, ["apply", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestApplyNoApprovedDiffs:
    """Tests for apply when no diffs are approved."""

    def test_apply_shows_no_approved(self, tmp_path: Path) -> None:
        """apply should show message when no approved diffs."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.apply._check_phase"
        ):
            result = runner.invoke(app, ["apply", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "no approved" in result.stdout.lower()


class TestApplyWithApprovedDiff:
    """Tests for apply with approved diffs."""

    def test_apply_requires_confirmation(self, tmp_path: Path) -> None:
        """apply should require confirmation before applying."""
        (tmp_path / ".project").mkdir()

        # Create and approve a diff
        from rice_factor.domain.services.diff_service import DiffService

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)
        diff_service.approve_diff(diff.id)

        with patch(
            "rice_factor.entrypoints.cli.commands.apply._check_phase"
        ):
            # Decline confirmation
            result = runner.invoke(
                app, ["apply", "--path", str(tmp_path)], input="n\n"
            )

        assert result.exit_code == 0
        # Should not apply
        assert "abort" in result.stdout.lower() or "cancelled" in result.stdout.lower()

    def test_apply_yes_skips_confirmation(self, tmp_path: Path) -> None:
        """--yes should skip confirmation prompt."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)
        diff_service.approve_diff(diff.id)

        with patch(
            "rice_factor.entrypoints.cli.commands.apply._check_phase"
        ):
            result = runner.invoke(
                app, ["apply", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        # Should apply without asking
        assert "applied" in result.stdout.lower()

    def test_apply_marks_diff_as_applied(self, tmp_path: Path) -> None:
        """apply should mark diff as applied."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService, DiffStatus

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)
        diff_service.approve_diff(diff.id)

        with patch(
            "rice_factor.entrypoints.cli.commands.apply._check_phase"
        ):
            result = runner.invoke(
                app, ["apply", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        # Diff should be marked as applied
        updated_diff = diff_service.load_diff(diff.id)
        assert updated_diff is not None
        assert updated_diff.status == DiffStatus.APPLIED


class TestApplyDryRun:
    """Tests for apply --dry-run mode."""

    def test_dry_run_does_not_apply(self, tmp_path: Path) -> None:
        """--dry-run should not apply diff."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService, DiffStatus

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)
        diff_service.approve_diff(diff.id)

        with patch(
            "rice_factor.entrypoints.cli.commands.apply._check_phase"
        ):
            result = runner.invoke(
                app, ["apply", "--path", str(tmp_path), "--dry-run"]
            )

        assert result.exit_code == 0
        # Diff should still be approved, not applied
        updated_diff = diff_service.load_diff(diff.id)
        assert updated_diff is not None
        assert updated_diff.status == DiffStatus.APPROVED

    def test_dry_run_shows_preview(self, tmp_path: Path) -> None:
        """--dry-run should show what would happen."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)
        diff_service.approve_diff(diff.id)

        with patch(
            "rice_factor.entrypoints.cli.commands.apply._check_phase"
        ):
            result = runner.invoke(
                app, ["apply", "--path", str(tmp_path), "--dry-run"]
            )

        assert result.exit_code == 0
        assert "dry run" in result.stdout.lower()


class TestApplyCreatesAuditEntry:
    """Tests for apply audit trail."""

    def test_apply_creates_audit_entry(self, tmp_path: Path) -> None:
        """Applying a diff should create an audit entry."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)
        diff_service.approve_diff(diff.id)

        with patch(
            "rice_factor.entrypoints.cli.commands.apply._check_phase"
        ):
            result = runner.invoke(
                app, ["apply", "--path", str(tmp_path), "--yes"]
            )

        assert result.exit_code == 0
        # Audit trail should exist
        trail_file = tmp_path / "audit" / "trail.json"
        assert trail_file.exists()
