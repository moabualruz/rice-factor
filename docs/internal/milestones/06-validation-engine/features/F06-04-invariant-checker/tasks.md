# Feature: F06-04 Invariant Checker

## Status: Pending

## Description

Implement the InvariantChecker that verifies domain invariants before validation proceeds. This validator checks critical system constraints like TestPlan lock status, artifact status transitions, approval chain integrity, and dependency existence. These are pre-validation checks that ensure the system is in a valid state.

## Requirements Reference

- M06-U-003: Never auto-fix issues
- M06-U-004: Provide actionable error messages
- M06-IC-001: Verify TestPlan lock status
- M06-IC-002: Verify artifact status transitions
- M06-IC-003: Verify approval chain integrity
- M06-IC-004: Verify artifact dependencies exist
- raw/product-requirements-specification.md: Section 6 TestPlan Lock
- raw/02-Formal-Artifact-Schemas.md: Section 2.1 Status Transitions

## Tasks

### InvariantChecker Implementation
- [ ] Create `rice_factor/adapters/validators/invariant_checker.py`
  - [ ] Define `InvariantChecker` class implementing `ValidatorPort`
  - [ ] Implement `name` property returning "invariant_checker"
  - [ ] Implement `validate(target, context) -> ValidationResult`
    - [ ] Target is artifacts directory
    - [ ] Run all invariant checks
    - [ ] Collect all violations
    - [ ] Return ValidationResult

### TestPlan Lock Check
- [ ] Implement `check_testplan_lock(artifacts_dir: Path) -> list[str]`
  - [ ] Load TestPlan artifact if exists
  - [ ] If TestPlan exists but status != "locked", add violation
  - [ ] Message: "TestPlan must be locked before implementation"
  - [ ] If no TestPlan exists, skip (not an error)

### Status Transition Check
- [ ] Implement `check_status_transitions(artifacts_dir: Path) -> list[str]`
  - [ ] Load all artifacts
  - [ ] Verify each artifact has valid status: draft, approved, locked
  - [ ] Check no artifact has invalid status
  - [ ] Check locked artifacts have previously been approved

### Approval Chain Check
- [ ] Implement `check_approval_chain(artifacts_dir: Path) -> list[str]`
  - [ ] Load approvals from `_meta/approvals.json`
  - [ ] For each approved/locked artifact, verify approval exists
  - [ ] Message: "Missing approval record for artifact: {id}"
  - [ ] Verify approval records reference existing artifacts

### Dependency Check
- [ ] Implement `check_dependencies(artifacts_dir: Path) -> list[str]`
  - [ ] Load all artifacts with depends_on field
  - [ ] For each dependency, verify referenced artifact exists
  - [ ] Message: "Missing dependency {dep_id} for artifact {id}"
  - [ ] Verify dependencies are approved or locked

### Artifact Loading Utilities
- [ ] Implement `load_all_artifacts(artifacts_dir: Path) -> list[dict]`
  - [ ] Recursively find all JSON files in artifacts/
  - [ ] Skip _meta/ directory
  - [ ] Parse each as artifact
  - [ ] Handle malformed files gracefully

- [ ] Implement `load_approvals(approvals_path: Path) -> dict`
  - [ ] Load approvals.json
  - [ ] Return empty dict if file doesn't exist
  - [ ] Handle malformed file gracefully

### Exports
- [ ] Update `rice_factor/adapters/validators/__init__.py`
  - [ ] Export `InvariantChecker`

### Unit Tests
- [ ] Create `tests/unit/adapters/validators/test_invariant_checker.py`
  - [ ] Test `name` property returns "invariant_checker"
  - [ ] Test `validate` returns ValidationResult
  - [ ] Test all invariants pass returns status="passed"
  - [ ] Test unlocked TestPlan returns status="failed"
  - [ ] Test missing approval returns status="failed"
  - [ ] Test missing dependency returns status="failed"
  - [ ] Test invalid status returns status="failed"
  - [ ] Test no artifacts directory returns status="passed"
  - [ ] Test malformed artifact handling

### Test Fixtures
- [ ] Create test fixtures for invariant tests
  - [ ] Valid artifacts with locked TestPlan
  - [ ] Draft TestPlan (violation)
  - [ ] Approved artifact without approval record (violation)
  - [ ] Artifact with missing dependency (violation)

## Acceptance Criteria

- [ ] `InvariantChecker` implements `ValidatorPort`
- [ ] Detects unlocked TestPlan
- [ ] Detects missing approval records
- [ ] Detects missing dependencies
- [ ] Detects invalid status values
- [ ] Returns actionable error messages
- [ ] Does not modify any files
- [ ] Handles missing/malformed files gracefully
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/validators/invariant_checker.py` | CREATE | Invariant checker implementation |
| `rice_factor/adapters/validators/__init__.py` | UPDATE | Export InvariantChecker |
| `tests/unit/adapters/validators/test_invariant_checker.py` | CREATE | Unit tests |
| `tests/fixtures/invariants/` | CREATE | Test fixture files |

## Dependencies

- F06-05: ValidationResult Generator (ValidatorPort, ValidationResult, ValidationContext)
- M02: Artifact System (artifact loading, approval system)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
