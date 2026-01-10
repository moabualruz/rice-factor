"""Tests for RefactorExecutorAdapter."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rice_factor.adapters.executors.audit_logger import AuditLogger
from rice_factor.adapters.executors.capability_registry import CapabilityRegistry
from rice_factor.adapters.executors.refactor_executor_adapter import (
    RefactorExecutorAdapter,
)
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.artifacts.execution_types import ExecutionMode
from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorOperation,
    RefactorOperationType,
    RefactorPlanPayload,
)
from rice_factor.domain.ports.executor import ExecutorPort


def create_refactor_artifact(
    status: ArtifactStatus = ArtifactStatus.APPROVED,
    operations: list[RefactorOperation] | None = None,
) -> ArtifactEnvelope[RefactorPlanPayload]:
    """Create a RefactorPlan artifact for testing."""
    if operations is None:
        operations = [
            RefactorOperation.model_validate({
                "type": RefactorOperationType.MOVE_FILE,
                "from": "src/old.py",
                "to": "src/new.py",
            }),
        ]

    payload = RefactorPlanPayload(
        goal="Refactor for testing",
        operations=operations,
    )

    return ArtifactEnvelope[RefactorPlanPayload](
        artifact_type=ArtifactType.REFACTOR_PLAN,
        status=status,
        payload=payload,
    )


@pytest.fixture
def capability_registry() -> CapabilityRegistry:
    """Create a capability registry with default bundled config."""
    # Use bundled default config - it has python, rust, etc. with move_file and rename_symbol support
    return CapabilityRegistry()


class TestRefactorExecutorAdapterProtocol:
    """Tests for RefactorExecutorAdapter protocol compliance."""

    def test_implements_executor_port(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """RefactorExecutorAdapter should implement ExecutorPort protocol."""
        storage = MagicMock()
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )
        assert isinstance(executor, ExecutorPort)

    def test_has_execute_method(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """RefactorExecutorAdapter should have execute method."""
        storage = MagicMock()
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )
        assert hasattr(executor, "execute")


class TestRefactorExecutorAdapterDryRun:
    """Tests for DRY_RUN mode."""

    def test_dry_run_generates_diff_without_moving_files(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """DRY_RUN mode should generate diff but not move files."""
        storage = MagicMock()

        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        source_file = src_dir / "old.py"
        source_file.write_text("# Old file content")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.DRY_RUN,
        )

        assert result.success
        # Source file should still exist
        assert source_file.exists()
        # Destination file should NOT exist
        assert not (src_dir / "new.py").exists()

    def test_dry_run_logs_would_apply(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """DRY_RUN mode should log what would be applied."""
        storage = MagicMock()

        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "old.py").write_text("# content")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.DRY_RUN,
        )

        assert any("Would apply" in log for log in result.logs)


class TestRefactorExecutorAdapterApply:
    """Tests for APPLY mode."""

    def test_apply_moves_file(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """APPLY mode should move the file."""
        storage = MagicMock()

        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        source_file = src_dir / "old.py"
        source_file.write_text("# Old file content")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.success
        # Source file should NOT exist anymore
        assert not source_file.exists()
        # Destination file should exist
        assert (src_dir / "new.py").exists()
        assert (src_dir / "new.py").read_text() == "# Old file content"

    def test_apply_renames_symbol(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """APPLY mode should rename symbols in file."""
        storage = MagicMock()

        # Create source file with symbol
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        source_file = src_dir / "module.py"
        source_file.write_text("def old_function():\n    return old_function()")

        operations = [
            RefactorOperation.model_validate({
                "type": RefactorOperationType.RENAME_SYMBOL,
                "from": "src/module.py",
                "to": "new_function",  # to is new symbol name
                "symbol": "old_function",
            }),
        ]
        artifact = create_refactor_artifact(operations=operations)
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.success
        content = source_file.read_text()
        assert "new_function" in content
        assert "old_function" not in content

    def test_apply_logs_applied_operations(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """APPLY mode should log applied operations."""
        storage = MagicMock()

        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "old.py").write_text("# content")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert any("Applied" in log for log in result.logs)


class TestRefactorExecutorAdapterArtifactValidation:
    """Tests for artifact validation."""

    def test_rejects_unapproved_artifact(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should reject artifacts that are not approved."""
        storage = MagicMock()
        artifact = create_refactor_artifact(status=ArtifactStatus.DRAFT)
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any("not approved" in error.lower() for error in result.errors)

    def test_rejects_wrong_artifact_type(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should reject artifacts that are not RefactorPlan."""
        storage = MagicMock()
        # Create a different artifact type
        wrong_artifact = MagicMock()
        wrong_artifact.artifact_type = ArtifactType.PROJECT_PLAN
        wrong_artifact.status = ArtifactStatus.APPROVED
        storage.load.return_value = wrong_artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any(
            "refactorplan" in error.lower() or "type" in error.lower()
            for error in result.errors
        )


class TestRefactorExecutorAdapterCapabilityCheck:
    """Tests for capability registry integration."""

    def test_rejects_unsupported_operation(
        self, tmp_path: Path
    ) -> None:
        """Should reject operations not supported for the language."""
        # Create a mock registry that returns False for move_file
        capability_registry = MagicMock()
        capability_registry.check_capability.return_value = False

        storage = MagicMock()

        # Create pyproject.toml to detect python
        (tmp_path / "pyproject.toml").write_text("[project]")

        artifact = create_refactor_artifact()  # move_file operation
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any(
            "not supported" in error.lower() or "unsupported" in error.lower()
            for error in result.errors
        )


class TestRefactorExecutorAdapterPreconditions:
    """Tests for precondition checks."""

    def test_rejects_missing_source_file(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should reject if source file doesn't exist."""
        storage = MagicMock()
        # Create pyproject.toml to detect python (needed for capability check)
        (tmp_path / "pyproject.toml").write_text("[project]")
        # Don't create the source file
        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any(
            "not found" in error.lower() or "source file" in error.lower()
            for error in result.errors
        )

    def test_rejects_existing_destination(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should reject if destination file already exists."""
        storage = MagicMock()

        # Create both source and destination files
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "old.py").write_text("# source")
        (src_dir / "new.py").write_text("# dest exists")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert result.failure
        assert any(
            "already exists" in error.lower() or "exists" in error.lower()
            for error in result.errors
        )


class TestRefactorExecutorAdapterLanguageDetection:
    """Tests for language detection."""

    def test_detects_python_from_pyproject(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should detect Python from pyproject.toml."""
        storage = MagicMock()
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        # Create pyproject.toml
        (tmp_path / "pyproject.toml").write_text("[project]")

        language = executor._detect_language(tmp_path)
        assert language == "python"

    def test_detects_rust_from_cargo(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should detect Rust from Cargo.toml."""
        storage = MagicMock()
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        # Create Cargo.toml
        (tmp_path / "Cargo.toml").write_text("[package]")

        language = executor._detect_language(tmp_path)
        assert language == "rust"

    def test_detects_go_from_go_mod(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should detect Go from go.mod."""
        storage = MagicMock()
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        # Create go.mod
        (tmp_path / "go.mod").write_text("module example")

        language = executor._detect_language(tmp_path)
        assert language == "go"

    def test_fallback_to_file_extension(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should fallback to file extension analysis."""
        storage = MagicMock()
        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        # Create .py files without pyproject.toml
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("# python")
        (src_dir / "utils.py").write_text("# python")

        language = executor._detect_language(tmp_path)
        assert language == "python"


class TestRefactorExecutorAdapterDiffGeneration:
    """Tests for diff generation."""

    def test_generates_diff_file(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should generate a diff file."""
        storage = MagicMock()

        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "old.py").write_text("# content")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.DRY_RUN,
        )

        assert result.success
        assert len(result.diffs) >= 1
        # Check diff file exists
        diff_path = result.diffs[0]
        assert diff_path.exists()


class TestRefactorExecutorAdapterAuditLogging:
    """Tests for audit logging."""

    def test_generates_audit_log_entry_on_success(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should create audit log entry on success."""
        storage = MagicMock()

        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "old.py").write_text("# content")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
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
        assert entries[-1].executor == "refactor"
        assert entries[-1].is_success

    def test_generates_audit_log_entry_on_failure(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Should create audit log entry on failure."""
        storage = MagicMock()
        artifact = create_refactor_artifact(status=ArtifactStatus.DRAFT)
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        entries = audit_logger.read_all_entries()
        assert len(entries) >= 1
        assert entries[-1].is_failure


class TestRefactorExecutorAdapterResult:
    """Tests for ExecutionResult."""

    def test_result_contains_diffs_list(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Result should contain list of diff paths."""
        storage = MagicMock()

        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "old.py").write_text("# content")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert isinstance(result.diffs, list)

    def test_result_contains_logs(
        self, tmp_path: Path, capability_registry: CapabilityRegistry
    ) -> None:
        """Result should contain execution logs."""
        storage = MagicMock()

        # Create source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "old.py").write_text("# content")

        artifact = create_refactor_artifact()
        storage.load.return_value = artifact

        audit_logger = AuditLogger(project_root=tmp_path)
        executor = RefactorExecutorAdapter(
            storage=storage,
            capability_registry=capability_registry,
            audit_logger=audit_logger,
        )

        result = executor.execute(
            artifact_path=tmp_path / "artifact.json",
            repo_root=tmp_path,
            mode=ExecutionMode.APPLY,
        )

        assert isinstance(result.logs, list)
        assert len(result.logs) > 0
