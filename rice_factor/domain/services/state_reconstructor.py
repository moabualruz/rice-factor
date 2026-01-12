"""State reconstruction service for long-running project support.

This module provides the StateReconstructor service that reconstructs project
state from artifacts, audit logs, and git history. It enables resuming work
on projects that were interrupted or need to be recovered.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


class StoragePort(Protocol):
    """Protocol for artifact storage operations."""

    def list_all(self) -> list[Any]:
        """List all artifacts."""
        ...


class AuditLogReaderPort(Protocol):
    """Protocol for reading audit log entries."""

    def read_all_entries(self) -> list[Any]:
        """Read all audit log entries."""
        ...


class ReconstructionSource(Enum):
    """Source of reconstruction data."""

    ARTIFACT = "artifact"
    AUDIT_LOG = "audit_log"
    GIT_HISTORY = "git_history"


@dataclass
class FileState:
    """State of a single file in the project."""

    path: str
    exists: bool
    last_modified: datetime | None = None
    last_commit_hash: str | None = None
    covered_by_artifact: str | None = None
    execution_count: int = 0
    last_execution: datetime | None = None


@dataclass
class ArtifactState:
    """Reconstructed state of an artifact."""

    artifact_id: str
    artifact_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    depends_on: list[str]
    target_files: list[str]
    execution_history: list[dict[str, Any]]
    is_stale: bool = False
    staleness_reason: str | None = None


@dataclass
class GitCommitInfo:
    """Information about a git commit."""

    commit_hash: str
    author: str
    timestamp: datetime
    message: str
    files_changed: list[str]


@dataclass
class ReconstructionIssue:
    """An issue discovered during state reconstruction."""

    source: ReconstructionSource
    severity: str  # "warning" or "error"
    message: str
    related_path: str | None = None
    related_artifact_id: str | None = None


@dataclass
class ReconstructedState:
    """Complete reconstructed project state."""

    reconstructed_at: datetime
    repo_root: Path
    artifacts: list[ArtifactState]
    files: dict[str, FileState]
    issues: list[ReconstructionIssue]
    recent_commits: list[GitCommitInfo]
    audit_entry_count: int
    git_available: bool

    @property
    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warning-level issues."""
        return any(i.severity == "warning" for i in self.issues)

    @property
    def artifact_count(self) -> int:
        """Get total number of artifacts."""
        return len(self.artifacts)

    @property
    def stale_artifact_count(self) -> int:
        """Get number of stale artifacts."""
        return sum(1 for a in self.artifacts if a.is_stale)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "reconstructed_at": self.reconstructed_at.isoformat(),
            "repo_root": str(self.repo_root),
            "artifact_count": self.artifact_count,
            "stale_artifact_count": self.stale_artifact_count,
            "file_count": len(self.files),
            "issue_count": len(self.issues),
            "error_count": sum(1 for i in self.issues if i.severity == "error"),
            "warning_count": sum(1 for i in self.issues if i.severity == "warning"),
            "audit_entry_count": self.audit_entry_count,
            "recent_commit_count": len(self.recent_commits),
            "git_available": self.git_available,
            "issues": [
                {
                    "source": i.source.value,
                    "severity": i.severity,
                    "message": i.message,
                    "related_path": i.related_path,
                    "related_artifact_id": i.related_artifact_id,
                }
                for i in self.issues
            ],
        }


@dataclass
class StateReconstructor:
    """Service for reconstructing project state from multiple sources.

    This service combines data from artifacts, audit logs, and git history
    to reconstruct the complete state of a project. It's useful for:
    - Resuming work after interruption
    - Validating project integrity
    - Detecting drift between code and artifacts
    - Generating state reports

    Attributes:
        repo_root: Root directory of the repository.
        storage: Optional storage port for loading artifacts.
        audit_reader: Optional audit log reader.
    """

    repo_root: Path
    storage: StoragePort | None = None
    audit_reader: AuditLogReaderPort | None = None
    _git_available: bool | None = field(default=None, init=False)

    def reconstruct(self) -> ReconstructedState:
        """Reconstruct complete project state.

        Returns:
            ReconstructedState containing artifacts, files, and issues.
        """
        issues: list[ReconstructionIssue] = []

        # Analyze artifacts
        artifacts, artifact_issues = self._analyze_artifacts()
        issues.extend(artifact_issues)

        # Build file state map from artifacts
        files: dict[str, FileState] = {}
        for artifact in artifacts:
            for target in artifact.target_files:
                if target not in files:
                    files[target] = FileState(
                        path=target,
                        exists=self._file_exists(target),
                        covered_by_artifact=artifact.artifact_id,
                    )

        # Analyze audit log
        execution_data, audit_issues, entry_count = self._analyze_audit_log()
        issues.extend(audit_issues)

        # Update artifacts with execution history
        for artifact in artifacts:
            artifact.execution_history = execution_data.get(artifact.artifact_id, [])

        # Update file states with execution counts
        for path, file_state in files.items():
            execution_count = sum(
                1 for entry in execution_data.values()
                for ex in entry
                if path in ex.get("files_affected", [])
            )
            file_state.execution_count = execution_count

        # Analyze git history
        commits, git_issues = self._analyze_git_history()
        issues.extend(git_issues)

        # Update file states with git info
        for commit in commits:
            for changed_file in commit.files_changed:
                if changed_file in files:
                    if files[changed_file].last_commit_hash is None:
                        files[changed_file].last_commit_hash = commit.commit_hash
                        files[changed_file].last_modified = commit.timestamp

        # Check for orphaned files (modified but not covered by artifacts)
        orphan_issues = self._detect_orphaned_modifications(files, commits, artifacts)
        issues.extend(orphan_issues)

        return ReconstructedState(
            reconstructed_at=datetime.now(UTC),
            repo_root=self.repo_root,
            artifacts=artifacts,
            files=files,
            issues=issues,
            recent_commits=commits,
            audit_entry_count=entry_count,
            git_available=self._check_git_available(),
        )

    def _analyze_artifacts(
        self,
    ) -> tuple[list[ArtifactState], list[ReconstructionIssue]]:
        """Analyze artifacts from storage.

        Returns:
            Tuple of (artifact states, issues).
        """
        artifacts: list[ArtifactState] = []
        issues: list[ReconstructionIssue] = []

        if self.storage is None:
            # Try to load artifacts from filesystem
            artifacts_from_fs, fs_issues = self._load_artifacts_from_filesystem()
            return artifacts_from_fs, fs_issues

        try:
            all_artifacts = self.storage.list_all()
            for artifact in all_artifacts:
                state = self._artifact_to_state(artifact)
                artifacts.append(state)

                # Check for staleness
                if self._is_artifact_stale(artifact):
                    state.is_stale = True
                    state.staleness_reason = "Artifact has not been updated recently"
                    issues.append(
                        ReconstructionIssue(
                            source=ReconstructionSource.ARTIFACT,
                            severity="warning",
                            message=f"Stale artifact: {state.artifact_type}",
                            related_artifact_id=state.artifact_id,
                        )
                    )

        except Exception as e:
            issues.append(
                ReconstructionIssue(
                    source=ReconstructionSource.ARTIFACT,
                    severity="error",
                    message=f"Failed to load artifacts: {e}",
                )
            )

        return artifacts, issues

    def _load_artifacts_from_filesystem(
        self,
    ) -> tuple[list[ArtifactState], list[ReconstructionIssue]]:
        """Load artifacts directly from filesystem.

        Returns:
            Tuple of (artifact states, issues).
        """
        artifacts: list[ArtifactState] = []
        issues: list[ReconstructionIssue] = []

        artifacts_dir = self.repo_root / "artifacts"
        if not artifacts_dir.exists():
            return artifacts, issues

        for json_path in artifacts_dir.rglob("*.json"):
            if "_meta" in str(json_path):
                continue

            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                state = self._dict_to_artifact_state(data)
                artifacts.append(state)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                issues.append(
                    ReconstructionIssue(
                        source=ReconstructionSource.ARTIFACT,
                        severity="warning",
                        message=f"Failed to parse artifact {json_path.name}: {e}",
                        related_path=str(json_path),
                    )
                )

        return artifacts, issues

    def _artifact_to_state(self, artifact: Any) -> ArtifactState:
        """Convert an artifact envelope to ArtifactState.

        Args:
            artifact: Artifact envelope object.

        Returns:
            ArtifactState representation.
        """
        # Extract target files based on artifact type
        target_files = self._extract_target_files(artifact)

        return ArtifactState(
            artifact_id=str(artifact.id),
            artifact_type=str(artifact.artifact_type.value),
            status=str(artifact.status.value),
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
            depends_on=[str(dep) for dep in artifact.depends_on],
            target_files=target_files,
            execution_history=[],
        )

    def _dict_to_artifact_state(self, data: dict[str, Any]) -> ArtifactState:
        """Convert a dictionary to ArtifactState.

        Args:
            data: Artifact data dictionary.

        Returns:
            ArtifactState representation.
        """
        # Parse timestamps
        created_at = self._parse_timestamp(data.get("created_at", ""))
        updated_at = self._parse_timestamp(data.get("updated_at", ""))

        # Extract target files from payload
        target_files = self._extract_target_files_from_dict(data)

        return ArtifactState(
            artifact_id=str(data.get("id", "")),
            artifact_type=str(data.get("artifact_type", "")),
            status=str(data.get("status", "draft")),
            created_at=created_at,
            updated_at=updated_at,
            depends_on=[str(d) for d in data.get("depends_on", [])],
            target_files=target_files,
            execution_history=[],
        )

    def _extract_target_files(self, artifact: Any) -> list[str]:
        """Extract target files from an artifact.

        Args:
            artifact: Artifact envelope object.

        Returns:
            List of target file paths.
        """
        targets: list[str] = []
        payload = artifact.payload

        if payload is None:
            return targets

        # Check for common target field patterns
        if hasattr(payload, "target") and payload.target is not None:
            targets.append(str(payload.target))
        if hasattr(payload, "files") and payload.files is not None:
            targets.extend(str(f) for f in payload.files)
        if hasattr(payload, "from_path") and payload.from_path is not None:
            targets.append(str(payload.from_path))
        if hasattr(payload, "to_path") and payload.to_path is not None:
            targets.append(str(payload.to_path))

        return targets

    def _extract_target_files_from_dict(self, data: dict[str, Any]) -> list[str]:
        """Extract target files from artifact dictionary.

        Args:
            data: Artifact data dictionary.

        Returns:
            List of target file paths.
        """
        targets: list[str] = []
        payload = data.get("payload", {})

        if isinstance(payload, dict):
            if "target" in payload:
                targets.append(str(payload["target"]))
            if "files" in payload:
                targets.extend(str(f) for f in payload["files"])
            if "from_path" in payload:
                targets.append(str(payload["from_path"]))
            if "to_path" in payload:
                targets.append(str(payload["to_path"]))

        return targets

    def _is_artifact_stale(self, artifact: Any) -> bool:
        """Check if an artifact is stale.

        Args:
            artifact: Artifact envelope object.

        Returns:
            True if stale, False otherwise.
        """
        # Consider stale if not updated in 90 days
        stale_threshold_days = 90
        if hasattr(artifact, "age_days"):
            return artifact.age_days > stale_threshold_days
        return False

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse a timestamp string.

        Args:
            timestamp_str: ISO format timestamp string.

        Returns:
            Parsed datetime (or current time if parsing fails).
        """
        if not timestamp_str:
            return datetime.now(UTC)

        try:
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            return datetime.now(UTC)

    def _analyze_audit_log(
        self,
    ) -> tuple[dict[str, list[dict[str, Any]]], list[ReconstructionIssue], int]:
        """Analyze audit log for execution history.

        Returns:
            Tuple of (execution data by artifact, issues, entry count).
        """
        execution_data: dict[str, list[dict[str, Any]]] = {}
        issues: list[ReconstructionIssue] = []
        entry_count = 0

        audit_log_path = self.repo_root / "audit" / "executions.log"
        if not audit_log_path.exists():
            return execution_data, issues, 0

        try:
            lines = audit_log_path.read_text(encoding="utf-8").strip().split("\n")
            for line in lines:
                if not line.strip():
                    continue

                entry_count += 1
                try:
                    entry = json.loads(line)
                    artifact_path = entry.get("artifact", "")

                    # Extract artifact ID from path if present
                    artifact_id = self._extract_artifact_id_from_path(artifact_path)

                    if artifact_id not in execution_data:
                        execution_data[artifact_id] = []

                    execution_data[artifact_id].append({
                        "timestamp": entry.get("timestamp"),
                        "executor": entry.get("executor"),
                        "status": entry.get("status"),
                        "mode": entry.get("mode"),
                        "files_affected": entry.get("files_affected", []),
                        "error": entry.get("error"),
                    })

                except json.JSONDecodeError:
                    issues.append(
                        ReconstructionIssue(
                            source=ReconstructionSource.AUDIT_LOG,
                            severity="warning",
                            message=f"Malformed audit log entry at line {entry_count}",
                        )
                    )

        except OSError as e:
            issues.append(
                ReconstructionIssue(
                    source=ReconstructionSource.AUDIT_LOG,
                    severity="error",
                    message=f"Failed to read audit log: {e}",
                    related_path=str(audit_log_path),
                )
            )

        return execution_data, issues, entry_count

    def _extract_artifact_id_from_path(self, path: str) -> str:
        """Extract artifact ID from an artifact path.

        Args:
            path: Artifact file path.

        Returns:
            Artifact ID or the original path.
        """
        # Artifacts are stored as <id>.json
        # e.g., artifacts/implementation_plans/abc123.json
        if "/" in path:
            filename = path.split("/")[-1]
            if filename.endswith(".json"):
                return filename[:-5]
        return path

    def _analyze_git_history(
        self,
    ) -> tuple[list[GitCommitInfo], list[ReconstructionIssue]]:
        """Analyze git history for recent changes.

        Returns:
            Tuple of (recent commits, issues).
        """
        commits: list[GitCommitInfo] = []
        issues: list[ReconstructionIssue] = []

        if not self._check_git_available():
            return commits, issues

        try:
            # Get recent commits with file changes
            result = subprocess.run(
                [
                    "git", "log",
                    "--pretty=format:%H|%an|%at|%s",
                    "--name-only",
                    "-n", "50",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                issues.append(
                    ReconstructionIssue(
                        source=ReconstructionSource.GIT_HISTORY,
                        severity="warning",
                        message=f"Git log failed: {result.stderr}",
                    )
                )
                return commits, issues

            commits = self._parse_git_log(result.stdout)

        except subprocess.TimeoutExpired:
            issues.append(
                ReconstructionIssue(
                    source=ReconstructionSource.GIT_HISTORY,
                    severity="warning",
                    message="Git log timed out",
                )
            )
        except FileNotFoundError:
            issues.append(
                ReconstructionIssue(
                    source=ReconstructionSource.GIT_HISTORY,
                    severity="warning",
                    message="Git not found in PATH",
                )
            )
        except Exception as e:
            issues.append(
                ReconstructionIssue(
                    source=ReconstructionSource.GIT_HISTORY,
                    severity="error",
                    message=f"Failed to analyze git history: {e}",
                )
            )

        return commits, issues

    def _parse_git_log(self, log_output: str) -> list[GitCommitInfo]:
        """Parse git log output into GitCommitInfo objects.

        Args:
            log_output: Output from git log command.

        Returns:
            List of GitCommitInfo objects.
        """
        commits: list[GitCommitInfo] = []
        current_commit: dict[str, Any] | None = None
        current_files: list[str] = []

        for line in log_output.strip().split("\n"):
            if not line:
                # Empty line separates commits
                if current_commit:
                    commits.append(
                        GitCommitInfo(
                            commit_hash=current_commit["hash"],
                            author=current_commit["author"],
                            timestamp=current_commit["timestamp"],
                            message=current_commit["message"],
                            files_changed=current_files,
                        )
                    )
                    current_commit = None
                    current_files = []
                continue

            if "|" in line and len(line.split("|")) >= 4:
                # This is a commit header line
                if current_commit:
                    commits.append(
                        GitCommitInfo(
                            commit_hash=current_commit["hash"],
                            author=current_commit["author"],
                            timestamp=current_commit["timestamp"],
                            message=current_commit["message"],
                            files_changed=current_files,
                        )
                    )
                    current_files = []

                parts = line.split("|")
                try:
                    timestamp = datetime.fromtimestamp(int(parts[2]), tz=UTC)
                except (ValueError, IndexError):
                    timestamp = datetime.now(UTC)

                current_commit = {
                    "hash": parts[0],
                    "author": parts[1],
                    "timestamp": timestamp,
                    "message": "|".join(parts[3:]) if len(parts) > 3 else "",
                }
            elif current_commit:
                # This is a file changed line
                current_files.append(line)

        # Don't forget the last commit
        if current_commit:
            commits.append(
                GitCommitInfo(
                    commit_hash=current_commit["hash"],
                    author=current_commit["author"],
                    timestamp=current_commit["timestamp"],
                    message=current_commit["message"],
                    files_changed=current_files,
                )
            )

        return commits

    def _check_git_available(self) -> bool:
        """Check if git is available.

        Returns:
            True if git is available, False otherwise.
        """
        if self._git_available is not None:
            return self._git_available

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_root,
                capture_output=True,
                timeout=5,
            )
            self._git_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._git_available = False

        return self._git_available

    def _file_exists(self, path: str) -> bool:
        """Check if a file exists in the repo.

        Args:
            path: Relative file path.

        Returns:
            True if file exists.
        """
        full_path = self.repo_root / path
        return full_path.exists()

    def _detect_orphaned_modifications(
        self,
        files: dict[str, FileState],
        commits: list[GitCommitInfo],
        artifacts: list[ArtifactState],
    ) -> list[ReconstructionIssue]:
        """Detect files modified in git but not covered by artifacts.

        Args:
            files: Known file states.
            commits: Recent git commits.
            artifacts: All artifacts.

        Returns:
            List of issues for orphaned modifications.
        """
        issues: list[ReconstructionIssue] = []

        # Get all files covered by artifacts
        covered_files = set(files.keys())

        # Check git history for modifications to uncovered files
        for commit in commits[:20]:  # Check recent commits
            for changed_file in commit.files_changed:
                # Skip non-source files
                if not self._is_source_file(changed_file):
                    continue

                if changed_file not in covered_files:
                    issues.append(
                        ReconstructionIssue(
                            source=ReconstructionSource.GIT_HISTORY,
                            severity="warning",
                            message=f"File modified without artifact coverage: {changed_file}",
                            related_path=changed_file,
                        )
                    )
                    # Add to covered so we don't report duplicates
                    covered_files.add(changed_file)

        return issues

    def _is_source_file(self, path: str) -> bool:
        """Check if a path is a source file.

        Args:
            path: File path.

        Returns:
            True if it's a source file.
        """
        source_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx",
            ".java", ".kt", ".go", ".rs",
            ".c", ".cpp", ".h", ".hpp",
            ".rb", ".php", ".cs", ".swift",
        }

        # Check extension
        for ext in source_extensions:
            if path.endswith(ext):
                return True

        return False

    def get_resumable_artifacts(self) -> list[ArtifactState]:
        """Get artifacts that can be resumed.

        Returns:
            List of artifacts in draft status.
        """
        state = self.reconstruct()
        return [a for a in state.artifacts if a.status == "draft"]

    def get_pending_executions(self) -> list[ArtifactState]:
        """Get approved artifacts pending execution.

        Returns:
            List of artifacts that are approved but not yet executed.
        """
        state = self.reconstruct()
        pending: list[ArtifactState] = []

        for artifact in state.artifacts:
            if artifact.status in ("approved", "APPROVED"):
                # Check if it has any successful executions
                has_success = any(
                    ex.get("status") == "success"
                    for ex in artifact.execution_history
                )
                if not has_success:
                    pending.append(artifact)

        return pending

    def get_failed_executions(self) -> list[tuple[ArtifactState, dict[str, Any]]]:
        """Get artifacts with failed executions.

        Returns:
            List of (artifact, last_failure) tuples.
        """
        state = self.reconstruct()
        failed: list[tuple[ArtifactState, dict[str, Any]]] = []

        for artifact in state.artifacts:
            failures = [
                ex for ex in artifact.execution_history
                if ex.get("status") == "failure"
            ]
            if failures:
                # Get most recent failure
                last_failure = failures[-1]
                failed.append((artifact, last_failure))

        return failed
