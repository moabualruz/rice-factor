# Feature F08-04: Invariant Enforcement Stage - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-04-01 | Implement InvariantEnforcer adapter | **Complete** | P0 |
| T08-04-02 | Implement test immutability check | **Complete** | P0 |
| T08-04-03 | Implement artifact-to-code mapping check | **Complete** | P0 |
| T08-04-04 | Implement architecture rule check | Deferred | P1 |
| T08-04-05 | Add git diff integration | **Complete** | P0 |
| T08-04-06 | Add CLI command | **Complete** | P0 |
| T08-04-07 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T08-04-01: Implement InvariantEnforcer Adapter

**Objective**: Create the Stage 3 validator adapter.

**Files Created**:
- [x] `rice_factor/adapters/ci/invariant_enforcer.py`

**Implementation**:
- [x] Create `InvariantEnforcementAdapter` class implementing `CIValidatorPort`
- [x] Orchestrate multiple invariant checks
- [x] Aggregate failures from all checks
- [x] Return `CIStageResult` with failures

**Acceptance Criteria**:
- [x] Runs all configured invariant checks
- [x] Aggregates failures correctly

---

### T08-04-02: Implement Test Immutability Check

**Objective**: Prevent test modifications after TestPlan lock.

**Implementation**:
- [x] Find locked TestPlan artifact (status == "locked")
- [x] Get list of changed files from git diff
- [x] Check if any changed file is in `tests/` directory
- [x] Create `TEST_MODIFICATION_AFTER_LOCK` failure
- [x] Include specific file path in failure

**Acceptance Criteria**:
- [x] Detects test file modifications
- [x] Only enforces when TestPlan is locked
- [x] Ignores test changes if TestPlan not locked

---

### T08-04-03: Implement Artifact-to-Code Mapping Check

**Objective**: Ensure all code changes are covered by plans.

**Implementation**:
- [x] Load all ImplementationPlan artifacts, extract `target` paths
- [x] Load all RefactorPlan artifacts, extract affected files (from/to paths)
- [x] Build set of "allowed" file paths
- [x] Get list of changed source files from git diff
- [x] Create `UNPLANNED_CODE_CHANGE` for files not in allowed set
- [x] Exclude non-source files (docs, config, etc.)
- [x] Skip check if no approved plans exist

**Acceptance Criteria**:
- [x] Detects unplanned code changes
- [x] Correctly extracts targets from plans
- [x] Handles multiple plans

---

### T08-04-04: Implement Architecture Rule Check

**Status**: Deferred to M12 (Language Refactoring)

**Rationale**: Architecture validation requires integration with language-specific analyzers that are part of M12. The InvariantEnforcementAdapter has a placeholder for this functionality.

---

### T08-04-05: Add Git Diff Integration

**Objective**: Get list of changed files from git.

**Implementation**:
- [x] Integrated into `InvariantEnforcementAdapter._get_changed_files()`
- [x] Support PR mode (diff against base branch)
- [x] Support push mode fallback (diff against previous commit)
- [x] Return set of changed file paths
- [x] Graceful error handling (fail open)

**Commands Used**:
```bash
# PR mode
git diff --name-only {base_branch}...HEAD

# Push mode fallback
git diff --name-only HEAD~1
```

**Acceptance Criteria**:
- [x] Works in CI environment
- [x] Handles various git scenarios

---

### T08-04-06: Add CLI Command

**Objective**: Add `rice-factor ci validate-invariants` command.

**Implementation**:
- [x] Add command to `ci.py` command group (already existed)
- [x] Wire up `InvariantEnforcementAdapter` adapter
- [x] Add `--json` output option
- [x] Exit with code 1 on failure

**Acceptance Criteria**:
- [x] Command runs invariant enforcement
- [x] Clear output for each invariant type

---

### T08-04-07: Write Unit Tests

**Objective**: Test invariant enforcement logic.

**Files Created**:
- [x] `tests/unit/adapters/ci/test_invariant_enforcer.py`

**Test Cases** (18 tests):
- [x] Test locked TestPlan with test changes fails
- [x] Test locked TestPlan without test changes passes
- [x] Test unlocked TestPlan with test changes passes
- [x] Test no TestPlan allows test changes
- [x] Test unplanned code change fails
- [x] Test planned code change passes
- [x] Test refactor plan allows file move
- [x] Test no plans skips mapping check
- [x] Test draft plan not counted
- [x] Test ignores non-source files
- [x] Test multiple failures reported
- [x] Test custom configuration options

**Acceptance Criteria**:
- [x] All invariant scenarios covered
- [x] Mock git operations for testing

---

## 3. Task Dependencies

```
T08-04-05 (Git Diff) ────────────────────────────┐
                                                  │
T08-04-01 (Adapter) ──┬──→ T08-04-02 (Test Lock) ┼──→ T08-04-06 (CLI)
                      │                           │          │
                      ├──→ T08-04-03 (Mapping) ──┤          │
                      │                           │          ↓
                      └──→ T08-04-04 (Arch) ─────┘   T08-04-07 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T08-04-01 | Low | Adapter skeleton |
| T08-04-02 | Medium | Lock detection + git |
| T08-04-03 | High | Plan parsing + set ops |
| T08-04-04 | Low | Deferred to M12 |
| T08-04-05 | Medium | Git integration |
| T08-04-06 | Low | CLI wiring |
| T08-04-07 | High | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | Core tasks complete - 18 tests passing, T08-04-04 deferred |
