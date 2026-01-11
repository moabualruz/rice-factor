# Feature F08-04: Invariant Enforcement Stage - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-04-01 | Implement InvariantEnforcer adapter | Pending | P0 |
| T08-04-02 | Implement test immutability check | Pending | P0 |
| T08-04-03 | Implement artifact-to-code mapping check | Pending | P0 |
| T08-04-04 | Implement architecture rule check | Pending | P1 |
| T08-04-05 | Add git diff integration | Pending | P0 |
| T08-04-06 | Add CLI command | Pending | P0 |
| T08-04-07 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T08-04-01: Implement InvariantEnforcer Adapter

**Objective**: Create the Stage 3 validator adapter.

**Files to Create**:
- [ ] `rice_factor/adapters/ci/invariant_enforcer.py`

**Implementation**:
- [ ] Create `InvariantEnforcer` class implementing `CIValidatorPort`
- [ ] Orchestrate multiple invariant checks
- [ ] Aggregate failures from all checks
- [ ] Return `CIStageResult` with failures

**Acceptance Criteria**:
- [ ] Runs all configured invariant checks
- [ ] Aggregates failures correctly

---

### T08-04-02: Implement Test Immutability Check

**Objective**: Prevent test modifications after TestPlan lock.

**Implementation**:
- [ ] Find locked TestPlan artifact (status == "locked")
- [ ] Get list of changed files from git diff
- [ ] Check if any changed file is in `tests/` directory
- [ ] Create `TEST_MODIFICATION_AFTER_LOCK` failure
- [ ] Include specific file path in failure

**Pseudocode** (from spec 3.7.1):
```python
if git_diff_contains("tests/"):
    fail("test_modification_after_lock")
```

**Acceptance Criteria**:
- [ ] Detects test file modifications
- [ ] Only enforces when TestPlan is locked
- [ ] Ignores test changes if TestPlan not locked

---

### T08-04-03: Implement Artifact-to-Code Mapping Check

**Objective**: Ensure all code changes are covered by plans.

**Implementation**:
- [ ] Load all ImplementationPlan artifacts, extract `target` paths
- [ ] Load all RefactorPlan artifacts, extract affected files
- [ ] Build set of "allowed" file paths
- [ ] Get list of changed source files from git diff
- [ ] Create `UNPLANNED_CODE_CHANGE` for files not in allowed set
- [ ] Exclude non-source files (docs, config, etc.)

**Pseudocode** (from spec 3.7.2):
```python
changed_files = git_diff_files()
allowed_files = union(
    ImplementationPlan.targets,
    RefactorPlan.affected_files
)
if any(changed_files not in allowed_files):
    fail("unplanned_code_change")
```

**Acceptance Criteria**:
- [ ] Detects unplanned code changes
- [ ] Correctly extracts targets from plans
- [ ] Handles multiple plans

---

### T08-04-04: Implement Architecture Rule Check

**Objective**: Enforce architecture rules if defined.

**Implementation**:
- [ ] Check if ArchitecturePlan exists
- [ ] Delegate to existing ArchitectureValidator from M06
- [ ] Create `ARCHITECTURE_VIOLATION` failures
- [ ] Optional check (skip if no ArchitecturePlan)

**Acceptance Criteria**:
- [ ] Reuses existing architecture validation
- [ ] Gracefully skips if not configured

---

### T08-04-05: Add Git Diff Integration

**Objective**: Get list of changed files from git.

**Implementation**:
- [ ] Create `GitDiffService` or reuse existing git integration
- [ ] Support PR mode (diff against base branch)
- [ ] Support push mode (diff against previous commit)
- [ ] Handle merge commits
- [ ] Return list of changed file paths

**Commands**:
```bash
# PR mode
git diff --name-only origin/main...HEAD

# Push mode
git diff --name-only HEAD~1...HEAD
```

**Acceptance Criteria**:
- [ ] Works in CI environment
- [ ] Handles various git scenarios

---

### T08-04-06: Add CLI Command

**Objective**: Add `rice-factor ci validate-invariants` command.

**Implementation**:
- [ ] Add command to `ci.py` command group
- [ ] Wire up `InvariantEnforcer` adapter
- [ ] Add options for selecting which checks to run
- [ ] Add `--json` output option
- [ ] Exit with code 1 on failure

**Acceptance Criteria**:
- [ ] Command runs invariant enforcement
- [ ] Clear output for each invariant type

---

### T08-04-07: Write Unit Tests

**Objective**: Test invariant enforcement logic.

**Files to Create**:
- [ ] `tests/unit/adapters/ci/test_invariant_enforcer.py`

**Test Cases**:
- [ ] Test locked TestPlan with test changes fails
- [ ] Test locked TestPlan without test changes passes
- [ ] Test unlocked TestPlan with test changes passes
- [ ] Test unplanned code change fails
- [ ] Test planned code change passes
- [ ] Test architecture violation fails
- [ ] Test no ArchitecturePlan skips check

**Acceptance Criteria**:
- [ ] All invariant scenarios covered
- [ ] Mock git operations for testing

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
| T08-04-04 | Low | Reuse M06 validator |
| T08-04-05 | Medium | Git integration |
| T08-04-06 | Low | CLI wiring |
| T08-04-07 | High | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
