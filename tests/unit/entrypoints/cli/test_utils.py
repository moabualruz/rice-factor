"""Unit tests for CLI utilities."""

from unittest.mock import MagicMock, patch

import pytest
import typer

from rice_factor.domain.failures import (
    ArtifactNotFoundError,
    ArtifactStatusError,
    ArtifactValidationError,
    ConfirmationRequired,
    MissingPrerequisiteError,
    PhaseError,
)
from rice_factor.entrypoints.cli.utils import (
    confirm,
    confirm_destructive,
    console,
    display_error,
    display_panel,
    display_table,
    error,
    handle_errors,
    info,
    success,
    supports_dry_run,
    warning,
)


class TestConsole:
    """Tests for console singleton."""

    def test_console_is_available(self) -> None:
        """Console singleton should be available."""
        assert console is not None

    def test_console_is_rich_console(self) -> None:
        """Console should be a Rich Console instance."""
        from rich.console import Console

        assert isinstance(console, Console)


class TestSuccessMessage:
    """Tests for success() function."""

    def test_success_prints_green_checkmark(self) -> None:
        """success() should print message with green checkmark."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            mock_console.print = MagicMock()
            success("Test message")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Test message" in call_args
            assert "green" in call_args


class TestWarningMessage:
    """Tests for warning() function."""

    def test_warning_prints_yellow_icon(self) -> None:
        """warning() should print message with yellow warning icon."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            mock_console.print = MagicMock()
            warning("Test warning")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Test warning" in call_args
            assert "yellow" in call_args


class TestErrorMessage:
    """Tests for error() function."""

    def test_error_prints_red_x(self) -> None:
        """error() should print message with red X."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            mock_console.print = MagicMock()
            error("Test error")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Test error" in call_args
            assert "red" in call_args


class TestInfoMessage:
    """Tests for info() function."""

    def test_info_prints_blue_icon(self) -> None:
        """info() should print message with blue info icon."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            mock_console.print = MagicMock()
            info("Test info")
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "Test info" in call_args
            assert "blue" in call_args


class TestConfirm:
    """Tests for confirm() function."""

    def test_confirm_calls_typer_confirm(self) -> None:
        """confirm() should delegate to typer.confirm."""
        with patch("rice_factor.entrypoints.cli.utils.typer.confirm") as mock_confirm:
            mock_confirm.return_value = True
            result = confirm("Are you sure?")
            assert result is True
            mock_confirm.assert_called_once_with("Are you sure?", default=False)

    def test_confirm_with_default_true(self) -> None:
        """confirm() should pass default parameter."""
        with patch("rice_factor.entrypoints.cli.utils.typer.confirm") as mock_confirm:
            mock_confirm.return_value = True
            confirm("Continue?", default=True)
            mock_confirm.assert_called_once_with("Continue?", default=True)


class TestConfirmDestructive:
    """Tests for confirm_destructive() function."""

    def test_confirm_destructive_shows_warning(self) -> None:
        """confirm_destructive() should show warning before confirmation."""
        with (
            patch("rice_factor.entrypoints.cli.utils.console") as mock_console,
            patch("rice_factor.entrypoints.cli.utils.typer.confirm") as mock_confirm,
        ):
            mock_confirm.return_value = True
            result = confirm_destructive("delete", "test.txt")
            assert result is True
            # Should print warning
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert "delete" in call_args
            assert "test.txt" in call_args

    def test_confirm_destructive_defaults_to_false(self) -> None:
        """confirm_destructive() should default to False."""
        with (
            patch("rice_factor.entrypoints.cli.utils.console"),
            patch("rice_factor.entrypoints.cli.utils.typer.confirm") as mock_confirm,
        ):
            mock_confirm.return_value = False
            confirm_destructive("overwrite", "config.yaml")
            mock_confirm.assert_called_once_with("Are you sure?", default=False)


class TestDisplayError:
    """Tests for display_error() function."""

    def test_display_error_shows_panel(self) -> None:
        """display_error() should show error in a panel."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            display_error("Error Title", "Error message")
            mock_console.print.assert_called_once()

    def test_display_error_with_hint(self) -> None:
        """display_error() should include hint if provided."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            display_error("Error", "Message", hint="Try this instead")
            mock_console.print.assert_called_once()
            # The Panel object should contain the hint
            panel = mock_console.print.call_args[0][0]
            assert "Try this instead" in str(panel.renderable)


class TestDisplayPanel:
    """Tests for display_panel() function."""

    def test_display_panel_shows_content(self) -> None:
        """display_panel() should show content in a styled panel."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            display_panel("Title", "Content")
            mock_console.print.assert_called_once()

    def test_display_panel_with_custom_style(self) -> None:
        """display_panel() should use custom style."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            display_panel("Title", "Content", style="green")
            mock_console.print.assert_called_once()
            panel = mock_console.print.call_args[0][0]
            assert panel.border_style == "green"


class TestDisplayTable:
    """Tests for display_table() function."""

    def test_display_table_shows_data(self) -> None:
        """display_table() should display data in a table."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            display_table(
                "Test Table",
                ["Col1", "Col2"],
                [["A", "B"], ["C", "D"]],
            )
            mock_console.print.assert_called_once()

    def test_display_table_without_header(self) -> None:
        """display_table() should support hiding header."""
        with patch("rice_factor.entrypoints.cli.utils.console") as mock_console:
            display_table(
                "Test Table",
                ["Col1", "Col2"],
                [["A", "B"]],
                show_header=False,
            )
            mock_console.print.assert_called_once()
            table = mock_console.print.call_args[0][0]
            assert table.show_header is False


class TestHandleErrors:
    """Tests for @handle_errors decorator."""

    def test_handle_errors_passes_through_normal_execution(self) -> None:
        """@handle_errors should pass through when no exception."""

        @handle_errors
        def good_function() -> str:
            return "success"

        result = good_function()
        assert result == "success"

    def test_handle_errors_catches_phase_error(self) -> None:
        """@handle_errors should catch PhaseError and exit."""

        @handle_errors
        def phase_error_function() -> None:
            raise PhaseError("test", "init", "planning")

        with patch("rice_factor.entrypoints.cli.utils.display_error"):
            with pytest.raises(typer.Exit) as exc_info:
                phase_error_function()
            assert exc_info.value.exit_code == 1

    def test_handle_errors_catches_missing_prerequisite_error(self) -> None:
        """@handle_errors should catch MissingPrerequisiteError and exit."""

        @handle_errors
        def missing_prereq_function() -> None:
            raise MissingPrerequisiteError("scaffold", "ProjectPlan not approved")

        with patch("rice_factor.entrypoints.cli.utils.display_error"):
            with pytest.raises(typer.Exit) as exc_info:
                missing_prereq_function()
            assert exc_info.value.exit_code == 1

    def test_handle_errors_catches_confirmation_required(self) -> None:
        """@handle_errors should catch ConfirmationRequired and exit."""

        @handle_errors
        def confirmation_function() -> None:
            raise ConfirmationRequired("delete files")

        with patch("rice_factor.entrypoints.cli.utils.display_error"):
            with pytest.raises(typer.Exit) as exc_info:
                confirmation_function()
            assert exc_info.value.exit_code == 1

    def test_handle_errors_catches_artifact_not_found(self) -> None:
        """@handle_errors should catch ArtifactNotFoundError and exit."""

        @handle_errors
        def not_found_function() -> None:
            raise ArtifactNotFoundError("Artifact not found")

        with patch("rice_factor.entrypoints.cli.utils.display_error"):
            with pytest.raises(typer.Exit) as exc_info:
                not_found_function()
            assert exc_info.value.exit_code == 1

    def test_handle_errors_catches_artifact_validation_error(self) -> None:
        """@handle_errors should catch ArtifactValidationError and exit."""

        @handle_errors
        def validation_function() -> None:
            raise ArtifactValidationError("Invalid schema")

        with patch("rice_factor.entrypoints.cli.utils.display_error"):
            with pytest.raises(typer.Exit) as exc_info:
                validation_function()
            assert exc_info.value.exit_code == 1

    def test_handle_errors_catches_artifact_status_error(self) -> None:
        """@handle_errors should catch ArtifactStatusError and exit."""

        @handle_errors
        def status_function() -> None:
            raise ArtifactStatusError("Cannot modify approved artifact")

        with patch("rice_factor.entrypoints.cli.utils.display_error"):
            with pytest.raises(typer.Exit) as exc_info:
                status_function()
            assert exc_info.value.exit_code == 1

    def test_handle_errors_catches_keyboard_interrupt(self) -> None:
        """@handle_errors should catch KeyboardInterrupt and exit with 130."""

        @handle_errors
        def interrupted_function() -> None:
            raise KeyboardInterrupt()

        with patch("rice_factor.entrypoints.cli.utils.console"):
            with pytest.raises(typer.Exit) as exc_info:
                interrupted_function()
            assert exc_info.value.exit_code == 130


class TestSupportsDryRun:
    """Tests for @supports_dry_run decorator."""

    def test_supports_dry_run_normal_execution(self) -> None:
        """@supports_dry_run should execute normally when dry_run=False."""

        @supports_dry_run
        def normal_function(dry_run: bool = False) -> str:  # noqa: ARG001
            return "executed"

        result = normal_function(dry_run=False)
        assert result == "executed"

    def test_supports_dry_run_shows_info_when_dry_run(self) -> None:
        """@supports_dry_run should show info message when dry_run=True."""

        @supports_dry_run
        def dry_run_function(dry_run: bool = False) -> str:  # noqa: ARG001
            return "executed"

        with patch("rice_factor.entrypoints.cli.utils.info") as mock_info:
            result = dry_run_function(dry_run=True)
            assert result == "executed"
            mock_info.assert_called_once()
            assert "Dry-run" in mock_info.call_args[0][0]
