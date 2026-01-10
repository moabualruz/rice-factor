"""Executor error types.

This module defines the error hierarchy for executor operations. All executor
errors inherit from ExecutorError, which in turn inherits from RiceFactorError.

Error Taxonomy:
    ExecutorError (base)
    ├── ExecutorPreconditionError     # Preconditions not met
    │   ├── ArtifactNotApprovedError  # Artifact not approved
    │   ├── FileAlreadyExistsError    # File already exists
    │   ├── SourceFileNotFoundError   # Source file missing
    │   ├── PathEscapesRepoError      # Path outside repo root
    │   └── TestsLockedError          # Tests locked, can't modify
    │
    ├── ExecutorCapabilityError       # Operation not supported
    │   └── UnsupportedOperationError # Capability check failed
    │
    ├── ExecutorArtifactError         # Invalid artifact
    │   ├── ArtifactSchemaError       # Schema validation failed
    │   └── ArtifactTypeError         # Wrong artifact type
    │
    └── ExecutorApplyError            # Apply failed
        ├── GitApplyError             # git apply failed
        └── FileWriteError            # File write failed
"""

from rice_factor.domain.failures.errors import RiceFactorError


class ExecutorError(RiceFactorError):
    """Base class for all executor errors.

    All executor-related errors inherit from this class, allowing
    for easy catching of any executor error.

    Example:
        >>> try:
        ...     executor.execute(artifact, repo, mode)
        ... except ExecutorError as e:
        ...     print(f"Executor failed: {e}")
    """

    pass


# -----------------------------------------------------------------------------
# Precondition Errors
# -----------------------------------------------------------------------------


class ExecutorPreconditionError(ExecutorError):
    """Base class for precondition violation errors.

    Raised when an executor's preconditions are not met before
    execution can proceed.
    """

    pass


class ArtifactNotApprovedError(ExecutorPreconditionError):
    """Raised when artifact is not approved for execution.

    Executors require artifacts to be in APPROVED status before
    they can be executed.

    Attributes:
        artifact_id: ID of the unapproved artifact.
        current_status: Current status of the artifact.
    """

    def __init__(
        self,
        artifact_id: str,
        current_status: str,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            artifact_id: ID of the unapproved artifact.
            current_status: Current status of the artifact.
            message: Optional custom message.
        """
        self.artifact_id = artifact_id
        self.current_status = current_status
        msg = message or (
            f"Artifact '{artifact_id}' is not approved. "
            f"Current status: {current_status}"
        )
        super().__init__(msg)


class FileAlreadyExistsError(ExecutorPreconditionError):
    """Raised when a file already exists and would be overwritten.

    Scaffold executor raises this when trying to create a file
    that already exists.

    Attributes:
        file_path: Path to the existing file.
    """

    def __init__(self, file_path: str, message: str | None = None) -> None:
        """Initialize the error.

        Args:
            file_path: Path to the existing file.
            message: Optional custom message.
        """
        self.file_path = file_path
        msg = message or f"File already exists: {file_path}"
        super().__init__(msg)


class SourceFileNotFoundError(ExecutorPreconditionError):
    """Raised when a source file is not found.

    Refactor executor raises this when the source file for a
    move or rename operation doesn't exist.

    Attributes:
        file_path: Path to the missing file.
    """

    def __init__(self, file_path: str, message: str | None = None) -> None:
        """Initialize the error.

        Args:
            file_path: Path to the missing file.
            message: Optional custom message.
        """
        self.file_path = file_path
        msg = message or f"Source file not found: {file_path}"
        super().__init__(msg)


class PathEscapesRepoError(ExecutorPreconditionError):
    """Raised when a path escapes the repository root.

    Security check to prevent path traversal attacks. All paths
    must resolve to within the repository root.

    Attributes:
        path: The offending path.
        repo_root: The repository root path.
    """

    def __init__(
        self,
        path: str,
        repo_root: str,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            path: The offending path.
            repo_root: The repository root path.
            message: Optional custom message.
        """
        self.path = path
        self.repo_root = repo_root
        msg = message or (
            f"Path '{path}' escapes repository root '{repo_root}'. "
            "Path traversal is not allowed."
        )
        super().__init__(msg)


class TestsLockedError(ExecutorPreconditionError):
    """Raised when trying to modify test files while tests are locked.

    Once TestPlan is locked, test files cannot be modified by
    any executor.

    Attributes:
        file_path: Path to the test file that would be modified.
    """

    def __init__(self, file_path: str, message: str | None = None) -> None:
        """Initialize the error.

        Args:
            file_path: Path to the test file.
            message: Optional custom message.
        """
        self.file_path = file_path
        msg = message or (
            f"Cannot modify test file '{file_path}': TestPlan is locked. "
            "Test files are immutable after lock."
        )
        super().__init__(msg)


# -----------------------------------------------------------------------------
# Capability Errors
# -----------------------------------------------------------------------------


class ExecutorCapabilityError(ExecutorError):
    """Base class for capability-related errors.

    Raised when an operation is not supported for the target
    language according to the capability registry.
    """

    pass


class UnsupportedOperationError(ExecutorCapabilityError):
    """Raised when an operation is not supported for a language.

    The capability registry determines which operations are
    supported for each language.

    Attributes:
        operation: The unsupported operation.
        language: The target language.
    """

    def __init__(
        self,
        operation: str,
        language: str,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            operation: The unsupported operation.
            language: The target language.
            message: Optional custom message.
        """
        self.operation = operation
        self.language = language
        msg = message or (
            f"Operation '{operation}' is not supported for language '{language}'. "
            "Check capability registry for supported operations."
        )
        super().__init__(msg)


# -----------------------------------------------------------------------------
# Artifact Errors
# -----------------------------------------------------------------------------


class ExecutorArtifactError(ExecutorError):
    """Base class for artifact-related errors.

    Raised when there's an issue with the artifact itself,
    such as schema violations or wrong type.
    """

    pass


class ArtifactSchemaError(ExecutorArtifactError):
    """Raised when artifact fails schema validation.

    Artifacts must conform to their JSON schema before
    they can be executed.

    Attributes:
        artifact_path: Path to the invalid artifact.
        validation_errors: List of validation error messages.
    """

    def __init__(
        self,
        artifact_path: str,
        validation_errors: list[str],
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            artifact_path: Path to the invalid artifact.
            validation_errors: List of validation error messages.
            message: Optional custom message.
        """
        self.artifact_path = artifact_path
        self.validation_errors = validation_errors
        errors_str = "; ".join(validation_errors[:3])
        if len(validation_errors) > 3:
            errors_str += f" (and {len(validation_errors) - 3} more)"
        msg = message or (
            f"Artifact '{artifact_path}' failed schema validation: {errors_str}"
        )
        super().__init__(msg)


class ArtifactTypeError(ExecutorArtifactError):
    """Raised when artifact is of wrong type for the executor.

    Each executor only accepts specific artifact types.

    Attributes:
        expected_type: The expected artifact type.
        actual_type: The actual artifact type.
    """

    def __init__(
        self,
        expected_type: str,
        actual_type: str,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            expected_type: The expected artifact type.
            actual_type: The actual artifact type.
            message: Optional custom message.
        """
        self.expected_type = expected_type
        self.actual_type = actual_type
        msg = message or (
            f"Expected artifact type '{expected_type}', got '{actual_type}'"
        )
        super().__init__(msg)


# -----------------------------------------------------------------------------
# Apply Errors
# -----------------------------------------------------------------------------


class ExecutorApplyError(ExecutorError):
    """Base class for apply-related errors.

    Raised when the diff generation or application fails.
    """

    pass


class GitApplyError(ExecutorApplyError):
    """Raised when git apply fails.

    The diff executor uses git apply to apply patches.

    Attributes:
        diff_path: Path to the diff file.
        git_output: Output from git apply command.
        exit_code: Exit code from git apply.
    """

    def __init__(
        self,
        diff_path: str,
        git_output: str,
        exit_code: int,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            diff_path: Path to the diff file.
            git_output: Output from git apply command.
            exit_code: Exit code from git apply.
            message: Optional custom message.
        """
        self.diff_path = diff_path
        self.git_output = git_output
        self.exit_code = exit_code
        msg = message or (
            f"git apply failed for '{diff_path}' (exit code {exit_code}): "
            f"{git_output[:200]}"
        )
        super().__init__(msg)


class FileWriteError(ExecutorApplyError):
    """Raised when file write operation fails.

    Scaffold executor raises this when it cannot write a file.

    Attributes:
        file_path: Path to the file.
        reason: Reason for the failure.
    """

    def __init__(
        self,
        file_path: str,
        reason: str,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            file_path: Path to the file.
            reason: Reason for the failure.
            message: Optional custom message.
        """
        self.file_path = file_path
        self.reason = reason
        msg = message or f"Failed to write file '{file_path}': {reason}"
        super().__init__(msg)


class DiffNotApprovedError(ExecutorPreconditionError):
    """Raised when a diff is not approved for application.

    The diff executor requires diffs to be approved before
    they can be applied.

    Attributes:
        diff_id: ID of the unapproved diff.
        current_status: Current status of the diff.
    """

    def __init__(
        self,
        diff_id: str,
        current_status: str,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            diff_id: ID of the unapproved diff.
            current_status: Current status of the diff.
            message: Optional custom message.
        """
        self.diff_id = diff_id
        self.current_status = current_status
        msg = message or (
            f"Diff '{diff_id}' is not approved. Current status: {current_status}"
        )
        super().__init__(msg)


class UnauthorizedFileModificationError(ExecutorPreconditionError):
    """Raised when diff touches files not declared in the plan.

    Diffs can only modify files that were declared in the
    associated ImplementationPlan.

    Attributes:
        unauthorized_files: List of unauthorized file paths.
    """

    def __init__(
        self,
        unauthorized_files: list[str],
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            unauthorized_files: List of unauthorized file paths.
            message: Optional custom message.
        """
        self.unauthorized_files = unauthorized_files
        files_str = ", ".join(unauthorized_files[:5])
        if len(unauthorized_files) > 5:
            files_str += f" (and {len(unauthorized_files) - 5} more)"
        msg = message or f"Diff modifies unauthorized files: {files_str}"
        super().__init__(msg)


class DestinationExistsError(ExecutorPreconditionError):
    """Raised when move destination already exists.

    Refactor executor raises this when the destination for
    a move operation already exists.

    Attributes:
        destination_path: Path to the existing destination.
    """

    def __init__(
        self,
        destination_path: str,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            destination_path: Path to the existing destination.
            message: Optional custom message.
        """
        self.destination_path = destination_path
        msg = message or f"Destination already exists: {destination_path}"
        super().__init__(msg)
