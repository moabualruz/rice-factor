# Milestone 07: MVP Integration - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

The MVP Integration milestone connects all components from Milestones 01-06 into a working end-to-end system. This is primarily an integration effort - no new major components are created, but existing components are wired together with proper safety enforcement.

**Key Design Goals:**
- Wire real LLM providers (Claude/OpenAI) to CLI commands
- Connect executors to CLI commands
- Enforce workflow phase ordering
- Implement hard-fail safety conditions
- Create comprehensive integration test coverage

**Core Philosophy:**
- **Integration over creation** - Reuse existing components, minimize new code
- **Safety first** - Hard-fail on any safety violation
- **Auditability** - Every operation must be traceable
- **Determinism** - LLM outputs must be reproducible (temp ≤0.2)

---

## 2. Architecture

### 2.1 Integration Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLI Layer (M03)                                │
│  rice-factor init | plan | scaffold | impl | apply | test | refactor       │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          Integration Layer (M07)                           │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      Safety Enforcer                                 │  │
│  │  • TestPlan lock verification (hash-based)                          │  │
│  │  • Diff authorization checking                                       │  │
│  │  • Artifact presence validation                                      │  │
│  │  • Schema validation enforcement                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      Workflow Orchestrator                          │  │
│  │  • Phase service integration                                         │  │
│  │  • Artifact dependency management                                    │  │
│  │  • Context assembly for LLM calls                                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│   LLM Compiler    │  │      Executors        │  │  Validation Engine    │
│      (M04)        │  │       (M05)           │  │       (M06)           │
│                   │  │                       │  │                       │
│ • ClaudeAdapter   │  │ • ScaffoldExecutor    │  │ • TestRunnerAdapter   │
│ • OpenAIAdapter   │  │ • DiffExecutor        │  │ • LintRunnerAdapter   │
│ • ArtifactBuilder │  │ • RefactorExecutor    │  │ • InvariantChecker    │
│ • CompilerPasses  │  │ • CapabilityRegistry  │  │ • ValidationOrch.     │
└───────────────────┘  └───────────────────────┘  └───────────────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                        Artifact System (M02)                               │
│  ArtifactService | StoragePort | ApprovalsTracker | FilesystemStorage     │
└───────────────────────────────────────────────────────────────────────────┘
```

### 2.2 File Organization (Minimal Changes)

```
rice_factor/
├── domain/
│   └── services/
│       └── safety_enforcer.py              # NEW: Hard-fail enforcement
│
├── adapters/
│   └── storage/
│       └── lock_manager.py                 # NEW: Hash-based TestPlan lock
│
├── entrypoints/
│   └── cli/
│       └── commands/
│           ├── plan.py                     # UPDATE: Replace StubLLM with real LLM
│           ├── scaffold.py                 # UPDATE: Wire ScaffoldExecutor
│           ├── impl.py                     # UPDATE: Wire diff generation
│           ├── apply.py                    # UPDATE: Wire DiffExecutor
│           └── refactor.py                 # UPDATE: Wire RefactorExecutor
│
└── tests/
    └── integration/
        ├── test_e2e_workflow.py            # NEW: End-to-end tests
        └── test_safety_enforcement.py      # NEW: Safety violation tests
```

---

## 3. Workflow State Machine

### 3.1 Phase Transitions

```
┌──────────┐
│  UNINIT  │ ─── rice-factor init ───▶ ┌────────┐
└──────────┘                           │  INIT  │
                                       └────┬───┘
                                            │
                            rice-factor plan project
                            rice-factor approve
                                            │
                                            ▼
                                      ┌──────────┐
                                      │ PLANNING │
                                      └────┬─────┘
                                           │
                           rice-factor scaffold
                                           │
                                           ▼
                                     ┌───────────┐
                                     │ SCAFFOLDED│
                                     └─────┬─────┘
                                           │
                          rice-factor plan tests
                          rice-factor approve
                          rice-factor lock
                                           │
                                           ▼
                                    ┌─────────────┐
                              ┌─────│ TEST_LOCKED │◀────────┐
                              │     └──────┬──────┘         │
                              │            │                │
         rice-factor plan refactor         │    rice-factor test (pass)
         rice-factor refactor              │                │
                              │            ▼                │
                              │    ┌──────────────┐         │
                              │    │IMPLEMENTING  │─────────┘
                              │    └──────────────┘
                              │      rice-factor plan impl
                              │      rice-factor impl
                              │      rice-factor apply
                              │      rice-factor test
                              │            │
                              │            ▼
                              │    [Loop until all files done]
                              │
                              └────▶ [Refactor flows return to TEST_LOCKED]
```

### 3.2 Phase Guard Rules

| Command | Required Phase | Blocking Reason |
|---------|---------------|-----------------|
| `init` | UNINIT | "Project already initialized" |
| `plan project` | INIT+ | "Run rice-factor init first" |
| `scaffold` | PLANNING+ | "Approve ProjectPlan first" |
| `plan tests` | SCAFFOLDED+ | "Run scaffold first" |
| `lock` | SCAFFOLDED+ | "Approve TestPlan first" |
| `plan impl` | TEST_LOCKED+ | "Lock TestPlan first" |
| `impl` | TEST_LOCKED+ | "Approve ImplementationPlan first" |
| `apply` | TEST_LOCKED+ | "Generate diff first" |
| `test` | TEST_LOCKED+ | "Lock TestPlan first" |
| `plan refactor` | TEST_LOCKED+ | "Lock TestPlan first" |
| `refactor` | TEST_LOCKED+ | "Approve RefactorPlan first" |

---

## 4. Safety Enforcement Design

### 4.1 TestPlan Lock Verification

**Mechanism**: SHA-256 hash of test file contents stored in `.project/.lock`

```python
# Lock file format: .project/.lock
{
    "test_plan_id": "uuid-xxx",
    "locked_at": "2026-01-10T12:00:00Z",
    "test_files": {
        "tests/test_user.rs": "sha256:abc123...",
        "tests/test_email.rs": "sha256:def456..."
    }
}
```

**Verification Points**:
- Before `rice-factor impl` - verify no test modifications
- Before `rice-factor apply` - verify no test modifications
- After `rice-factor apply` - recompute hashes, verify unchanged

**Hard-Fail Error**:
```
ERROR: TestPlan lock violated
  Modified file: tests/test_user.rs
  Expected hash: sha256:abc123...
  Actual hash:   sha256:xyz789...

Action: Reset tests to locked state or create new TestPlan
```

### 4.2 Diff Authorization Checking

**Mechanism**: Parse diff file paths, compare to ImplementationPlan target

```python
def verify_diff_authorization(diff_content: str, plan: ImplementationPlan) -> None:
    """Verify diff only touches authorized files."""
    touched_files = parse_diff_files(diff_content)
    authorized = {plan.target}

    unauthorized = touched_files - authorized
    if unauthorized:
        raise UnauthorizedFileError(
            f"Diff touches unauthorized files: {unauthorized}"
        )
```

**Hard-Fail Error**:
```
ERROR: Diff authorization failed
  ImplementationPlan target: src/domain/user.rs
  Diff also touches: src/lib.rs, src/domain/email.rs

Action: Regenerate diff scoped to target file only
```

### 4.3 Hard-Fail Condition Matrix

| Condition | Detection Point | Error Type | Recovery |
|-----------|-----------------|------------|----------|
| Tests modified after lock | impl, apply, test | `TestsLockedError` | Reset tests or unlock |
| Artifact missing | Any command | `MissingArtifactError` | Generate missing artifact |
| Schema validation fails | Artifact load | `SchemaValidationError` | Fix or regenerate artifact |
| LLM outputs non-JSON | Plan commands | `InvalidLLMOutputError` | Retry LLM call |
| Diff touches unauthorized files | apply | `UnauthorizedFileError` | Regenerate diff |
| Phase requirement not met | Any command | `PhaseError` | Complete required steps |

---

## 5. LLM Integration

### 5.1 Replacing StubLLMAdapter

**Current State** (plan.py):
```python
from rice_factor.adapters.llm.stub import StubLLMAdapter
llm = StubLLMAdapter()
payload = llm.generate_project_plan()
```

**Target State**:
```python
from rice_factor.adapters.llm.claude import ClaudeAdapter
from rice_factor.domain.services.context_builder import ContextBuilder

# Build context from .project/ files
context = ContextBuilder(project_root).build_project_context()

# Use real LLM
llm = ClaudeAdapter(api_key=config.anthropic_api_key)
result = llm.generate(
    pass_type="project_planner",
    context=context,
    temperature=0.1
)
payload = result.artifact
```

### 5.2 Context Scoping per Phase

| Phase | Context Builder Method | Context Size | Inputs |
|-------|----------------------|--------------|--------|
| Project Planning | `build_project_context()` | Large | requirements.md, constraints.md, glossary.md |
| Scaffold Planning | `build_scaffold_context()` | Medium | ProjectPlan |
| Test Planning | `build_test_context()` | Medium | ScaffoldPlan, requirements.md |
| Implementation | `build_impl_context(target)` | Tiny | Target file, TestPlan assertions |
| Refactor | `build_refactor_context(goal)` | Tiny | Goal, target files |

### 5.3 LLM Configuration

```yaml
# config/llm.yaml
llm:
  provider: claude  # or openai
  temperature: 0.1  # ≤0.2 for determinism
  max_tokens: 4096
  timeout: 60
  retry:
    max_attempts: 3
    backoff: exponential
```

---

## 6. Error Handling Strategy

### 6.1 Error Taxonomy

```
IntegrationError (base)
├── SafetyViolationError
│   ├── TestsLockedError           # Tests modified after lock
│   ├── UnauthorizedFileError      # Diff touches wrong files
│   └── SchemaValidationError      # Invalid artifact schema
│
├── WorkflowError
│   ├── PhaseError                 # Wrong phase for command
│   ├── MissingPrerequisiteError   # Required artifact missing
│   └── ApprovalRequiredError      # Artifact not approved
│
└── ExecutionError
    ├── LLMError                   # LLM call failed
    ├── ExecutorError              # Executor failed
    └── ValidationError            # Tests failed
```

### 6.2 Error Recovery Guidance

Each error includes recovery guidance:

```python
class TestsLockedError(SafetyViolationError):
    def __init__(self, modified_files: list[str]):
        self.modified_files = modified_files
        super().__init__(
            f"TestPlan lock violated. Modified: {modified_files}",
            recovery="Reset tests to locked state: git checkout <test_files>"
        )
```

---

## 7. Testing Strategy

### 7.1 Integration Test Scenarios

**Happy Path Tests (E2E)**:

| Test | Description | Exit Criteria |
|------|-------------|---------------|
| `test_e2e_init_to_scaffold` | Init → plan → approve → scaffold | EC-001, EC-002 |
| `test_e2e_test_lock` | Plan tests → approve → lock | EC-003 |
| `test_e2e_implementation` | Plan impl → impl → apply → test | EC-004 |
| `test_e2e_refactor` | Plan refactor → dry-run | EC-005 |
| `test_e2e_full_workflow` | Complete happy path | EC-001 through EC-006 |
| `test_audit_trail` | Verify audit completeness | EC-007 |

**Safety Violation Tests**:

| Test | Description | Expected Result |
|------|-------------|-----------------|
| `test_fail_on_test_modification` | Modify test after lock | `TestsLockedError` |
| `test_fail_on_missing_artifact` | Skip ProjectPlan | `MissingPrerequisiteError` |
| `test_fail_on_invalid_json` | Mock LLM invalid response | `InvalidLLMOutputError` |
| `test_fail_on_unauthorized_diff` | Diff touches extra files | `UnauthorizedFileError` |
| `test_fail_on_wrong_phase` | Scaffold before plan | `PhaseError` |

### 7.2 Test Fixtures

```python
@pytest.fixture
def mvp_project(tmp_path):
    """Create a minimal MVP project for testing."""
    # Create .project/ structure
    project_dir = tmp_path / ".project"
    project_dir.mkdir()
    (project_dir / "requirements.md").write_text("User management system")
    (project_dir / "constraints.md").write_text("Language: Rust")
    (project_dir / "glossary.md").write_text("User: A system user")

    # Create artifacts/ structure
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "audit").mkdir()

    return tmp_path
```

---

## 8. Audit Trail Design

### 8.1 Audit Log Format

```json
{
  "timestamp": "2026-01-10T12:34:56.789Z",
  "operation": "plan_project",
  "phase": "INIT",
  "actor": "cli",
  "status": "success",
  "artifact_id": "uuid-xxx",
  "details": {
    "llm_provider": "claude",
    "llm_model": "claude-3-sonnet",
    "duration_ms": 1500
  }
}
```

### 8.2 Audit Points

| Operation | Audit Entry |
|-----------|-------------|
| Plan artifact | LLM call details, artifact ID |
| Approve artifact | Approver, artifact ID |
| Lock TestPlan | File hashes, lock timestamp |
| Execute scaffold | Files created |
| Apply diff | Files modified, diff hash |
| Run tests | Test results, duration |
| Safety violation | Violation type, details |

---

## 9. Implementation Order

1. **F07-07**: Safety Enforcement
   - Create `safety_enforcer.py`
   - Create `lock_manager.py`
   - Wire safety checks to commands

2. **F07-01**: Init Flow Integration
   - Add intake file validation
   - Add blocking until non-empty

3. **F07-02**: Project Planning Integration
   - Replace StubLLMAdapter in plan.py
   - Wire ContextBuilder
   - Connect ArtifactBuilder

4. **F07-03**: Scaffolding Integration
   - Wire ScaffoldExecutor to scaffold command
   - Add phase transition after scaffold

5. **F07-04**: Test Lock Integration
   - Wire lock command with hash storage
   - Add verification to impl/apply commands

6. **F07-05**: Implementation Loop
   - Wire plan impl with real LLM
   - Wire impl command with diff generation
   - Wire apply with DiffExecutor
   - Wire test with TestRunnerAdapter

7. **F07-06**: Refactoring Integration
   - Wire RefactorExecutor
   - Add capability checking

8. **F07-08**: Integration Tests
   - Create E2E test suite
   - Create safety violation tests

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial design document |
