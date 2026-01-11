"""Tests for executor error types."""


from rice_factor.domain.failures.errors import RiceFactorError
from rice_factor.domain.failures.executor_errors import (
    ArtifactNotApprovedError,
    ArtifactSchemaError,
    ArtifactTypeError,
    DestinationExistsError,
    DiffNotApprovedError,
    ExecutorApplyError,
    ExecutorArtifactError,
    ExecutorCapabilityError,
    ExecutorError,
    ExecutorPreconditionError,
    FileAlreadyExistsError,
    FileWriteError,
    GitApplyError,
    PathEscapesRepoError,
    SourceFileNotFoundError,
    TestsLockedError,
    UnauthorizedFileModificationError,
    UnsupportedOperationError,
)


class TestExecutorErrorHierarchy:
    """Tests for error hierarchy."""

    def test_executor_error_inherits_from_rice_factor_error(self) -> None:
        """ExecutorError should inherit from RiceFactorError."""
        assert issubclass(ExecutorError, RiceFactorError)

    def test_precondition_error_inherits_from_executor_error(self) -> None:
        """ExecutorPreconditionError should inherit from ExecutorError."""
        assert issubclass(ExecutorPreconditionError, ExecutorError)

    def test_capability_error_inherits_from_executor_error(self) -> None:
        """ExecutorCapabilityError should inherit from ExecutorError."""
        assert issubclass(ExecutorCapabilityError, ExecutorError)

    def test_artifact_error_inherits_from_executor_error(self) -> None:
        """ExecutorArtifactError should inherit from ExecutorError."""
        assert issubclass(ExecutorArtifactError, ExecutorError)

    def test_apply_error_inherits_from_executor_error(self) -> None:
        """ExecutorApplyError should inherit from ExecutorError."""
        assert issubclass(ExecutorApplyError, ExecutorError)


class TestPreconditionErrors:
    """Tests for precondition error types."""

    def test_artifact_not_approved_error(self) -> None:
        """ArtifactNotApprovedError should contain artifact info."""
        error = ArtifactNotApprovedError(
            artifact_id="test-uuid",
            current_status="draft",
        )
        assert error.artifact_id == "test-uuid"
        assert error.current_status == "draft"
        assert "test-uuid" in str(error)
        assert "draft" in str(error)
        assert issubclass(ArtifactNotApprovedError, ExecutorPreconditionError)

    def test_file_already_exists_error(self) -> None:
        """FileAlreadyExistsError should contain file path."""
        error = FileAlreadyExistsError(file_path="src/user.py")
        assert error.file_path == "src/user.py"
        assert "src/user.py" in str(error)
        assert issubclass(FileAlreadyExistsError, ExecutorPreconditionError)

    def test_source_file_not_found_error(self) -> None:
        """SourceFileNotFoundError should contain file path."""
        error = SourceFileNotFoundError(file_path="src/missing.py")
        assert error.file_path == "src/missing.py"
        assert "src/missing.py" in str(error)
        assert issubclass(SourceFileNotFoundError, ExecutorPreconditionError)

    def test_path_escapes_repo_error(self) -> None:
        """PathEscapesRepoError should contain path and repo root."""
        error = PathEscapesRepoError(
            path="../../../etc/passwd",
            repo_root="/home/user/project",
        )
        assert error.path == "../../../etc/passwd"
        assert error.repo_root == "/home/user/project"
        assert "escapes" in str(error).lower()
        assert issubclass(PathEscapesRepoError, ExecutorPreconditionError)

    def test_tests_locked_error(self) -> None:
        """TestsLockedError should contain file path."""
        error = TestsLockedError(file_path="tests/test_user.py")
        assert error.file_path == "tests/test_user.py"
        assert "locked" in str(error).lower()
        assert issubclass(TestsLockedError, ExecutorPreconditionError)

    def test_diff_not_approved_error(self) -> None:
        """DiffNotApprovedError should contain diff info."""
        error = DiffNotApprovedError(
            diff_id="diff-uuid",
            current_status="pending",
        )
        assert error.diff_id == "diff-uuid"
        assert error.current_status == "pending"
        assert issubclass(DiffNotApprovedError, ExecutorPreconditionError)

    def test_unauthorized_file_modification_error(self) -> None:
        """UnauthorizedFileModificationError should contain files."""
        error = UnauthorizedFileModificationError(
            unauthorized_files=["secret.py", "config.yaml"],
        )
        assert error.unauthorized_files == ["secret.py", "config.yaml"]
        assert "secret.py" in str(error)
        assert issubclass(UnauthorizedFileModificationError, ExecutorPreconditionError)

    def test_destination_exists_error(self) -> None:
        """DestinationExistsError should contain destination path."""
        error = DestinationExistsError(destination_path="src/new_location.py")
        assert error.destination_path == "src/new_location.py"
        assert "src/new_location.py" in str(error)
        assert issubclass(DestinationExistsError, ExecutorPreconditionError)


class TestCapabilityErrors:
    """Tests for capability error types."""

    def test_unsupported_operation_error(self) -> None:
        """UnsupportedOperationError should contain operation and language."""
        error = UnsupportedOperationError(
            operation="extract_interface",
            language="python",
        )
        assert error.operation == "extract_interface"
        assert error.language == "python"
        assert "extract_interface" in str(error)
        assert "python" in str(error)
        assert issubclass(UnsupportedOperationError, ExecutorCapabilityError)


class TestArtifactErrors:
    """Tests for artifact error types."""

    def test_artifact_schema_error(self) -> None:
        """ArtifactSchemaError should contain path and errors."""
        error = ArtifactSchemaError(
            artifact_path="artifacts/plan.json",
            validation_errors=["Missing field: files", "Invalid type: name"],
        )
        assert error.artifact_path == "artifacts/plan.json"
        assert len(error.validation_errors) == 2
        assert "Missing field: files" in str(error)
        assert issubclass(ArtifactSchemaError, ExecutorArtifactError)

    def test_artifact_schema_error_truncates_many_errors(self) -> None:
        """ArtifactSchemaError should truncate many errors."""
        errors = [f"Error {i}" for i in range(10)]
        error = ArtifactSchemaError(
            artifact_path="artifacts/plan.json",
            validation_errors=errors,
        )
        # Should show first 3 and indicate more
        assert "and 7 more" in str(error)

    def test_artifact_type_error(self) -> None:
        """ArtifactTypeError should contain expected and actual types."""
        error = ArtifactTypeError(
            expected_type="ScaffoldPlan",
            actual_type="ProjectPlan",
        )
        assert error.expected_type == "ScaffoldPlan"
        assert error.actual_type == "ProjectPlan"
        assert "ScaffoldPlan" in str(error)
        assert "ProjectPlan" in str(error)
        assert issubclass(ArtifactTypeError, ExecutorArtifactError)


class TestApplyErrors:
    """Tests for apply error types."""

    def test_git_apply_error(self) -> None:
        """GitApplyError should contain diff path and output."""
        error = GitApplyError(
            diff_path="audit/diffs/test.diff",
            git_output="error: patch failed: file.py:10",
            exit_code=1,
        )
        assert error.diff_path == "audit/diffs/test.diff"
        assert "patch failed" in error.git_output
        assert error.exit_code == 1
        assert "test.diff" in str(error)
        assert issubclass(GitApplyError, ExecutorApplyError)

    def test_file_write_error(self) -> None:
        """FileWriteError should contain path and reason."""
        error = FileWriteError(
            file_path="src/user.py",
            reason="Permission denied",
        )
        assert error.file_path == "src/user.py"
        assert error.reason == "Permission denied"
        assert "src/user.py" in str(error)
        assert "Permission denied" in str(error)
        assert issubclass(FileWriteError, ExecutorApplyError)


class TestCustomMessages:
    """Tests for custom error messages."""

    def test_artifact_not_approved_custom_message(self) -> None:
        """Should use custom message when provided."""
        error = ArtifactNotApprovedError(
            artifact_id="test",
            current_status="draft",
            message="Custom error message",
        )
        assert str(error) == "Custom error message"

    def test_file_already_exists_custom_message(self) -> None:
        """Should use custom message when provided."""
        error = FileAlreadyExistsError(
            file_path="test.py",
            message="Custom message",
        )
        assert str(error) == "Custom message"

    def test_unsupported_operation_custom_message(self) -> None:
        """Should use custom message when provided."""
        error = UnsupportedOperationError(
            operation="test",
            language="test",
            message="Custom message",
        )
        assert str(error) == "Custom message"


class TestErrorCatching:
    """Tests for catching errors at different levels."""

    def test_catch_all_executor_errors(self) -> None:
        """Should catch all executor errors with ExecutorError."""
        errors = [
            ArtifactNotApprovedError("id", "draft"),
            FileAlreadyExistsError("path"),
            UnsupportedOperationError("op", "lang"),
            ArtifactSchemaError("path", []),
            GitApplyError("path", "output", 1),
        ]
        for error in errors:
            try:
                raise error
            except ExecutorError:
                pass  # Should catch all

    def test_catch_precondition_errors(self) -> None:
        """Should catch precondition errors specifically."""
        errors = [
            ArtifactNotApprovedError("id", "draft"),
            FileAlreadyExistsError("path"),
            PathEscapesRepoError("path", "root"),
            TestsLockedError("path"),
        ]
        for error in errors:
            try:
                raise error
            except ExecutorPreconditionError:
                pass  # Should catch all precondition errors
