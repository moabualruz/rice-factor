"""Tests for ScaffoldExecutor."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import BaseModel

from rice_factor.adapters.executors.audit_logger import AuditLogger
from rice_factor.adapters.executors.scaffold_executor import ScaffoldExecutor
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.execution_types import ExecutionMode
from rice_factor.domain.artifacts.payloads.scaffold_plan import (
    FileEntry,
    FileKind,
    ScaffoldPlanPayload,
)
from rice_factor.domain.ports.executor import ExecutorPort


def create_scaffold_artifact(
    status: ArtifactStatus = ArtifactStatus.APPROVED,
    files: list[dict[str, Any]] | None = None,
) -> ArtifactEnvelope[ScaffoldPlanPayload]:
    """Create a scaffold plan artifact for testing."""
    if files is None:
        files = [
            {"path": "src/user.py", "description": "User model", "kind": "source"},
            {"path": "src/auth.py", "description": "Auth module", "kind": "source"},
        ]

    payload = ScaffoldPlanPayload(
        files=[
            FileEntry(path=f["path"], description=f["description"], kind=f["kind"])
            for f in files
        ]
    )

    return ArtifactEnvelope[ScaffoldPlanPayload](
        artifact_type=ArtifactType.SCAFFOLD_PLAN,
        status=status,
        payload=payload,
    )


class TestScaffoldExecutorProtocol:
    """Tests for ScaffoldExecutor protocol compliance."""

    def test_implements_executor_port(self, tmp_path: Path) -> None:
        """ScaffoldExecutor should implement ExecutorPort protocol."""
        storage = MagicMock()
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )
        assert isinstance(executor, ExecutorPort)

    def test_has_execute_method(self, tmp_path: Path) -> None:
        """ScaffoldExecutor should have execute method."""
        storage = MagicMock()
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )
        assert hasattr(executor, "execute")


class TestScaffoldExecutorDryRun:
    """Tests for DRY_RUN mode."""

    def test_dry_run_generates_diff_without_creating_files(
        self, tmp_path: Path
    ) -> None:
        """DRY_RUN mode should generate diff but not create files."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        artifact_path = tmp_path / "artifact.json"
        result = executor.execute(
            artifact_path=artifact_path,
            repo_root=tmp_path,
            mode=ExecutionMode.DRY_RUN,
        )

        assert result.success
        # Files should NOT be created
        assert not (tmp_path / "src" / "user.py").exists()
        assert not (tmp_path / "src" / "auth.py").exists()

    def test_dry_run_logs_would_create(self, tmp_path: Path) -> None:
        """DRY_RUN mode should log what would be created."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        artifact_path = tmp_path / "artifact.json"
        result = executor.execute(
            artifact_path=artifact_path,
            repo_root=tmp_path,
            mode=ExecutionMode.DRY_RUN,
        )

        assert any("Would create" in log for log in result.logs)


class TestScaffoldExecutorApply:
    """Tests for APPLY mode."""

    def test_apply_creates_files(self, tmp_path: Path) -> None:
        """APPLY mode should create the files."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        artifact_path = tmp_path / "artifact.json"
        result = executor.execute(
            artifact_path=artifact_path,
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.success
        # Files should be created
        assert (tmp_path / "src" / "user.py").exists()
        assert (tmp_path / "src" / "auth.py").exists()

    def test_apply_creates_parent_directories(self, tmp_path: Path) -> None:
        """APPLY mode should create parent directories."""
        storage = MagicMock()
        artifact = create_scaffold_artifact(
            files=[
                {
                    "path": "deep/nested/dir/file.py",
                    "description": "Deep file",
                    "kind": "source",
                }
            ]
        )
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.success
        assert (tmp_path / "deep" / "nested" / "dir" / "file.py").exists()

    def test_apply_files_have_todo_comments(self, tmp_path: Path) -> None:
        """Created files should have TODO comments."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        content = (tmp_path / "src" / "user.py").read_text()
        assert "TODO" in content

    def test_apply_logs_created_files(self, tmp_path: Path) -> None:
        """APPLY mode should log created files."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert any("Created" in log for log in result.logs)


class TestScaffoldExecutorSkipsExisting:
    """Tests for skipping existing files."""

    def test_skips_existing_files(self, tmp_path: Path) -> None:
        """Should skip files that already exist."""
        # Create existing file
        (tmp_path / "src").mkdir()
        existing_file = tmp_path / "src" / "user.py"
        existing_file.write_text("# existing content")

        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.success
        # Existing file should NOT be overwritten
        assert existing_file.read_text() == "# existing content"
        # Other file should be created
        assert (tmp_path / "src" / "auth.py").exists()

    def test_logs_skipped_files(self, tmp_path: Path) -> None:
        """Should log skipped files."""
        # Create existing file
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "user.py").write_text("# existing")

        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert any("Skipped" in log or "skip" in log.lower() for log in result.logs)


class TestScaffoldExecutorArtifactValidation:
    """Tests for artifact validation."""

    def test_rejects_unapproved_artifact(self, tmp_path: Path) -> None:
        """Should reject artifacts that are not approved."""
        storage = MagicMock()
        artifact = create_scaffold_artifact(status=ArtifactStatus.DRAFT)
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any("not approved" in error.lower() for error in result.errors)

    def test_rejects_wrong_artifact_type(self, tmp_path: Path) -> None:
        """Should reject artifacts that are not ScaffoldPlan."""
        storage = MagicMock()
        # Create a different artifact type
        wrong_artifact = MagicMock()
        wrong_artifact.artifact_type = ArtifactType.PROJECT_PLAN
        wrong_artifact.status = ArtifactStatus.APPROVED
        storage.load.return_value = wrong_artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any(
            "scaffoldplan" in error.lower() or "type" in error.lower()
            for error in result.errors
        )


class TestScaffoldExecutorPathSecurity:
    """Tests for path security."""

    def test_rejects_path_traversal(self, tmp_path: Path) -> None:
        """Should reject paths that escape the repo."""
        storage = MagicMock()
        artifact = create_scaffold_artifact(
            files=[
                {
                    "path": "../../../etc/passwd",
                    "description": "Bad path",
                    "kind": "source",
                }
            ]
        )
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any("escape" in error.lower() for error in result.errors)


class TestScaffoldExecutorAuditLogging:
    """Tests for audit logging."""

    def test_generates_audit_log_entry_on_success(self, tmp_path: Path) -> None:
        """Should create audit log entry on success."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        # Check audit log exists and has entry
        log_path = tmp_path / "audit" / "executions.log"
        assert log_path.exists()
        entries = audit_logger.read_all_entries()
        assert len(entries) >= 1
        assert entries[-1].executor == "scaffold"
        assert entries[-1].is_success

    def test_generates_audit_log_entry_on_failure(self, tmp_path: Path) -> None:
        """Should create audit log entry on failure."""
        storage = MagicMock()
        artifact = create_scaffold_artifact(status=ArtifactStatus.DRAFT)
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        entries = audit_logger.read_all_entries()
        assert len(entries) >= 1
        assert entries[-1].is_failure


class TestScaffoldExecutorDiffGeneration:
    """Tests for diff generation."""

    def test_generates_diff_file(self, tmp_path: Path) -> None:
        """Should generate a diff file."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.DRY_RUN,
        )

        assert result.success
        assert len(result.diffs) >= 1
        diff_path = tmp_path / result.diffs[0]
        assert diff_path.exists()

    def test_diff_contains_file_creation(self, tmp_path: Path) -> None:
        """Diff should show file creation."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.DRY_RUN,
        )

        diff_path = tmp_path / result.diffs[0]
        diff_content = diff_path.read_text()
        assert "new file" in diff_content or "+++" in diff_content


class TestScaffoldExecutorResult:
    """Tests for ExecutionResult."""

    def test_result_contains_diffs_list(self, tmp_path: Path) -> None:
        """Result should contain list of diff paths."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert isinstance(result.diffs, list)

    def test_result_contains_logs(self, tmp_path: Path) -> None:
        """Result should contain execution logs."""
        storage = MagicMock()
        artifact = create_scaffold_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = ScaffoldExecutor(
            storage=storage,
            audit_logger=audit_logger,
            project_root=tmp_path,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert isinstance(result.logs, list)
        assert len(result.logs) > 0
