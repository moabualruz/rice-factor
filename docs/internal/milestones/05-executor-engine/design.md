# Milestone 05: Executor Engine - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

The Executor Engine milestone implements the deterministic execution layer that applies approved artifacts to the codebase. Executors are mechanical tools with no intelligence.

**Key Design Goals:**
- Stateless, deterministic execution
- Fail-fast on any precondition violation
- Emit diffs rather than direct writes
- Log every action to audit trail
- Language-agnostic via capability registry

**Core Philosophy:**
- Executors are **NOT** agents
- Executors are **NOT** intelligent
- Executors are **dumb Unix tools**
- Think: `cp`, `mv`, `patch` - not AI assistants

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLI Layer (from M03)                            │
│  scaffold | impl <file> | apply | refactor dry-run                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────┐
│                         Domain Services                                  │
│                                │                                         │
│  ┌─────────────────────────────┴─────────────────────────────────────┐  │
│  │                      ExecutorService                              │  │
│  │  • Orchestrates execution pipeline                                │  │
│  │  • Validates artifacts before execution                           │  │
│  │  • Coordinates with audit logging                                 │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                       │
│  ┌─────────────────┐  ┌──────────┴────────────┐  ┌──────────────────┐  │
│  │CapabilityChecker│  │   ExecutorRegistry    │  │   AuditLogger    │  │
│  │ (lang support)  │  │  (executor lookup)    │  │ (execution log)  │  │
│  └─────────────────┘  └──────────┬────────────┘  └──────────────────┘  │
│                                  │                                       │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼───────────────────────────────────────┐
│                          Domain Ports                                    │
│                                  │                                       │
│  ┌───────────────────────────────┴───────────────────────────────────┐  │
│  │                        ExecutorPort                               │  │
│  │  Protocol:                                                        │  │
│  │    execute(artifact_path, repo_root, mode) -> ExecutionResult     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼───────────────────────────────────────┐
│                            Adapters                                      │
│                                  │                                       │
│  ┌──────────────────┐  ┌────────┴────────┐  ┌───────────────────────┐  │
│  │ ScaffoldExecutor │  │  DiffExecutor   │  │   RefactorExecutor    │  │
│  │ (create files)   │  │  (git apply)    │  │   (move/rename)       │  │
│  └──────────────────┘  └─────────────────┘  └───────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Hexagonal File Organization

```
rice_factor/
├── domain/
│   ├── ports/
│   │   └── executor.py                    # ExecutorPort protocol (NEW)
│   │
│   ├── artifacts/
│   │   └── execution_types.py             # ExecutionMode, ExecutionResult (NEW)
│   │
│   ├── services/
│   │   ├── scaffold_service.py            # Existing - will be wrapped
│   │   ├── refactor_executor.py           # Existing - will be wrapped
│   │   └── diff_service.py                # Existing - will be enhanced
│   │
│   └── failures/
│       └── executor_errors.py             # Executor error types (NEW)
│
├── adapters/
│   └── executors/
│       ├── __init__.py                    # Export executors (UPDATE)
│       ├── scaffold_executor.py           # ScaffoldExecutor adapter (NEW)
│       ├── diff_executor.py               # DiffExecutor adapter (NEW)
│       ├── refactor_executor.py           # RefactorExecutor adapter (NEW)
│       ├── capability_registry.py         # CapabilityRegistry (NEW)
│       └── audit_logger.py                # AuditLogger (NEW)
│
├── config/
│   └── capability_registry.yaml           # Default capability registry (NEW)
│
└── entrypoints/
    └── cli/
        └── commands/
            ├── scaffold.py                # Update to use executor (UPDATE)
            ├── impl.py                    # Update to use executor (UPDATE)
            ├── apply.py                   # Update to use executor (UPDATE)
            └── refactor.py                # Update to use executor (UPDATE)
```

---

## 3. ExecutorPort Protocol Design

### 3.1 ExecutorPort Protocol

```python
from typing import Protocol
from pathlib import Path
from rice_factor.domain.artifacts.execution_types import (
    ExecutionMode, ExecutionResult
)

class ExecutorPort(Protocol):
    """Abstract interface for all executors.

    All executors must implement this protocol. Executors are:
    - Stateless
    - Deterministic
    - Fail-fast
    - Auditable
    """

    def execute(
        self,
        artifact_path: Path,
        repo_root: Path,
        mode: ExecutionMode
    ) -> ExecutionResult:
        """
        Execute the operation defined by the artifact.

        Args:
            artifact_path: Path to the artifact JSON file
            repo_root: Root directory of the target repository
            mode: DRY_RUN (preview) or APPLY (execute)

        Returns:
            ExecutionResult with status, diffs, errors, logs

        Raises:
            ExecutorPreconditionError: Preconditions not met
            ExecutorCapabilityError: Operation not supported
            ExecutorArtifactError: Invalid artifact
        """
        ...
```

### 3.2 Execution Types

```python
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

class ExecutionMode(Enum):
    """Mode of execution."""
    DRY_RUN = "dry_run"   # Generate diff, don't apply
    APPLY = "apply"        # Generate diff and apply

@dataclass
class ExecutionResult:
    """Result from an executor."""
    status: Literal["success", "failure"]
    diffs: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.status == "success"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "status": self.status,
            "diffs": [str(p) for p in self.diffs],
            "errors": self.errors,
            "logs": self.logs,
        }
```

---

## 4. Executor Types

### 4.1 Scaffold Executor

**Purpose:** Create empty files and directories from ScaffoldPlan.

**Input:** ScaffoldPlan artifact (approved)

**Preconditions:**
- Artifact is approved
- Files do not already exist
- Paths are within repo root
- No content beyond headers/comments

**Pseudocode:**
```pseudo
function execute_scaffold(artifact_path, repo_root, mode):
    artifact = load_artifact(artifact_path)

    if artifact.status != APPROVED:
        fail("artifact_not_approved")

    for file in artifact.payload.files:
        abs_path = repo_root / file.path

        if path_escapes_repo(abs_path, repo_root):
            fail("path_escapes_repo")

        if exists(abs_path):
            log("skipped: " + file.path)
            continue

        if mode == DRY_RUN:
            record_diff("create " + file.path)
            continue

        create_directories(parent(abs_path))
        content = generate_header_comment(file.description, file.kind)
        write_file(abs_path, content)
        record_log("created " + file.path)

    emit_audit_log()
    return success
```

### 4.2 Diff Executor

**Purpose:** Apply approved diffs using git apply.

**Input:** Approved diff file

**Preconditions:**
- Diff is approved
- Diff touches only declared files
- Tests are not modified if locked
- No binary files

**Key Rule:** Diff executor **never generates diffs** - only applies them.

**Pseudocode:**
```pseudo
function execute_diff(diff_path, repo_root, mode):
    diff = load_diff(diff_path)

    if diff.status != APPROVED:
        fail("diff_not_approved")

    for file in diff.touched_files:
        if file not in allowed_files:
            fail("unauthorized_file_modification")

        if is_test_file(file) and tests_locked():
            fail("test_modification_forbidden")

    if mode == DRY_RUN:
        return diff  # Preview only

    result = git_apply(diff, repo_root)

    if not result.success:
        fail("patch_failed: " + result.error)

    emit_audit_log()
    return success
```

### 4.3 Refactor Executor

**Purpose:** Perform mechanical refactors (move_file, rename_symbol).

**Input:** RefactorPlan artifact (approved)

**Supported Operations (MVP):**
- `move_file` - Move/rename a file
- `rename_symbol` - Simple textual rename

**Pseudocode:**
```pseudo
function execute_refactor(artifact_path, repo_root, mode):
    artifact = load_artifact(artifact_path)
    language = detect_language(repo_root)

    for op in artifact.payload.operations:
        if not check_capability(op.type, language):
            fail("operation_not_supported: " + op.type)

        if op.type == "move_file":
            plan_move(op, repo_root)

        if op.type == "rename_symbol":
            plan_rename(op, repo_root)

    diff = generate_diff_from_plans()

    if mode == DRY_RUN:
        return diff

    apply_diff(diff, repo_root)
    emit_audit_log()
    return success
```

---

## 5. Shared Executor Pipeline

Every executor follows this exact 9-step pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTOR PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Load Artifact                                               │
│     └── read_json(artifact_path)                                │
│                                                                 │
│  2. Validate Schema                                             │
│     └── validate_against_schema(artifact)                       │
│     └── FAIL if invalid                                         │
│                                                                 │
│  3. Verify Approval & Lock Status                               │
│     └── check artifact.status == APPROVED                       │
│     └── check approvals.json contains artifact_id               │
│     └── FAIL if not approved                                    │
│                                                                 │
│  4. Capability Check                                            │
│     └── for each operation: check_capability(op, language)      │
│     └── FAIL if unsupported                                     │
│                                                                 │
│  5. Precondition Checks                                         │
│     └── executor-specific checks (file exists, etc.)            │
│     └── FAIL if preconditions not met                           │
│                                                                 │
│  6. Generate Diff                                               │
│     └── compute changes without applying                        │
│     └── save to audit/diffs/<id>.diff                           │
│                                                                 │
│  7. Apply Diff (if APPLY mode)                                  │
│     └── git apply <diff>                                        │
│     └── FAIL if patch fails                                     │
│                                                                 │
│  8. Emit Audit Logs                                             │
│     └── append to audit/executions.log                          │
│                                                                 │
│  9. Return Result                                               │
│     └── ExecutionResult(status, diffs, errors, logs)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Capability Registry Design

### 6.1 Schema Definition

```yaml
# capability_registry.yaml
languages:
  python:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: false
  rust:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: partial
  go:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: false
  javascript:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: false
  typescript:
    operations:
      move_file: true
      rename_symbol: true
      extract_interface: false
      enforce_dependency: false
```

### 6.2 Loading Strategy

```python
class CapabilityRegistry:
    """Registry for language operation capabilities."""

    def __init__(self, project_root: Path | None = None):
        self._registry = self._load_registry(project_root)

    def _load_registry(self, project_root: Path | None) -> dict:
        """Load registry with project override."""
        # 1. Load bundled default
        bundled = self._load_bundled_registry()

        # 2. Check for project override
        if project_root:
            project_registry = project_root / "tools" / "registry" / "capability_registry.yaml"
            if project_registry.exists():
                override = yaml.safe_load(project_registry.read_text())
                return self._merge_registries(bundled, override)

        return bundled

    def check_capability(self, operation: str, language: str) -> bool:
        """Check if operation is supported for language."""
        lang_config = self._registry.get("languages", {}).get(language, {})
        operations = lang_config.get("operations", {})
        return operations.get(operation, False) == True
```

### 6.3 Capability Checker Integration

```python
def check_all_capabilities(
    operations: list[RefactorOperation],
    language: str,
    registry: CapabilityRegistry
) -> list[str]:
    """Check all operations and return unsupported ones."""
    unsupported = []
    for op in operations:
        if not registry.check_capability(op.type.value, language):
            unsupported.append(f"{op.type.value} not supported for {language}")
    return unsupported
```

---

## 7. Audit Logging Design

### 7.1 Log Format

```json
{
  "timestamp": "2026-01-10T12:34:56.789Z",
  "executor": "scaffold_executor",
  "artifact": "artifacts/planning/scaffold_plan.json",
  "status": "success",
  "mode": "apply",
  "diff": "audit/diffs/20260110_123456_scaffold.diff",
  "files_affected": ["src/domain/user.py", "src/api/endpoints.py"],
  "duration_ms": 150
}
```

### 7.2 Log Location

- Primary log: `audit/executions.log`
- Diffs: `audit/diffs/<timestamp>_<executor>.diff`

### 7.3 Audit Trail Guarantees

- **Append-only**: Logs are never modified or deleted
- **Atomic writes**: Each log entry is complete
- **Timestamped**: ISO-8601 with milliseconds
- **Traceable**: Links to source artifact and generated diff

---

## 8. Error Handling Strategy

### 8.1 Error Taxonomy

```
ExecutorError (base)
├── ExecutorPreconditionError     # Preconditions not met
│   ├── ArtifactNotApprovedError  # Artifact not approved
│   ├── FileAlreadyExistsError    # File already exists
│   ├── FileNotFoundError         # Source file missing
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
```

### 8.2 Failure Modes per Executor

| Executor | Failure Mode | Error Type |
|----------|--------------|------------|
| Scaffold | File exists | FileAlreadyExistsError |
| Scaffold | Path escapes repo | PathEscapesRepoError |
| Diff | Not approved | ArtifactNotApprovedError |
| Diff | Tests locked | TestsLockedError |
| Diff | Patch fails | GitApplyError |
| Refactor | Source missing | FileNotFoundError |
| Refactor | Dest exists | FileAlreadyExistsError |
| Refactor | Unsupported op | UnsupportedOperationError |

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# Test ExecutorPort protocol compliance
def test_executor_implements_protocol():
    assert isinstance(ScaffoldExecutor(...), ExecutorPort)

# Test DRY_RUN mode
def test_scaffold_dry_run_does_not_create_files(tmp_path):
    executor = ScaffoldExecutor()
    result = executor.execute(artifact, tmp_path, ExecutionMode.DRY_RUN)
    assert result.success
    assert not (tmp_path / "src/user.py").exists()

# Test APPLY mode
def test_scaffold_apply_creates_files(tmp_path):
    executor = ScaffoldExecutor()
    result = executor.execute(artifact, tmp_path, ExecutionMode.APPLY)
    assert result.success
    assert (tmp_path / "src/user.py").exists()

# Test precondition failures
def test_scaffold_rejects_unapproved_artifact():
    artifact = create_draft_artifact()
    with pytest.raises(ArtifactNotApprovedError):
        executor.execute(artifact, repo_root, ExecutionMode.APPLY)
```

### 9.2 Integration Tests

```python
# Test full pipeline with real git
def test_diff_executor_applies_patch(git_repo):
    diff_path = create_test_diff(git_repo)
    executor = DiffExecutor()
    result = executor.execute(diff_path, git_repo, ExecutionMode.APPLY)
    assert result.success
    assert "expected content" in (git_repo / "src/file.py").read_text()

# Test audit log creation
def test_execution_creates_audit_log(tmp_path):
    executor = ScaffoldExecutor()
    executor.execute(artifact, tmp_path, ExecutionMode.APPLY)
    audit_log = tmp_path / "audit" / "executions.log"
    assert audit_log.exists()
    log_entry = json.loads(audit_log.read_text().strip())
    assert log_entry["executor"] == "scaffold_executor"
```

---

## 10. CLI Integration

### 10.1 Existing Commands to Wire

| Command | Executor | Mode |
|---------|----------|------|
| `rice-factor scaffold` | ScaffoldExecutor | APPLY |
| `rice-factor scaffold --dry-run` | ScaffoldExecutor | DRY_RUN |
| `rice-factor apply` | DiffExecutor | APPLY |
| `rice-factor apply --dry-run` | DiffExecutor | DRY_RUN |
| `rice-factor refactor dry-run` | RefactorExecutor | DRY_RUN |
| `rice-factor refactor apply` | RefactorExecutor | APPLY |

### 10.2 Command Flow

```
rice-factor scaffold
     │
     ▼
Load ScaffoldPlan artifact (approved)
     │
     ▼
ScaffoldExecutor.execute(artifact, repo_root, APPLY)
     │
     ├── Validate artifact
     ├── Check preconditions
     ├── Generate diff
     ├── Create files
     ├── Emit audit log
     └── Return result
     │
     ▼
Display result to user
```

---

## 11. Implementation Order

1. **F05-01**: Executor Base Interface (foundation)
   - ExecutorPort protocol
   - ExecutionMode, ExecutionResult types
   - Executor error types

2. **F05-05**: Capability Registry (needed by executors)
   - Default registry YAML
   - CapabilityRegistry class
   - check_capability function

3. **F05-06**: Audit Logging (needed by all executors)
   - AuditLogger class
   - JSON log format
   - Integration hooks

4. **F05-02**: Scaffold Executor (simplest executor)
   - Wrap existing ScaffoldService
   - Implement 9-step pipeline
   - Unit tests

5. **F05-03**: Diff Executor (git integration)
   - git apply integration
   - Precondition checks
   - Unit tests

6. **F05-04**: Refactor Executor (most complex)
   - move_file implementation
   - rename_symbol implementation
   - Capability integration
   - Unit tests

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial design document |
