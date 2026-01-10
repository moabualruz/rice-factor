"""Unit tests for review command."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestReviewCommandHelp:
    """Tests for review command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["review", "--help"])
        assert result.exit_code == 0
        assert "review" in result.stdout.lower()

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["review", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout


class TestReviewRequiresInit:
    """Tests for review phase requirements."""

    def test_review_requires_init(self, tmp_path: Path) -> None:
        """review should fail if project not initialized."""
        result = runner.invoke(app, ["review", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestReviewNoPendingDiffs:
    """Tests for review when no diffs are pending."""

    def test_review_shows_no_pending(self, tmp_path: Path) -> None:
        """review should show message when no pending diffs."""
        (tmp_path / ".project").mkdir()

        with patch(
            "rice_factor.entrypoints.cli.commands.review._check_phase"
        ):
            result = runner.invoke(app, ["review", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "no pending" in result.stdout.lower()


class TestReviewWithPendingDiffs:
    """Tests for review with pending diffs."""

    def test_review_shows_diff_content(self, tmp_path: Path) -> None:
        """review should show diff content."""
        (tmp_path / ".project").mkdir()

        # Create a pending diff via DiffService
        from rice_factor.domain.services.diff_service import DiffService

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)

        with patch(
            "rice_factor.entrypoints.cli.commands.review._check_phase"
        ):
            # Skip the diff (just press enter)
            result = runner.invoke(
                app, ["review", "--path", str(tmp_path)], input="s\n"
            )

        assert result.exit_code == 0
        # Should show the diff
        assert "main.py" in result.stdout

    def test_review_approve_updates_status(self, tmp_path: Path) -> None:
        """review approve should update diff status."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService, DiffStatus

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)

        with patch(
            "rice_factor.entrypoints.cli.commands.review._check_phase"
        ):
            result = runner.invoke(
                app, ["review", "--path", str(tmp_path)], input="a\n"
            )

        assert result.exit_code == 0
        # Diff should be approved
        updated_diff = diff_service.load_diff(diff.id)
        assert updated_diff is not None
        assert updated_diff.status == DiffStatus.APPROVED

    def test_review_reject_updates_status(self, tmp_path: Path) -> None:
        """review reject should update diff status."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService, DiffStatus

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)

        with patch(
            "rice_factor.entrypoints.cli.commands.review._check_phase"
        ):
            # 'r' to reject, then empty line for reason prompt
            result = runner.invoke(
                app, ["review", "--path", str(tmp_path)], input="r\n\n"
            )

        assert result.exit_code == 0
        # Diff should be rejected
        updated_diff = diff_service.load_diff(diff.id)
        assert updated_diff is not None
        assert updated_diff.status == DiffStatus.REJECTED

    def test_review_skip_leaves_pending(self, tmp_path: Path) -> None:
        """review skip should leave diff as pending."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService, DiffStatus

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)

        with patch(
            "rice_factor.entrypoints.cli.commands.review._check_phase"
        ):
            result = runner.invoke(
                app, ["review", "--path", str(tmp_path)], input="s\n"
            )

        assert result.exit_code == 0
        # Diff should still be pending
        updated_diff = diff_service.load_diff(diff.id)
        assert updated_diff is not None
        assert updated_diff.status == DiffStatus.PENDING


class TestReviewCreatesAuditEntry:
    """Tests for review audit trail."""

    def test_review_approve_creates_audit_entry(self, tmp_path: Path) -> None:
        """Approving a diff should create an audit entry."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)

        with patch(
            "rice_factor.entrypoints.cli.commands.review._check_phase"
        ):
            result = runner.invoke(
                app, ["review", "--path", str(tmp_path)], input="a\n"
            )

        assert result.exit_code == 0
        # Audit trail should exist
        trail_file = tmp_path / "audit" / "trail.json"
        assert trail_file.exists()

    def test_review_reject_creates_audit_entry(self, tmp_path: Path) -> None:
        """Rejecting a diff should create an audit entry."""
        (tmp_path / ".project").mkdir()

        from rice_factor.domain.services.diff_service import DiffService

        diff_service = DiffService(tmp_path)
        diff = diff_service.generate_diff("main.py")
        diff_service.save_diff(diff)

        with patch(
            "rice_factor.entrypoints.cli.commands.review._check_phase"
        ):
            # 'r' to reject, then empty line for reason prompt
            result = runner.invoke(
                app, ["review", "--path", str(tmp_path)], input="r\n\n"
            )

        assert result.exit_code == 0
        # Audit trail should exist
        trail_file = tmp_path / "audit" / "trail.json"
        assert trail_file.exists()
