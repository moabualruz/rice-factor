"""Safety enforcement service for MVP integration.

This service provides safety checks that enforce hard-fail conditions
for the MVP workflow. All safety violations result in immediate failure
with clear error messages and recovery guidance.

Hard-Fail Conditions (from M07 requirements):
- M07-E-001: Tests modified after lock
- M07-E-002: Required artifact missing
- M07-E-003: LLM outputs non-JSON (handled by OutputValidator)
- M07-E-004: Diff touches unauthorized files
- M07-E-005: Schema validation fails (handled by Pydantic)
"""

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.failures.cli_errors import MissingPrerequisiteError
from rice_factor.domain.failures.executor_errors import (
    TestsLockedError,
    UnauthorizedFileModificationError,
)

if TYPE_CHECKING:
    from rice_factor.domain.services.artifact_service import ArtifactService
    from rice_factor.domain.services.phase_service import PhaseService


class LockVerificationResult:
    """Result of TestPlan lock verification.

    Attributes:
        is_valid: Whether the lock is intact (no modifications).
        modified_files: List of files that have been modified.
        expected_hashes: Dict of file paths to expected hashes.
        actual_hashes: Dict of file paths to actual hashes.
    """

    def __init__(
        self,
        is_valid: bool,
        modified_files: list[str] | None = None,
        expected_hashes: dict[str, str] | None = None,
        actual_hashes: dict[str, str] | None = None,
    ) -> None:
        """Initialize verification result.

        Args:
            is_valid: Whether the lock is intact.
            modified_files: List of modified file paths.
            expected_hashes: Expected file hashes from lock.
            actual_hashes: Actual computed file hashes.
        """
        self.is_valid = is_valid
        self.modified_files = modified_files or []
        self.expected_hashes = expected_hashes or {}
        self.actual_hashes = actual_hashes or {}


class SafetyEnforcer:
    """Service for enforcing safety constraints in the MVP workflow.

    The SafetyEnforcer provides methods to verify safety conditions
    before executing operations. All methods raise appropriate errors
    when safety violations are detected.

    Attributes:
        project_root: Root directory of the project.
        artifact_service: Service for artifact operations.
        phase_service: Service for phase checking.
    """

    def __init__(
        self,
        project_root: Path,
        artifact_service: "ArtifactService | None" = None,
        phase_service: "PhaseService | None" = None,
    ) -> None:
        """Initialize the safety enforcer.

        Args:
            project_root: Root directory of the project.
            artifact_service: Optional artifact service.
            phase_service: Optional phase service.
        """
        self._project_root = project_root
        self._artifact_service = artifact_service
        self._phase_service = phase_service

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    @property
    def lock_file_path(self) -> Path:
        """Get the path to the lock file."""
        return self._project_root / ".project" / ".lock"

    def check_test_lock_intact(self) -> LockVerificationResult:
        """Verify that test files have not been modified since lock.

        Compares current file hashes against the stored lock file hashes.

        Returns:
            LockVerificationResult with verification status.

        Note:
            Does not raise an error - caller should check is_valid and
            raise TestsLockedError if needed.
        """
        lock_file = self.lock_file_path
        if not lock_file.exists():
            # No lock file means tests aren't locked - this is valid
            return LockVerificationResult(is_valid=True)

        try:
            lock_data = json.loads(lock_file.read_text())
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable lock file
            return LockVerificationResult(is_valid=False, modified_files=["<lock file corrupt>"])

        expected_hashes = lock_data.get("test_files", {})
        if not expected_hashes:
            return LockVerificationResult(is_valid=True)

        modified_files = []
        actual_hashes = {}

        for file_path, expected_hash in expected_hashes.items():
            full_path = self._project_root / file_path
            actual_hash = self._compute_file_hash(full_path)
            actual_hashes[file_path] = actual_hash

            if actual_hash != expected_hash:
                modified_files.append(file_path)

        return LockVerificationResult(
            is_valid=len(modified_files) == 0,
            modified_files=modified_files,
            expected_hashes=expected_hashes,
            actual_hashes=actual_hashes,
        )

    def require_test_lock_intact(self) -> None:
        """Require that test files have not been modified since lock.

        Raises:
            TestsLockedError: If any test files have been modified.
        """
        result = self.check_test_lock_intact()
        if not result.is_valid and result.modified_files:
            # Raise error for the first modified file
            raise TestsLockedError(
                result.modified_files[0],
                message=(
                    f"TestPlan lock violated. Modified files: {', '.join(result.modified_files)}. "
                    "Test files are immutable after lock. "
                    "Recovery: Reset tests to locked state with 'git checkout <test_files>'"
                ),
            )

    def check_artifact_exists(
        self,
        artifact_type: ArtifactType,
        status: ArtifactStatus | None = None,
    ) -> bool:
        """Check if an artifact of the given type exists.

        Args:
            artifact_type: The type of artifact to check.
            status: Optional required status (e.g., APPROVED, LOCKED).

        Returns:
            True if artifact exists (and has required status if specified).
        """
        if self._artifact_service is None:
            return False

        try:
            storage = self._artifact_service.storage
            artifacts = storage.list_by_type(artifact_type)

            if not artifacts:
                return False

            if status is not None:
                return any(a.status == status for a in artifacts)

            return True
        except Exception:
            return False

    def require_artifact_exists(
        self,
        artifact_type: ArtifactType,
        status: ArtifactStatus | None = None,
        command: str = "this command",
    ) -> None:
        """Require that an artifact of the given type exists.

        Args:
            artifact_type: The type of artifact required.
            status: Optional required status.
            command: Command name for error message.

        Raises:
            MissingPrerequisiteError: If artifact doesn't exist.
        """
        if not self.check_artifact_exists(artifact_type, status):
            status_str = f" with status '{status.value}'" if status else ""
            raise MissingPrerequisiteError(
                command,
                f"Required artifact '{artifact_type.value}'{status_str} not found. "
                f"Create it first with 'rice-factor plan {artifact_type.value.replace('_plan', '')}'",
            )

    def check_diff_authorized(
        self,
        diff_content: str,
        authorized_files: set[str],
    ) -> tuple[bool, set[str]]:
        """Check if a diff only touches authorized files.

        Args:
            diff_content: The diff content to check.
            authorized_files: Set of authorized file paths.

        Returns:
            Tuple of (is_authorized, unauthorized_files).
        """
        touched_files = self._parse_diff_files(diff_content)
        unauthorized = touched_files - authorized_files

        return len(unauthorized) == 0, unauthorized

    def require_diff_authorized(
        self,
        diff_content: str,
        authorized_files: set[str],
    ) -> None:
        """Require that a diff only touches authorized files.

        Args:
            diff_content: The diff content to check.
            authorized_files: Set of authorized file paths.

        Raises:
            UnauthorizedFileModificationError: If diff touches unauthorized files.
        """
        is_authorized, unauthorized = self.check_diff_authorized(diff_content, authorized_files)
        if not is_authorized:
            raise UnauthorizedFileModificationError(
                list(unauthorized),
                message=(
                    f"Diff modifies unauthorized files: {', '.join(unauthorized)}. "
                    f"Only these files are authorized: {', '.join(authorized_files)}. "
                    "Recovery: Regenerate diff scoped to authorized files only."
                ),
            )

    def check_phase_valid(self, command: str) -> bool:
        """Check if the current phase allows a command.

        Args:
            command: The command to check.

        Returns:
            True if command is allowed in current phase.
        """
        if self._phase_service is None:
            return True

        return self._phase_service.can_execute(command)

    def require_phase_valid(self, command: str) -> None:
        """Require that the current phase allows a command.

        Args:
            command: The command to execute.

        Raises:
            PhaseError: If command not allowed in current phase.
            MissingPrerequisiteError: If project not initialized.
        """
        if self._phase_service is None:
            return

        self._phase_service.require_phase(command)

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file.

        Args:
            file_path: Path to the file.

        Returns:
            Hash string prefixed with 'sha256:', or '<missing>' if file doesn't exist.
        """
        if not file_path.exists():
            return "<missing>"

        try:
            content = file_path.read_bytes()
            hash_value = hashlib.sha256(content).hexdigest()
            return f"sha256:{hash_value}"
        except OSError:
            return "<error>"

    def _parse_diff_files(self, diff_content: str) -> set[str]:
        """Parse file paths from a diff.

        Args:
            diff_content: The diff content.

        Returns:
            Set of file paths touched by the diff.
        """
        files = set()
        for line in diff_content.split("\n"):
            # Handle unified diff format
            if line.startswith("+++ b/") or line.startswith("--- a/"):
                # Extract path after a/ or b/ prefix
                path = line[6:].strip()
                if path and path != "/dev/null":
                    files.add(path)
            elif line.startswith("+++ ") or line.startswith("--- "):
                # Handle format without a/ b/ prefix
                path = line[4:].strip()
                if path and path != "/dev/null":
                    files.add(path)
            # Handle git diff --stat format
            elif " | " in line and not line.startswith("diff "):
                path = line.split(" | ")[0].strip()
                if path:
                    files.add(path)

        return files
