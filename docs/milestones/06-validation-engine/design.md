# Milestone 06: Validation Engine - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

The Validation Engine milestone implements the verification layer that ensures correctness through tests, linting, architecture rules, and invariant checks. Validators are emit-only tools that produce ValidationResult artifacts.

**Key Design Goals:**
- Native tool integration (cargo, go, mvn, pytest, ruff, etc.)
- Emit-only model (no side effects, no auto-fixing)
- Fail-fast on validation failure
- Deterministic and reproducible
- Auditable validation history

**Core Philosophy:**
- Validators are **NOT** fixers
- Validators **emit**, never **mutate**
- Validators use **native tools**, not custom implementations
- Think: `cargo test`, `pytest`, `ruff check` - not AI-powered analyzers

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLI Layer (from M03)                            │
│  rice-factor test | rice-factor lint | rice-factor validate            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────┐
│                         Domain Services                                  │
│                                    │                                     │
│  ┌─────────────────────────────────┴─────────────────────────────────┐  │
│  │                    ValidationService                              │  │
│  │  • Orchestrates validation pipeline                               │  │
│  │  • Aggregates results from validators                             │  │
│  │  • Generates ValidationResult artifacts                           │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                       │
│  ┌─────────────────┐  ┌──────────┴────────────┐  ┌──────────────────┐  │
│  │LanguageDetector │  │  ValidatorRegistry    │  │ValidationAuditLog│  │
│  │ (from M05)      │  │  (validator lookup)   │  │ (validation log) │  │
│  └─────────────────┘  └──────────┬────────────┘  └──────────────────┘  │
│                                  │                                       │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼───────────────────────────────────────┐
│                          Domain Ports                                    │
│                                  │                                       │
│  ┌───────────────────────────────┴───────────────────────────────────┐  │
│  │                        ValidatorPort                              │  │
│  │  Protocol:                                                        │  │
│  │    validate(target, context) -> ValidationResult                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────┬───────────────────────────────────────┘
                                   │
┌──────────────────────────────────┼───────────────────────────────────────┐
│                            Adapters                                      │
│                                  │                                       │
│  ┌──────────────────┐  ┌────────┴────────┐  ┌───────────────────────┐  │
│  │ TestRunnerAdapter│  │LintRunnerAdapter│  │ArchitectureValidator │  │
│  │ (cargo, pytest)  │  │ (ruff, clippy)  │  │   (import checks)     │  │
│  └──────────────────┘  └─────────────────┘  └───────────────────────┘  │
│                                                                          │
│  ┌──────────────────┐  ┌─────────────────────────────────────────────┐  │
│  │InvariantChecker  │  │        ValidationResultGenerator           │  │
│  │ (domain rules)   │  │        (aggregate & emit)                  │  │
│  └──────────────────┘  └─────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Hexagonal File Organization

```
rice_factor/
├── domain/
│   ├── ports/
│   │   └── validator.py                    # ValidatorPort protocol (NEW)
│   │
│   ├── artifacts/
│   │   └── validation_types.py             # ValidationResult types (NEW)
│   │
│   ├── services/
│   │   └── validation_service.py           # ValidationService (NEW)
│   │
│   └── failures/
│       └── validation_errors.py            # Validation error types (NEW)
│
├── adapters/
│   └── validators/
│       ├── __init__.py                     # Export validators (NEW)
│       ├── test_runner_adapter.py          # TestRunnerAdapter (NEW)
│       ├── lint_runner_adapter.py          # LintRunnerAdapter (NEW)
│       ├── architecture_validator.py       # ArchitectureValidator (NEW)
│       ├── invariant_checker.py            # InvariantChecker (NEW)
│       └── validation_result_generator.py  # ValidationResultGenerator (NEW)
│
├── config/
│   └── validator_registry.yaml             # Default validator config (NEW)
│
└── entrypoints/
    └── cli/
        └── commands/
            └── test.py                     # Update to use validators (UPDATE)
```

---

## 3. ValidatorPort Protocol Design

### 3.1 ValidatorPort Protocol

```python
from typing import Protocol
from pathlib import Path
from rice_factor.domain.artifacts.validation_types import (
    ValidationContext, ValidationResult
)

class ValidatorPort(Protocol):
    """Abstract interface for all validators.

    All validators must implement this protocol. Validators are:
    - Emit-only (produce results, no side effects)
    - Deterministic
    - Fail-fast
    - Auditable
    """

    @property
    def name(self) -> str:
        """Unique name for this validator."""
        ...

    def validate(
        self,
        target: Path,
        context: ValidationContext
    ) -> ValidationResult:
        """
        Validate the target.

        Args:
            target: Path to validate (file, directory, or artifact)
            context: Validation context (language, config, etc.)

        Returns:
            ValidationResult with status and any errors

        Note:
            Validators NEVER raise exceptions for validation failures.
            They return ValidationResult(status="failed", errors=[...])
        """
        ...
```

### 3.2 Validation Types

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

@dataclass
class ValidationContext:
    """Context for validation."""
    repo_root: Path
    language: str
    config: dict = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Result from a validator."""
    target: str
    status: Literal["passed", "failed"]
    errors: list[str] = field(default_factory=list)
    validator: str = ""
    duration_ms: int = 0

    @property
    def passed(self) -> bool:
        """Check if validation passed."""
        return self.status == "passed"

    def to_dict(self) -> dict:
        """Serialize to dictionary (for artifact storage)."""
        return {
            "target": self.target,
            "status": self.status,
            "errors": self.errors,
        }

    def to_payload(self) -> dict:
        """Serialize to artifact payload format."""
        result = {
            "target": self.target,
            "status": self.status,
        }
        if self.errors:
            result["errors"] = self.errors
        return result
```

---

## 4. Validator Types

### 4.1 Test Runner Adapter

**Purpose:** Run native test commands and capture results.

**Input:** Repository root, language

**Output:** ValidationResult with test status

**Language Commands:**
| Language | Command | Exit Code |
|----------|---------|-----------|
| Python | `pytest` | 0 = pass |
| Rust | `cargo test` | 0 = pass |
| Go | `go test ./...` | 0 = pass |
| JavaScript | `npm test` | 0 = pass |
| TypeScript | `npm test` | 0 = pass |
| Java | `mvn test` | 0 = pass |

**Pseudocode:**
```pseudo
function run_tests(repo_root, language):
    command = get_test_command(language)

    if command is None:
        return ValidationResult(
            target=str(repo_root),
            status="failed",
            errors=["No test command for language: " + language]
        )

    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        timeout=config.test_timeout
    )

    if result.returncode == 0:
        return ValidationResult(
            target=str(repo_root),
            status="passed"
        )
    else:
        return ValidationResult(
            target=str(repo_root),
            status="failed",
            errors=parse_test_output(result.stderr, result.stdout)
        )
```

### 4.2 Lint Runner Adapter

**Purpose:** Run native lint commands and capture results.

**Input:** Repository root, language

**Output:** ValidationResult with lint status

**Language Commands:**
| Language | Command | Exit Code |
|----------|---------|-----------|
| Python | `ruff check .` | 0 = pass |
| Rust | `cargo clippy` | 0 = pass |
| Go | `golint ./...` | 0 = pass |
| JavaScript | `eslint .` | 0 = pass |
| TypeScript | `eslint .` | 0 = pass |

**Pseudocode:**
```pseudo
function run_lint(repo_root, language):
    command = get_lint_command(language)

    if command is None:
        return ValidationResult(
            target=str(repo_root),
            status="passed",  # No linter = pass (optional check)
            errors=[]
        )

    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True
    )

    if result.returncode == 0:
        return ValidationResult(
            target=str(repo_root),
            status="passed"
        )
    else:
        return ValidationResult(
            target=str(repo_root),
            status="failed",
            errors=parse_lint_output(result.stdout, language)
        )
```

### 4.3 Architecture Validator

**Purpose:** Validate hexagonal layer import rules.

**Input:** Source directory

**Output:** ValidationResult with import violations

**Layer Rules:**
- `domain/` cannot import from `adapters/`
- `domain/` cannot import from `entrypoints/`
- `domain/` can only use stdlib

**Pseudocode:**
```pseudo
function validate_architecture(repo_root):
    violations = []

    domain_files = glob(repo_root / "rice_factor/domain/**/*.py")

    for file in domain_files:
        imports = extract_imports(file)

        for imp in imports:
            if imp.startswith("rice_factor.adapters"):
                violations.append(
                    f"{file}: domain imports from adapters: {imp}"
                )
            if imp.startswith("rice_factor.entrypoints"):
                violations.append(
                    f"{file}: domain imports from entrypoints: {imp}"
                )

    if violations:
        return ValidationResult(
            target="architecture",
            status="failed",
            errors=violations
        )
    else:
        return ValidationResult(
            target="architecture",
            status="passed"
        )
```

### 4.4 Invariant Checker

**Purpose:** Verify domain invariants.

**Input:** Artifacts directory, approvals file

**Output:** ValidationResult with invariant violations

**Invariants Checked:**
1. TestPlan lock status
2. Artifact status transitions
3. Approval chain integrity
4. Dependency existence

**Pseudocode:**
```pseudo
function check_invariants(artifacts_dir):
    violations = []

    # Check TestPlan lock
    test_plan = load_artifact(artifacts_dir / "planning/test_plan.json")
    if test_plan and test_plan.status != "locked":
        violations.append("TestPlan must be locked before implementation")

    # Check artifact status transitions
    for artifact in load_all_artifacts(artifacts_dir):
        if not is_valid_status_transition(artifact):
            violations.append(f"Invalid status for {artifact.id}")

    # Check approval chain
    approvals = load_approvals(artifacts_dir / "_meta/approvals.json")
    for artifact in load_approved_artifacts(artifacts_dir):
        if artifact.id not in approvals:
            violations.append(f"Missing approval for {artifact.id}")

    # Check dependencies exist
    for artifact in load_all_artifacts(artifacts_dir):
        for dep_id in artifact.depends_on:
            if not artifact_exists(artifacts_dir, dep_id):
                violations.append(f"Missing dependency {dep_id} for {artifact.id}")

    if violations:
        return ValidationResult(
            target="invariants",
            status="failed",
            errors=violations
        )
    else:
        return ValidationResult(
            target="invariants",
            status="passed"
        )
```

---

## 5. Validation Pipeline

Every validation run follows this pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Detect Language                                             │
│     └── from capability_registry.yaml or project config         │
│                                                                 │
│  2. Check Invariants (pre-validation)                           │
│     └── InvariantChecker.validate()                             │
│     └── FAIL if invariants violated                             │
│                                                                 │
│  3. Run Tests                                                   │
│     └── TestRunnerAdapter.validate()                            │
│     └── Capture pass/fail status                                │
│                                                                 │
│  4. Run Lint (optional)                                         │
│     └── LintRunnerAdapter.validate()                            │
│     └── Capture lint errors                                     │
│                                                                 │
│  5. Check Architecture (optional)                               │
│     └── ArchitectureValidator.validate()                        │
│     └── Capture import violations                               │
│                                                                 │
│  6. Aggregate Results                                           │
│     └── Combine all ValidationResults                           │
│     └── Overall status = "passed" only if ALL pass              │
│                                                                 │
│  7. Generate ValidationResult Artifact                          │
│     └── Save to artifacts/validation/                           │
│                                                                 │
│  8. Emit Audit Log                                              │
│     └── Append to audit/validation.log                          │
│                                                                 │
│  9. Return Result                                               │
│     └── ValidationResult with aggregate status                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Error Handling Strategy

### 6.1 Error Taxonomy

```
ValidationError (base)
├── ValidatorConfigError           # Configuration issues
│   ├── LanguageNotSupportedError  # Unknown language
│   └── ValidatorNotFoundError     # Validator not registered
│
├── ValidatorExecutionError        # Execution issues
│   ├── CommandNotFoundError       # Test/lint command missing
│   ├── TimeoutError               # Command timed out
│   └── ProcessError               # Subprocess failed
│
└── InvariantViolationError        # Domain invariant violations
    ├── TestPlanNotLockedError     # TestPlan not locked
    ├── InvalidStatusError         # Invalid status transition
    ├── MissingApprovalError       # Missing approval record
    └── MissingDependencyError     # Missing artifact dependency
```

### 6.2 Error vs Failed Validation

**Important Distinction:**
- **ValidationResult(status="failed")**: Validation ran but target failed
- **Exception raised**: Validation could not run (config error, command missing)

Validators should:
- Return `ValidationResult(status="failed")` for normal validation failures
- Raise exceptions only for infrastructure/configuration errors

---

## 7. Audit Logging Design

### 7.1 Log Format

```json
{
  "timestamp": "2026-01-10T12:34:56.789Z",
  "validator": "test_runner",
  "target": "/path/to/repo",
  "language": "python",
  "status": "passed",
  "duration_ms": 1500,
  "errors": []
}
```

### 7.2 Log Location

- Primary log: `audit/validation.log`
- ValidationResult artifacts: `artifacts/validation/<id>.json`

### 7.3 Audit Trail Guarantees

- **Append-only**: Logs are never modified or deleted
- **Timestamped**: ISO-8601 with milliseconds
- **Traceable**: Links validator to target and result
- **Complete**: Every validation action logged

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# Test ValidatorPort protocol compliance
def test_validator_implements_protocol():
    assert isinstance(TestRunnerAdapter(...), ValidatorPort)

# Test pass case
def test_test_runner_pass(tmp_path):
    # Create passing test project
    validator = TestRunnerAdapter()
    result = validator.validate(tmp_path, context)
    assert result.passed
    assert result.errors == []

# Test fail case
def test_test_runner_fail(tmp_path):
    # Create failing test project
    validator = TestRunnerAdapter()
    result = validator.validate(tmp_path, context)
    assert not result.passed
    assert len(result.errors) > 0

# Test invariant violations
def test_invariant_checker_detects_unlocked_testplan(tmp_path):
    # Create artifacts with draft TestPlan
    checker = InvariantChecker()
    result = checker.validate(tmp_path / "artifacts", context)
    assert not result.passed
    assert "TestPlan must be locked" in result.errors[0]
```

### 8.2 Integration Tests

```python
# Test full validation pipeline
def test_validation_pipeline(git_repo):
    service = ValidationService()
    result = service.validate_all(git_repo)
    assert isinstance(result, ValidationResult)

# Test audit log creation
def test_validation_creates_audit_log(tmp_path):
    validator = TestRunnerAdapter()
    validator.validate(tmp_path, context)
    audit_log = tmp_path / "audit" / "validation.log"
    assert audit_log.exists()
```

---

## 9. CLI Integration

### 9.1 Commands to Wire

| Command | Validator | Description |
|---------|-----------|-------------|
| `rice-factor test` | TestRunnerAdapter | Run tests |
| `rice-factor lint` | LintRunnerAdapter | Run linter |
| `rice-factor validate` | All validators | Full validation |
| `rice-factor validate --arch` | ArchitectureValidator | Architecture only |

### 9.2 Command Flow

```
rice-factor test
     │
     ▼
Detect project language
     │
     ▼
Check invariants (pre-validation)
     │
     ▼
TestRunnerAdapter.validate(repo_root, context)
     │
     ├── Execute test command
     ├── Capture output
     ├── Parse results
     └── Return ValidationResult
     │
     ▼
Generate ValidationResult artifact
     │
     ▼
Emit audit log
     │
     ▼
Display result to user
```

---

## 10. Implementation Order

1. **F06-05**: ValidationResult Generator (foundation)
   - ValidatorPort protocol
   - ValidationResult, ValidationContext types
   - Validation error types
   - ValidationResultGenerator service

2. **F06-01**: Test Runner Adapter (P0)
   - TestRunnerAdapter implementation
   - Language-specific test commands
   - Output parsing
   - Unit tests

3. **F06-02**: Lint Runner Adapter (P1)
   - LintRunnerAdapter implementation
   - Language-specific lint commands
   - Output parsing
   - Unit tests

4. **F06-04**: Invariant Checker (P1)
   - InvariantChecker implementation
   - Domain invariant checks
   - Unit tests

5. **F06-03**: Architecture Validator (P1 - optional)
   - ArchitectureValidator implementation
   - Import analysis
   - Unit tests

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial design document |
