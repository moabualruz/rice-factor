# Milestone 08: CI/CD Integration - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)
> **Source Spec**: [item-03-ci-cd-pipeline-and-automation-strategy.md](../../raw/item-03-ci-cd-pipeline-and-automation-strategy.md)

---

## 1. Design Overview

The CI/CD Integration milestone implements a **guardian pipeline** that enforces Rice-Factor's invariants without participating in artifact generation. The pipeline validates that:

1. All artifacts are valid and approved
2. All code changes are backed by plans
3. Test immutability is preserved
4. Full audit trail exists

The design follows the canonical 5-stage pipeline from the specification, with each stage implemented as a separate validator that can run independently or as part of the full pipeline.

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI Pipeline                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────┐ │
│  │ Artifact │→ │ Approval │→ │Invariant │→ │  Test    │→ │Audit│ │
│  │Validation│  │Verificat.│  │Enforcement│ │Execution │  │Verif│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────┘ │
│       ↓             ↓             ↓             ↓           ↓    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    CI Result Aggregator                      │ │
│  │  - Collects stage results                                    │ │
│  │  - Produces final pass/fail                                  │ │
│  │  - Generates structured report                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │   CI Output     │
                    │  - Exit code    │
                    │  - JSON report  │
                    │  - Human output │
                    └─────────────────┘
```

### 2.2 Hexagonal File Organization

```
rice_factor/
├── domain/
│   ├── ci/
│   │   ├── __init__.py
│   │   ├── models.py              # CIResult, CIStageResult, CIFailure
│   │   ├── failure_codes.py       # CIFailureCode enum and taxonomy
│   │   └── pipeline.py            # CIPipeline orchestrator
│   └── ports/
│       └── ci_validator.py        # CIValidatorPort protocol
│
├── adapters/
│   └── ci/
│       ├── __init__.py
│       ├── artifact_validator.py   # Stage 1: Artifact validation
│       ├── approval_verifier.py    # Stage 2: Approval verification
│       ├── invariant_enforcer.py   # Stage 3: Invariant enforcement
│       ├── test_executor.py        # Stage 4: Test execution (delegates to M06)
│       └── audit_verifier.py       # Stage 5: Audit verification
│
├── entrypoints/
│   └── cli/
│       └── commands/
│           └── ci.py               # `rice-factor ci` command group
│
└── templates/
    └── ci/
        ├── github-actions.yml      # GitHub Actions template
        └── README.md               # Template usage guide
```

---

## 3. Domain Models

### 3.1 CI Failure Codes

```python
from enum import Enum

class CIFailureCode(str, Enum):
    """Canonical CI failure taxonomy."""

    # Stage 1: Artifact Validation
    DRAFT_ARTIFACT_PRESENT = "draft_artifact_present"
    LOCKED_ARTIFACT_MODIFIED = "locked_artifact_modified"
    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"

    # Stage 2: Approval Verification
    ARTIFACT_NOT_APPROVED = "artifact_not_approved"
    APPROVAL_METADATA_MISSING = "approval_metadata_missing"
    APPROVAL_ID_MISMATCH = "approval_id_mismatch"

    # Stage 3: Invariant Enforcement
    TEST_MODIFICATION_AFTER_LOCK = "test_modification_after_lock"
    UNPLANNED_CODE_CHANGE = "unplanned_code_change"
    ARCHITECTURE_VIOLATION = "architecture_violation"

    # Stage 4: Test Execution
    TEST_FAILURE = "test_failure"
    TEST_TIMEOUT = "test_timeout"

    # Stage 5: Audit Verification
    ORPHANED_CODE_CHANGE = "orphaned_code_change"
    AUDIT_INTEGRITY_VIOLATION = "audit_integrity_violation"
    MISSING_AUDIT_LOG = "missing_audit_log"
```

### 3.2 CI Result Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CIFailure:
    """A single CI failure with remediation guidance."""
    code: CIFailureCode
    message: str
    file_path: Optional[str] = None
    remediation: Optional[str] = None
    details: Optional[dict] = None

@dataclass
class CIStageResult:
    """Result of a single CI stage."""
    stage: str
    passed: bool
    failures: list[CIFailure]
    duration_ms: int

@dataclass
class CIResult:
    """Aggregate result of full CI pipeline."""
    passed: bool
    stages: list[CIStageResult]
    total_duration_ms: int
    timestamp: datetime

    def to_json(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "passed": self.passed,
            "stages": [
                {
                    "stage": s.stage,
                    "passed": s.passed,
                    "failures": [
                        {
                            "code": f.code.value,
                            "message": f.message,
                            "file_path": f.file_path,
                            "remediation": f.remediation,
                        }
                        for f in s.failures
                    ],
                    "duration_ms": s.duration_ms,
                }
                for s in self.stages
            ],
            "total_duration_ms": self.total_duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }
```

---

## 4. CI Validator Port

```python
from typing import Protocol
from pathlib import Path

class CIValidatorPort(Protocol):
    """Protocol for CI validation stages."""

    def validate(self, repo_root: Path) -> CIStageResult:
        """
        Run validation for this stage.

        Args:
            repo_root: Root directory of the repository

        Returns:
            CIStageResult with pass/fail and any failures
        """
        ...
```

---

## 5. Stage Implementations

### 5.1 Stage 1: Artifact Validation

```python
class ArtifactValidator:
    """Stage 1: Validate all artifacts in the repository."""

    def validate(self, repo_root: Path) -> CIStageResult:
        failures = []

        # Load all artifacts
        artifacts_dir = repo_root / "artifacts"
        for artifact_file in artifacts_dir.rglob("*.json"):
            if artifact_file.name.startswith("_"):
                continue  # Skip metadata files

            artifact = self._load_artifact(artifact_file)

            # Check 1: Schema validation
            if not self._validate_schema(artifact):
                failures.append(CIFailure(
                    code=CIFailureCode.SCHEMA_VALIDATION_FAILED,
                    message=f"Schema validation failed for {artifact_file}",
                    file_path=str(artifact_file),
                    remediation="Fix schema errors and re-save artifact",
                ))

            # Check 2: No drafts allowed
            if artifact.get("status") == "draft":
                failures.append(CIFailure(
                    code=CIFailureCode.DRAFT_ARTIFACT_PRESENT,
                    message=f"Draft artifact found: {artifact_file}",
                    file_path=str(artifact_file),
                    remediation="Run `rice-factor approve <artifact>` to approve",
                ))

            # Check 3: Locked artifacts unchanged
            if artifact.get("status") == "locked":
                if self._has_changed(artifact_file):
                    failures.append(CIFailure(
                        code=CIFailureCode.LOCKED_ARTIFACT_MODIFIED,
                        message=f"Locked artifact modified: {artifact_file}",
                        file_path=str(artifact_file),
                        remediation="Revert changes to locked artifact",
                    ))

        return CIStageResult(
            stage="artifact_validation",
            passed=len(failures) == 0,
            failures=failures,
            duration_ms=self._elapsed_ms(),
        )
```

### 5.2 Stage 2: Approval Verification

```python
class ApprovalVerifier:
    """Stage 2: Verify all artifacts are approved."""

    def validate(self, repo_root: Path) -> CIStageResult:
        failures = []

        # Load approvals metadata
        approvals_file = repo_root / "artifacts" / "_meta" / "approvals.json"
        if not approvals_file.exists():
            failures.append(CIFailure(
                code=CIFailureCode.APPROVAL_METADATA_MISSING,
                message="Approvals metadata file not found",
                file_path=str(approvals_file),
                remediation="Run `rice-factor init` to create metadata",
            ))
            return self._result(failures)

        approvals = json.loads(approvals_file.read_text())
        approved_ids = {a["artifact_id"] for a in approvals.get("approvals", [])}

        # Check each artifact has approval
        for artifact in self._load_all_artifacts(repo_root):
            artifact_id = artifact.get("id")
            if artifact_id not in approved_ids:
                failures.append(CIFailure(
                    code=CIFailureCode.ARTIFACT_NOT_APPROVED,
                    message=f"Artifact not approved: {artifact_id}",
                    file_path=artifact.get("_file_path"),
                    remediation=f"Run `rice-factor approve {artifact_id}`",
                ))

        return self._result(failures)
```

### 5.3 Stage 3: Invariant Enforcement

```python
class InvariantEnforcer:
    """Stage 3: Enforce system invariants."""

    def validate(self, repo_root: Path) -> CIStageResult:
        failures = []

        # Check 1: Test immutability
        failures.extend(self._check_test_immutability(repo_root))

        # Check 2: Artifact-to-code mapping
        failures.extend(self._check_code_mapping(repo_root))

        # Check 3: Architecture rules (optional)
        failures.extend(self._check_architecture(repo_root))

        return self._result(failures)

    def _check_test_immutability(self, repo_root: Path) -> list[CIFailure]:
        """Check that tests are not modified after TestPlan lock."""
        failures = []

        # Check if TestPlan is locked
        test_plan = self._find_locked_test_plan(repo_root)
        if not test_plan:
            return []  # No locked TestPlan, nothing to enforce

        # Get changed files from git
        changed_files = self._get_git_diff_files(repo_root)

        # Check for test file modifications
        for file_path in changed_files:
            if file_path.startswith("tests/"):
                failures.append(CIFailure(
                    code=CIFailureCode.TEST_MODIFICATION_AFTER_LOCK,
                    message=f"Test file modified after TestPlan lock: {file_path}",
                    file_path=file_path,
                    remediation="Unlock TestPlan, update tests, re-lock",
                ))

        return failures

    def _check_code_mapping(self, repo_root: Path) -> list[CIFailure]:
        """Check that all code changes are covered by plans."""
        failures = []

        # Get allowed files from plans
        allowed_files = set()
        for impl_plan in self._load_implementation_plans(repo_root):
            allowed_files.add(impl_plan.get("payload", {}).get("target"))
        for refactor_plan in self._load_refactor_plans(repo_root):
            for op in refactor_plan.get("payload", {}).get("operations", []):
                allowed_files.add(op.get("source"))
                allowed_files.add(op.get("target"))

        # Check changed files
        changed_files = self._get_git_diff_files(repo_root)
        for file_path in changed_files:
            if self._is_source_file(file_path) and file_path not in allowed_files:
                failures.append(CIFailure(
                    code=CIFailureCode.UNPLANNED_CODE_CHANGE,
                    message=f"Unplanned code change: {file_path}",
                    file_path=file_path,
                    remediation=f"Create ImplementationPlan for {file_path}",
                ))

        return failures
```

### 5.4 Stage 4: Test Execution

```python
class TestExecutor:
    """Stage 4: Execute test suite."""

    def __init__(self, test_runner: TestRunnerAdapter):
        self.test_runner = test_runner

    def validate(self, repo_root: Path) -> CIStageResult:
        failures = []

        # Delegate to existing test runner from M06
        result = self.test_runner.validate(
            target=str(repo_root),
            context={"mode": "ci"},
        )

        if result.status == "failed":
            for error in result.errors:
                failures.append(CIFailure(
                    code=CIFailureCode.TEST_FAILURE,
                    message=error,
                    remediation="Fix failing tests or update implementation",
                ))

        return self._result(failures)
```

### 5.5 Stage 5: Audit Verification

```python
class AuditVerifier:
    """Stage 5: Verify audit trail integrity."""

    def validate(self, repo_root: Path) -> CIStageResult:
        failures = []

        audit_dir = repo_root / "audit"
        diffs_dir = audit_dir / "diffs"

        # Load execution log
        exec_log = audit_dir / "executions.log"
        logged_operations = self._parse_execution_log(exec_log)

        # Check each commit has audit entry
        for commit in self._get_pr_commits(repo_root):
            if commit not in logged_operations:
                failures.append(CIFailure(
                    code=CIFailureCode.ORPHANED_CODE_CHANGE,
                    message=f"Commit has no audit entry: {commit}",
                    remediation="Apply changes via rice-factor workflow",
                ))

        # Verify diff hashes
        for diff_file in diffs_dir.glob("*.diff"):
            stored_hash = self._get_stored_hash(diff_file)
            actual_hash = self._compute_hash(diff_file)
            if stored_hash != actual_hash:
                failures.append(CIFailure(
                    code=CIFailureCode.AUDIT_INTEGRITY_VIOLATION,
                    message=f"Diff hash mismatch: {diff_file}",
                    file_path=str(diff_file),
                    remediation="Investigate potential tampering",
                ))

        return self._result(failures)
```

---

## 6. CI Pipeline Orchestrator

```python
class CIPipeline:
    """Orchestrates the full CI validation pipeline."""

    def __init__(
        self,
        artifact_validator: ArtifactValidator,
        approval_verifier: ApprovalVerifier,
        invariant_enforcer: InvariantEnforcer,
        test_executor: TestExecutor,
        audit_verifier: AuditVerifier,
    ):
        self.stages = [
            ("artifact_validation", artifact_validator),
            ("approval_verification", approval_verifier),
            ("invariant_enforcement", invariant_enforcer),
            ("test_execution", test_executor),
            ("audit_verification", audit_verifier),
        ]

    def run(self, repo_root: Path, stop_on_failure: bool = True) -> CIResult:
        """
        Run the full CI pipeline.

        Args:
            repo_root: Repository root directory
            stop_on_failure: If True, stop on first failing stage

        Returns:
            CIResult with aggregate results
        """
        start_time = datetime.now()
        stage_results = []
        overall_passed = True

        for stage_name, validator in self.stages:
            result = validator.validate(repo_root)
            stage_results.append(result)

            if not result.passed:
                overall_passed = False
                if stop_on_failure:
                    break

        return CIResult(
            passed=overall_passed,
            stages=stage_results,
            total_duration_ms=self._elapsed_ms(start_time),
            timestamp=datetime.now(),
        )
```

---

## 7. CLI Commands

### 7.1 Command Structure

```python
import typer
from rich.console import Console

ci_app = typer.Typer(name="ci", help="CI/CD validation commands")

@ci_app.command("validate")
def validate_all(
    repo_root: Path = typer.Option(Path.cwd(), help="Repository root"),
    json_output: bool = typer.Option(False, "--json", help="JSON output"),
    stop_on_failure: bool = typer.Option(True, help="Stop on first failure"),
):
    """Run full CI validation pipeline."""
    pipeline = create_ci_pipeline()
    result = pipeline.run(repo_root, stop_on_failure)

    if json_output:
        print(json.dumps(result.to_json(), indent=2))
    else:
        render_ci_result(result)

    raise typer.Exit(0 if result.passed else 1)

@ci_app.command("validate-artifacts")
def validate_artifacts(repo_root: Path = typer.Option(Path.cwd())):
    """Run artifact validation stage only."""
    validator = ArtifactValidator()
    result = validator.validate(repo_root)
    render_stage_result(result)
    raise typer.Exit(0 if result.passed else 1)

# Similar commands for each stage...
```

---

## 8. GitHub Actions Template

```yaml
# .github/workflows/rice-factor-ci.yml
name: Rice-Factor CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for diff detection

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Rice-Factor
        run: pip install rice-factor

      - name: Validate Artifacts
        run: rice-factor ci validate-artifacts

      - name: Verify Approvals
        run: rice-factor ci validate-approvals

      - name: Enforce Invariants
        run: rice-factor ci validate-invariants

      - name: Run Tests
        run: rice-factor test

      - name: Verify Audit Trail
        run: rice-factor ci validate-audit

      - name: Full Validation Report
        if: always()
        run: rice-factor ci validate --json > ci-report.json

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ci-report
          path: ci-report.json
```

---

## 9. Error Handling

### 9.1 Failure Remediation Mapping

```python
REMEDIATION_GUIDE = {
    CIFailureCode.DRAFT_ARTIFACT_PRESENT:
        "Run `rice-factor approve <artifact-id>` to approve the draft artifact",

    CIFailureCode.ARTIFACT_NOT_APPROVED:
        "Run `rice-factor approve <artifact-id>` to record approval",

    CIFailureCode.TEST_MODIFICATION_AFTER_LOCK:
        "1. Run `rice-factor unlock tests`\n"
        "2. Update tests as needed\n"
        "3. Run `rice-factor plan tests` to update TestPlan\n"
        "4. Run `rice-factor lock tests` to re-lock",

    CIFailureCode.UNPLANNED_CODE_CHANGE:
        "1. Run `rice-factor plan impl <file>` to create plan\n"
        "2. Run `rice-factor approve <plan-id>`\n"
        "3. Commit changes with audit trail",

    CIFailureCode.ORPHANED_CODE_CHANGE:
        "Apply changes through the rice-factor workflow:\n"
        "1. Create appropriate plan\n"
        "2. Generate diff with `rice-factor impl`\n"
        "3. Apply with `rice-factor apply`",
}
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Test each validator independently with mock repositories
- Test failure detection for each failure code
- Test CIResult serialization

### 10.2 Integration Tests

- Test full pipeline with sample repository
- Test GitHub Actions template in act (local runner)
- Test CI exit codes

### 10.3 Test Fixtures

```python
@pytest.fixture
def repo_with_draft_artifact(tmp_path):
    """Create repo with draft artifact for testing."""
    artifacts_dir = tmp_path / "artifacts" / "planning"
    artifacts_dir.mkdir(parents=True)
    (artifacts_dir / "project_plan.json").write_text(json.dumps({
        "id": "test-uuid",
        "status": "draft",
        "artifact_type": "ProjectPlan",
        "payload": {},
    }))
    return tmp_path
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial milestone design |
