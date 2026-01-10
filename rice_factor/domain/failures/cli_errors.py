"""CLI-specific error types.

This module defines exceptions for CLI operations including:
- PhaseError: When a command is executed in the wrong phase
- MissingPrerequisiteError: When required artifacts/state is missing
- ConfirmationRequired: When user didn't confirm a destructive action
"""

from rice_factor.domain.failures.errors import RiceFactorError


class CLIError(RiceFactorError):
    """Base class for CLI-related errors.

    All CLI-specific exceptions should inherit from this class.
    """


class PhaseError(CLIError):
    """Raised when a command is executed in an invalid phase.

    Examples:
        - Running 'scaffold' before ProjectPlan is approved
        - Running 'impl' before TestPlan is locked
        - Running any command before 'init'
    """

    def __init__(
        self,
        command: str,
        current_phase: str,
        required_phase: str,
        message: str | None = None,
    ) -> None:
        """Initialize phase error.

        Args:
            command: The command that was attempted
            current_phase: The current project phase
            required_phase: The required phase for this command
            message: Optional custom message
        """
        self.command = command
        self.current_phase = current_phase
        self.required_phase = required_phase

        if message is None:
            message = (
                f"Cannot run '{command}' in phase '{current_phase}'. "
                f"Required phase: '{required_phase}' or later."
            )
        super().__init__(message)


class MissingPrerequisiteError(CLIError):
    """Raised when required prerequisites are not met.

    Examples:
        - Missing .project/ directory
        - Required artifact doesn't exist
        - Required artifact is not approved
    """

    def __init__(
        self,
        command: str,
        prerequisite: str,
        message: str | None = None,
    ) -> None:
        """Initialize missing prerequisite error.

        Args:
            command: The command that was attempted
            prerequisite: Description of the missing prerequisite
            message: Optional custom message
        """
        self.command = command
        self.prerequisite = prerequisite

        if message is None:
            message = f"Cannot run '{command}': {prerequisite}"
        super().__init__(message)


class ConfirmationRequired(CLIError):
    """Raised when a destructive action was not confirmed.

    Used when a command requires user confirmation but the user
    declined or didn't provide confirmation.
    """

    def __init__(
        self,
        action: str,
        message: str | None = None,
    ) -> None:
        """Initialize confirmation required error.

        Args:
            action: The action that required confirmation
            message: Optional custom message
        """
        self.action = action

        if message is None:
            message = f"Action '{action}' requires confirmation."
        super().__init__(message)
