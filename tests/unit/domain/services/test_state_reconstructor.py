"""Unit tests for StateReconstructor service."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from rice_factor.domain.services.state_reconstructor import (
    ArtifactState,
    FileState,
    GitCommitInfo,
    ReconstructedState,
    ReconstructionIssue,
    ReconstructionSource,
    StateReconstructor,
)


@dataclass
class MockArtifact:
    """Mock artifact for testing."""

    id: str
    artifact_type: MockArtifactType
    status: MockStatus
    created_at: datetime
    updated_at: datetime
    depends_on: list[str] = field(default_factory=list)
    payload: Any = None
    age_days: int = 0


@dataclass
class MockArtifactType:
    value: str


@dataclass
class MockStatus:
    value: str


@dataclass
class MockPayload:
    target: str | None = None
    files: list[str] | None = None
    from_path: str | None = None
    to_path: str | None = None


@dataclass
class MockStorage:
    """Mock storage port for testing."""

    artifacts: list[Any] = field(default_factory=list)
    should_fail: bool = False

    def list_all(self) -> list[Any]:
        if self.should_fail:
            raise RuntimeError("Storage failure")
        return self.artifacts


@dataclass
class MockAuditReader:
    """Mock audit reader for testing."""

    entries: list[dict[str, Any]] = field(default_factory=list)

    def read_all_entries(self) -> list[dict[str, Any]]:
        return self.entries


class TestFileState:
    """Tests for FileState dataclass."""

    def test_creation(self) -> None:
        """FileState should be creatable with minimal args."""
        state = FileState(path="src/main.py", exists=True)
        assert state.path == "src/main.py"
        assert state.exists is True
        assert state.last_modified is None
        assert state.execution_count == 0

    def test_full_creation(self) -> None:
        """FileState should accept all fields."""
        now = datetime.now(UTC)
        state = FileState(
            path="src/main.py",
            exists=True,
            last_modified=now,
            last_commit_hash="abc123",
            covered_by_artifact="artifact-1",
            execution_count=5,
            last_execution=now,
        )
        assert state.last_commit_hash == "abc123"
        assert state.covered_by_artifact == "artifact-1"


class TestArtifactState:
    """Tests for ArtifactState dataclass."""

    def test_creation(self) -> None:
        """ArtifactState should be creatable."""
        now = datetime.now(UTC)
        state = ArtifactState(
            artifact_id="test-123",
            artifact_type="ImplementationPlan",
            status="approved",
            created_at=now,
            updated_at=now,
            depends_on=[],
            target_files=["src/main.py"],
            execution_history=[],
        )
        assert state.artifact_id == "test-123"
        assert state.is_stale is False

    def test_staleness(self) -> None:
        """ArtifactState should track staleness."""
        now = datetime.now(UTC)
        state = ArtifactState(
            artifact_id="test-123",
            artifact_type="ImplementationPlan",
            status="draft",
            created_at=now,
            updated_at=now,
            depends_on=[],
            target_files=[],
            execution_history=[],
            is_stale=True,
            staleness_reason="Too old",
        )
        assert state.is_stale is True
        assert state.staleness_reason == "Too old"


class TestGitCommitInfo:
    """Tests for GitCommitInfo dataclass."""

    def test_creation(self) -> None:
        """GitCommitInfo should be creatable."""
        now = datetime.now(UTC)
        commit = GitCommitInfo(
            commit_hash="abc123def",
            author="Test User",
            timestamp=now,
            message="Test commit",
            files_changed=["src/main.py", "src/utils.py"],
        )
        assert commit.commit_hash == "abc123def"
        assert len(commit.files_changed) == 2


class TestReconstructedState:
    """Tests for ReconstructedState dataclass."""

    def test_creation(self) -> None:
        """ReconstructedState should be creatable."""
        now = datetime.now(UTC)
        state = ReconstructedState(
            reconstructed_at=now,
            repo_root=Path("/test/repo"),
            artifacts=[],
            files={},
            issues=[],
            recent_commits=[],
            audit_entry_count=0,
            git_available=True,
        )
        assert state.artifact_count == 0
        assert state.has_errors is False

    def test_has_errors(self) -> None:
        """should detect error-level issues."""
        now = datetime.now(UTC)
        state = ReconstructedState(
            reconstructed_at=now,
            repo_root=Path("/test/repo"),
            artifacts=[],
            files={},
            issues=[
                ReconstructionIssue(
                    source=ReconstructionSource.ARTIFACT,
                    severity="error",
                    message="Test error",
                )
            ],
            recent_commits=[],
            audit_entry_count=0,
            git_available=True,
        )
        assert state.has_errors is True
        assert state.has_warnings is False

    def test_has_warnings(self) -> None:
        """should detect warning-level issues."""
        now = datetime.now(UTC)
        state = ReconstructedState(
            reconstructed_at=now,
            repo_root=Path("/test/repo"),
            artifacts=[],
            files={},
            issues=[
                ReconstructionIssue(
                    source=ReconstructionSource.AUDIT_LOG,
                    severity="warning",
                    message="Test warning",
                )
            ],
            recent_commits=[],
            audit_entry_count=0,
            git_available=True,
        )
        assert state.has_warnings is True
        assert state.has_errors is False

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        artifact = ArtifactState(
            artifact_id="test-1",
            artifact_type="ProjectPlan",
            status="draft",
            created_at=now,
            updated_at=now,
            depends_on=[],
            target_files=[],
            execution_history=[],
            is_stale=True,
        )
        state = ReconstructedState(
            reconstructed_at=now,
            repo_root=Path("/test/repo"),
            artifacts=[artifact],
            files={"src/main.py": FileState(path="src/main.py", exists=True)},
            issues=[],
            recent_commits=[],
            audit_entry_count=10,
            git_available=True,
        )
        result = state.to_dict()
        assert result["artifact_count"] == 1
        assert result["stale_artifact_count"] == 1
        assert result["file_count"] == 1
        assert result["audit_entry_count"] == 10


class TestStateReconstructor:
    """Tests for StateReconstructor service."""

    def test_creation(self, tmp_path: Path) -> None:
        """StateReconstructor should be creatable."""
        reconstructor = StateReconstructor(repo_root=tmp_path)
        assert reconstructor.repo_root == tmp_path

    def test_reconstruct_empty_repo(self, tmp_path: Path) -> None:
        """should handle empty repository."""
        reconstructor = StateReconstructor(repo_root=tmp_path)
        state = reconstructor.reconstruct()
        assert state.artifact_count == 0
        assert state.audit_entry_count == 0

    def test_reconstruct_with_artifacts_dir(self, tmp_path: Path) -> None:
        """should load artifacts from filesystem."""
        # Create artifacts directory
        artifacts_dir = tmp_path / "artifacts" / "implementation_plans"
        artifacts_dir.mkdir(parents=True)

        # Create a test artifact
        artifact_data = {
            "id": str(uuid4()),
            "artifact_type": "ImplementationPlan",
            "status": "draft",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "depends_on": [],
            "payload": {"target": "src/main.py"},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact_data))

        reconstructor = StateReconstructor(repo_root=tmp_path)
        state = reconstructor.reconstruct()
        assert state.artifact_count == 1
        assert state.artifacts[0].artifact_type == "ImplementationPlan"

    def test_reconstruct_with_storage(self, tmp_path: Path) -> None:
        """should use storage port when available."""
        now = datetime.now(UTC)
        mock_artifact = MockArtifact(
            id=str(uuid4()),
            artifact_type=MockArtifactType("ProjectPlan"),
            status=MockStatus("approved"),
            created_at=now,
            updated_at=now,
            payload=MockPayload(target="src/main.py"),
        )
        storage = MockStorage(artifacts=[mock_artifact])

        reconstructor = StateReconstructor(repo_root=tmp_path, storage=storage)
        state = reconstructor.reconstruct()
        assert state.artifact_count == 1

    def test_reconstruct_with_storage_failure(self, tmp_path: Path) -> None:
        """should handle storage failures gracefully."""
        storage = MockStorage(should_fail=True)

        reconstructor = StateReconstructor(repo_root=tmp_path, storage=storage)
        state = reconstructor.reconstruct()
        assert state.has_errors is True
        assert any("Failed to load artifacts" in i.message for i in state.issues)

    def test_analyze_audit_log(self, tmp_path: Path) -> None:
        """should parse audit log entries."""
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()

        # Create audit log
        entries = [
            {
                "timestamp": datetime.now(UTC).isoformat() + "Z",
                "executor": "scaffold",
                "artifact": "artifacts/scaffold_plans/test.json",
                "status": "success",
                "mode": "apply",
                "files_affected": ["src/main.py"],
            },
            {
                "timestamp": datetime.now(UTC).isoformat() + "Z",
                "executor": "diff",
                "artifact": "artifacts/implementation_plans/impl.json",
                "status": "failure",
                "mode": "apply",
                "error": "Test error",
                "files_affected": [],
            },
        ]
        log_content = "\n".join(json.dumps(e) for e in entries)
        (audit_dir / "executions.log").write_text(log_content)

        reconstructor = StateReconstructor(repo_root=tmp_path)
        state = reconstructor.reconstruct()
        assert state.audit_entry_count == 2

    def test_analyze_audit_log_with_malformed_entries(self, tmp_path: Path) -> None:
        """should handle malformed audit log entries."""
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()

        # Create audit log with malformed entry
        log_content = "not valid json\n" + json.dumps({
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "executor": "scaffold",
            "artifact": "test.json",
            "status": "success",
            "mode": "apply",
            "files_affected": [],
        })
        (audit_dir / "executions.log").write_text(log_content)

        reconstructor = StateReconstructor(repo_root=tmp_path)
        state = reconstructor.reconstruct()
        assert state.audit_entry_count == 2  # Both lines counted
        assert state.has_warnings is True  # One warning for malformed entry

    def test_get_resumable_artifacts(self, tmp_path: Path) -> None:
        """should return only draft artifacts."""
        now = datetime.now(UTC)
        artifacts = [
            MockArtifact(
                id="1",
                artifact_type=MockArtifactType("ProjectPlan"),
                status=MockStatus("draft"),
                created_at=now,
                updated_at=now,
            ),
            MockArtifact(
                id="2",
                artifact_type=MockArtifactType("TestPlan"),
                status=MockStatus("approved"),
                created_at=now,
                updated_at=now,
            ),
        ]
        storage = MockStorage(artifacts=artifacts)

        reconstructor = StateReconstructor(repo_root=tmp_path, storage=storage)
        resumable = reconstructor.get_resumable_artifacts()
        assert len(resumable) == 1
        assert resumable[0].artifact_id == "1"

    def test_get_pending_executions(self, tmp_path: Path) -> None:
        """should return approved artifacts without successful execution."""
        now = datetime.now(UTC)
        artifacts = [
            MockArtifact(
                id="1",
                artifact_type=MockArtifactType("ImplementationPlan"),
                status=MockStatus("approved"),
                created_at=now,
                updated_at=now,
            ),
        ]
        storage = MockStorage(artifacts=artifacts)

        reconstructor = StateReconstructor(repo_root=tmp_path, storage=storage)
        pending = reconstructor.get_pending_executions()
        assert len(pending) == 1

    def test_get_failed_executions(self, tmp_path: Path) -> None:
        """should return artifacts with failed executions."""
        now = datetime.now(UTC)
        # Create artifact
        artifacts_dir = tmp_path / "artifacts" / "implementation_plans"
        artifacts_dir.mkdir(parents=True)
        artifact_id = str(uuid4())
        artifact_data = {
            "id": artifact_id,
            "artifact_type": "ImplementationPlan",
            "status": "approved",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "depends_on": [],
            "payload": {},
        }
        (artifacts_dir / f"{artifact_id}.json").write_text(json.dumps(artifact_data))

        # Create audit log with failure
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir()
        entry = {
            "timestamp": now.isoformat() + "Z",
            "executor": "diff",
            "artifact": f"artifacts/implementation_plans/{artifact_id}.json",
            "status": "failure",
            "mode": "apply",
            "error": "Test failure",
            "files_affected": [],
        }
        (audit_dir / "executions.log").write_text(json.dumps(entry))

        reconstructor = StateReconstructor(repo_root=tmp_path)
        failed = reconstructor.get_failed_executions()
        assert len(failed) == 1
        artifact, failure = failed[0]
        assert failure["error"] == "Test failure"

    def test_extract_target_files_from_dict(self, tmp_path: Path) -> None:
        """should extract target files from various payload formats."""
        reconstructor = StateReconstructor(repo_root=tmp_path)

        # Test with target field
        data = {"payload": {"target": "src/main.py"}}
        targets = reconstructor._extract_target_files_from_dict(data)
        assert "src/main.py" in targets

        # Test with files list
        data = {"payload": {"files": ["src/a.py", "src/b.py"]}}
        targets = reconstructor._extract_target_files_from_dict(data)
        assert "src/a.py" in targets
        assert "src/b.py" in targets

        # Test with from/to paths (refactor)
        data = {"payload": {"from_path": "old.py", "to_path": "new.py"}}
        targets = reconstructor._extract_target_files_from_dict(data)
        assert "old.py" in targets
        assert "new.py" in targets

    def test_is_source_file(self, tmp_path: Path) -> None:
        """should detect source file extensions."""
        reconstructor = StateReconstructor(repo_root=tmp_path)

        assert reconstructor._is_source_file("main.py") is True
        assert reconstructor._is_source_file("app.ts") is True
        assert reconstructor._is_source_file("Component.tsx") is True
        assert reconstructor._is_source_file("Main.java") is True
        assert reconstructor._is_source_file("README.md") is False
        assert reconstructor._is_source_file("config.json") is False

    def test_parse_timestamp(self, tmp_path: Path) -> None:
        """should parse various timestamp formats."""
        reconstructor = StateReconstructor(repo_root=tmp_path)

        # ISO format with Z
        ts = reconstructor._parse_timestamp("2026-01-10T12:00:00Z")
        assert ts.year == 2026
        assert ts.month == 1

        # ISO format with timezone
        ts = reconstructor._parse_timestamp("2026-01-10T12:00:00+00:00")
        assert ts.year == 2026

        # Empty string returns current time
        ts = reconstructor._parse_timestamp("")
        assert ts is not None

    def test_file_exists(self, tmp_path: Path) -> None:
        """should check file existence."""
        # Create a file
        (tmp_path / "existing.py").write_text("# content")

        reconstructor = StateReconstructor(repo_root=tmp_path)
        assert reconstructor._file_exists("existing.py") is True
        assert reconstructor._file_exists("nonexistent.py") is False


class TestReconstructionIssue:
    """Tests for ReconstructionIssue dataclass."""

    def test_creation(self) -> None:
        """ReconstructionIssue should be creatable."""
        issue = ReconstructionIssue(
            source=ReconstructionSource.ARTIFACT,
            severity="error",
            message="Test error",
            related_path="src/main.py",
            related_artifact_id="artifact-1",
        )
        assert issue.source == ReconstructionSource.ARTIFACT
        assert issue.severity == "error"

    def test_minimal_creation(self) -> None:
        """ReconstructionIssue should work with minimal args."""
        issue = ReconstructionIssue(
            source=ReconstructionSource.GIT_HISTORY,
            severity="warning",
            message="Test warning",
        )
        assert issue.related_path is None
        assert issue.related_artifact_id is None
