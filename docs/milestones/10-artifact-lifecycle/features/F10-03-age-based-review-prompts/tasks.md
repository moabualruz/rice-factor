# Feature F10-03: Age-Based Review Prompts - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-03-01 | Create LifecycleService | Complete | P0 |
| T10-03-02 | Implement review prompt generation | Complete | P0 |
| T10-03-03 | Add work blocking check | Complete | P0 |
| T10-03-04 | Integrate with CLI commands | Complete | P0 |
| T10-03-05 | Add record review functionality | Complete | P1 |
| T10-03-06 | Write unit tests | Complete | P0 |

---

## 2. Task Details

### T10-03-01: Create LifecycleService

**Objective**: Central service for lifecycle management.

**Files Created**:
- [x] `rice_factor/domain/services/lifecycle_service.py`

**Implementation**:
```python
@dataclass
class LifecycleService:
    artifact_store: StoragePort
    config: LifecycleConfig = field(default_factory=LifecycleConfig.default)
    arch_validator: ArchitectureValidatorPort | None = None
    coverage_monitor: CoverageMonitorPort | None = None

    def evaluate_all(self) -> list[PolicyResult]: ...
    def get_blocking_issues(self) -> list[PolicyResult]: ...
    def generate_age_report(self) -> AgeReport: ...
```

**Acceptance Criteria**:
- [x] Service follows domain patterns
- [x] Supports optional validators
- [x] Evaluates all artifacts

---

### T10-03-02: Implement Review Prompt Generation

**Objective**: Generate actionable review prompts.

**Files Modified**:
- [x] `rice_factor/domain/services/lifecycle_service.py`

**Created Models**:
- [x] `ReviewPrompt` - Prompt for artifact review
- [x] `AgeReport` - Comprehensive age report

**Prompt Types**:

| Urgency | Message |
|---------|---------|
| INFORMATIONAL | "FYI: {artifact} is {age} months old" |
| RECOMMENDED | "{artifact} should be reviewed (age: {age} months)" |
| REQUIRED | "Review required: {artifact} ({reason})" |
| MANDATORY | "BLOCKING: {artifact} must be reviewed before proceeding" |

**Acceptance Criteria**:
- [x] Prompts are actionable
- [x] Messages include relevant details
- [x] Suggested actions provided

---

### T10-03-03: Add Work Blocking Check

**Objective**: Prevent new work when mandatory review pending.

**Files Modified**:
- [x] `rice_factor/domain/services/lifecycle_service.py`

**Methods Added**:
- [x] `check_can_proceed()` - Check if work can proceed
- [x] `require_can_proceed()` - Raise if blocked
- [x] `get_blocking_issues()` - Get MANDATORY issues

**Exception**:
- [x] `LifecycleBlockingError` - Raised when blocked

**Acceptance Criteria**:
- [x] Mandatory issues block work
- [x] Clear error message shown
- [x] `LifecycleBlockingError` includes blocking issues

---

### T10-03-04: Integrate with CLI Commands

**Objective**: Show prompts in relevant commands.

**Files Modified**:
- [x] `rice_factor/entrypoints/cli/commands/artifact.py`

**Commands Updated**:
- [x] `rice-factor artifact age` - Shows age report with prompts
- [x] Exit codes: 0=healthy, 1=needs review, 2=overdue

CLI integration with plan/impl commands complete:
- [x] `_check_lifecycle()` helper added to plan.py
- [x] `rice-factor plan impl` shows lifecycle warnings
- [x] `rice-factor plan refactor` shows lifecycle warnings
- [x] Optional blocking via `block_on_mandatory` parameter

**Acceptance Criteria**:
- [x] Warnings shown in age report
- [x] Blocking issues result in exit code 2
- [x] User knows what to do via suggested actions

---

### T10-03-05: Add Record Review Functionality

**Objective**: Allow marking artifacts as reviewed.

**Files Modified**:
- [x] `rice_factor/entrypoints/cli/commands/artifact.py`

**Command Added**:
```bash
rice-factor artifact review <artifact-id> [--notes "Review notes"]
```

**Service Methods**:
- [x] `record_review(artifact_id, notes)` - Mark as reviewed
- [x] `extend_artifact(artifact_id, months, reason)` - Extend validity

**Acceptance Criteria**:
- [x] Review timestamp updated
- [x] Optional notes saved
- [x] LOCKED artifacts rejected

---

### T10-03-06: Write Unit Tests

**Objective**: Test review prompt system.

**Files Created**:
- [x] `tests/unit/domain/services/test_lifecycle_service.py`

**Test Cases** (25 tests):
- [x] ReviewPrompt creation and to_dict
- [x] AgeReport creation and to_dict
- [x] LifecycleBlockingError message formatting
- [x] evaluate_artifact with/without policy
- [x] evaluate_all with multiple artifacts
- [x] evaluate_all with arch validator
- [x] evaluate_all with coverage monitor
- [x] get_blocking_issues empty/with violations
- [x] check_can_proceed true/false
- [x] require_can_proceed success/raises
- [x] generate_prompts empty/for old/mandatory/recommended
- [x] generate_age_report
- [x] record_review updates timestamp/with notes
- [x] extend_artifact

**CLI Test Cases** (7 new tests for review command):
- [x] review --help shows options
- [x] review errors for not found artifact
- [x] review rejects LOCKED artifacts
- [x] review updates timestamp
- [x] review with notes saves notes
- [x] review resets age timer

**Acceptance Criteria**:
- [x] All scenarios tested
- [x] 50 tests passing for lifecycle + artifact commands

---

## 3. Task Dependencies

```
T10-03-01 (Service) ──→ T10-03-02 (Prompts) ──→ T10-03-03 (Blocking)
                                                      │
                                           ┌──────────┴──────────┐
                                           ↓                     ↓
                                   T10-03-04 (CLI)       T10-03-05 (Review)
                                           │                     │
                                           └──────────┬──────────┘
                                                      ↓
                                              T10-03-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T10-03-01 | Medium | Service design |
| T10-03-02 | Medium | Message formatting |
| T10-03-03 | Medium | Integration |
| T10-03-04 | Medium | Multiple commands |
| T10-03-05 | Low | Simple command |
| T10-03-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.1.0 | 2026-01-11 | Implementation | All tasks completed |
