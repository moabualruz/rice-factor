"""Unit tests for CLI error types."""

import pytest

from rice_factor.domain.failures import RiceFactorError
from rice_factor.domain.failures.cli_errors import (
    CLIError,
    ConfirmationRequired,
    MissingPrerequisiteError,
    PhaseError,
)


class TestCLIError:
    """Tests for CLIError base class."""

    def test_inherits_from_rice_factor_error(self) -> None:
        """CLIError should inherit from RiceFactorError."""
        assert issubclass(CLIError, RiceFactorError)

    def test_can_be_raised(self) -> None:
        """CLIError should be raisable."""
        with pytest.raises(CLIError):
            raise CLIError("Test error")

    def test_message_is_preserved(self) -> None:
        """CLIError should preserve error message."""
        error = CLIError("Test message")
        assert str(error) == "Test message"


class TestPhaseError:
    """Tests for PhaseError class."""

    def test_inherits_from_cli_error(self) -> None:
        """PhaseError should inherit from CLIError."""
        assert issubclass(PhaseError, CLIError)

    def test_stores_command(self) -> None:
        """PhaseError should store command name."""
        error = PhaseError("scaffold", "init", "planning")
        assert error.command == "scaffold"

    def test_stores_current_phase(self) -> None:
        """PhaseError should store current phase."""
        error = PhaseError("scaffold", "init", "planning")
        assert error.current_phase == "init"

    def test_stores_required_phase(self) -> None:
        """PhaseError should store required phase."""
        error = PhaseError("scaffold", "init", "planning")
        assert error.required_phase == "planning"

    def test_generates_default_message(self) -> None:
        """PhaseError should generate meaningful default message."""
        error = PhaseError("scaffold", "init", "planning")
        message = str(error)
        assert "scaffold" in message
        assert "init" in message
        assert "planning" in message

    def test_accepts_custom_message(self) -> None:
        """PhaseError should accept custom message."""
        error = PhaseError("test", "a", "b", message="Custom message")
        assert str(error) == "Custom message"


class TestMissingPrerequisiteError:
    """Tests for MissingPrerequisiteError class."""

    def test_inherits_from_cli_error(self) -> None:
        """MissingPrerequisiteError should inherit from CLIError."""
        assert issubclass(MissingPrerequisiteError, CLIError)

    def test_stores_command(self) -> None:
        """MissingPrerequisiteError should store command name."""
        error = MissingPrerequisiteError("scaffold", "ProjectPlan not approved")
        assert error.command == "scaffold"

    def test_stores_prerequisite(self) -> None:
        """MissingPrerequisiteError should store prerequisite description."""
        error = MissingPrerequisiteError("scaffold", "ProjectPlan not approved")
        assert error.prerequisite == "ProjectPlan not approved"

    def test_generates_default_message(self) -> None:
        """MissingPrerequisiteError should generate meaningful default message."""
        error = MissingPrerequisiteError("scaffold", "ProjectPlan not approved")
        message = str(error)
        assert "scaffold" in message
        assert "ProjectPlan not approved" in message

    def test_accepts_custom_message(self) -> None:
        """MissingPrerequisiteError should accept custom message."""
        error = MissingPrerequisiteError("test", "prereq", message="Custom message")
        assert str(error) == "Custom message"


class TestConfirmationRequired:
    """Tests for ConfirmationRequired class."""

    def test_inherits_from_cli_error(self) -> None:
        """ConfirmationRequired should inherit from CLIError."""
        assert issubclass(ConfirmationRequired, CLIError)

    def test_stores_action(self) -> None:
        """ConfirmationRequired should store action description."""
        error = ConfirmationRequired("delete files")
        assert error.action == "delete files"

    def test_generates_default_message(self) -> None:
        """ConfirmationRequired should generate meaningful default message."""
        error = ConfirmationRequired("delete files")
        message = str(error)
        assert "delete files" in message
        assert "confirmation" in message.lower()

    def test_accepts_custom_message(self) -> None:
        """ConfirmationRequired should accept custom message."""
        error = ConfirmationRequired("test", message="Custom message")
        assert str(error) == "Custom message"


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_all_cli_errors_catchable_as_cli_error(self) -> None:
        """All CLI errors should be catchable as CLIError."""
        errors = [
            PhaseError("cmd", "a", "b"),
            MissingPrerequisiteError("cmd", "prereq"),
            ConfirmationRequired("action"),
        ]

        for error in errors:
            try:
                raise error
            except CLIError:
                pass  # Should be caught
            except Exception:
                pytest.fail(f"{type(error).__name__} not caught as CLIError")

    def test_all_cli_errors_catchable_as_rice_factor_error(self) -> None:
        """All CLI errors should be catchable as RiceFactorError."""
        errors = [
            PhaseError("cmd", "a", "b"),
            MissingPrerequisiteError("cmd", "prereq"),
            ConfirmationRequired("action"),
        ]

        for error in errors:
            try:
                raise error
            except RiceFactorError:
                pass  # Should be caught
            except Exception:
                pytest.fail(f"{type(error).__name__} not caught as RiceFactorError")
