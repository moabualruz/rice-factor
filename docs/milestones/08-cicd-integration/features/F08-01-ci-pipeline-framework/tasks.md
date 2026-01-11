# Feature F08-01: CI Pipeline Framework - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-01-01 | Create CI domain models | Pending | P0 |
| T08-01-02 | Implement CIFailureCode enum | Pending | P0 |
| T08-01-03 | Implement CIValidatorPort protocol | Pending | P0 |
| T08-01-04 | Implement CIPipeline orchestrator | Pending | P0 |
| T08-01-05 | Create CI CLI command group | Pending | P0 |
| T08-01-06 | Add JSON output support | Pending | P1 |
| T08-01-07 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T08-01-01: Create CI Domain Models

**Objective**: Create Pydantic models for CI results and failures.

**Files to Create**:
- [ ] `rice_factor/domain/ci/__init__.py`
- [ ] `rice_factor/domain/ci/models.py`

**Implementation**:
- [ ] Create `CIFailure` dataclass with code, message, file_path, remediation
- [ ] Create `CIStageResult` dataclass with stage, passed, failures, duration
- [ ] Create `CIResult` dataclass with aggregate results
- [ ] Add `to_json()` method for JSON serialization

**Acceptance Criteria**:
- [ ] All models are immutable (frozen dataclass or Pydantic)
- [ ] JSON serialization produces valid output
- [ ] Models follow existing domain patterns

---

### T08-01-02: Implement CIFailureCode Enum

**Objective**: Create the canonical CI failure taxonomy as an enum.

**Files to Create**:
- [ ] `rice_factor/domain/ci/failure_codes.py`

**Implementation**:
- [ ] Create `CIFailureCode(str, Enum)` with all failure codes from spec
- [ ] Add remediation guide mapping
- [ ] Add failure code categories (artifact, approval, invariant, audit)

**Failure Codes**:
- [ ] `DRAFT_ARTIFACT_PRESENT`
- [ ] `LOCKED_ARTIFACT_MODIFIED`
- [ ] `SCHEMA_VALIDATION_FAILED`
- [ ] `ARTIFACT_NOT_APPROVED`
- [ ] `APPROVAL_METADATA_MISSING`
- [ ] `TEST_MODIFICATION_AFTER_LOCK`
- [ ] `UNPLANNED_CODE_CHANGE`
- [ ] `ARCHITECTURE_VIOLATION`
- [ ] `TEST_FAILURE`
- [ ] `ORPHANED_CODE_CHANGE`
- [ ] `AUDIT_INTEGRITY_VIOLATION`

**Acceptance Criteria**:
- [ ] All codes from spec 3.14 are implemented
- [ ] Each code has remediation guidance

---

### T08-01-03: Implement CIValidatorPort Protocol

**Objective**: Create the protocol interface for CI validators.

**Files to Create**:
- [ ] `rice_factor/domain/ports/ci_validator.py`

**Implementation**:
- [ ] Create `CIValidatorPort` protocol with `validate(repo_root) -> CIStageResult`
- [ ] Document interface contract

**Acceptance Criteria**:
- [ ] Protocol follows existing port patterns
- [ ] Interface is minimal and focused

---

### T08-01-04: Implement CIPipeline Orchestrator

**Objective**: Create the pipeline orchestrator that runs all stages.

**Files to Create**:
- [ ] `rice_factor/domain/ci/pipeline.py`

**Implementation**:
- [ ] Create `CIPipeline` class that accepts validators
- [ ] Implement `run()` method that executes stages in order
- [ ] Add `stop_on_failure` option
- [ ] Calculate total duration
- [ ] Aggregate results

**Acceptance Criteria**:
- [ ] Stages run in correct order
- [ ] Pipeline stops on first failure when configured
- [ ] Results are correctly aggregated

---

### T08-01-05: Create CI CLI Command Group

**Objective**: Create the `rice-factor ci` command group.

**Files to Create**:
- [ ] `rice_factor/entrypoints/cli/commands/ci.py`

**Implementation**:
- [ ] Create `ci_app` Typer app
- [ ] Add `validate` command for full pipeline
- [ ] Add `validate-artifacts` command for Stage 1
- [ ] Add `validate-approvals` command for Stage 2
- [ ] Add `validate-invariants` command for Stage 3
- [ ] Add `validate-audit` command for Stage 5
- [ ] Register with main app

**Acceptance Criteria**:
- [ ] `rice-factor ci --help` shows all commands
- [ ] Commands exit with non-zero on failure
- [ ] Output is clear and actionable

---

### T08-01-06: Add JSON Output Support

**Objective**: Add `--json` flag for machine-readable output.

**Implementation**:
- [ ] Add `--json` option to all CI commands
- [ ] Output JSON to stdout when flag is set
- [ ] Ensure JSON is valid and parseable

**Acceptance Criteria**:
- [ ] JSON output matches `CIResult.to_json()` schema
- [ ] Human output is default

---

### T08-01-07: Write Unit Tests

**Objective**: Comprehensive test coverage for CI framework.

**Files to Create**:
- [ ] `tests/unit/domain/ci/test_models.py`
- [ ] `tests/unit/domain/ci/test_failure_codes.py`
- [ ] `tests/unit/domain/ci/test_pipeline.py`
- [ ] `tests/unit/entrypoints/cli/commands/test_ci.py`

**Test Cases**:
- [ ] Test CIResult serialization
- [ ] Test CIFailure creation
- [ ] Test pipeline stage ordering
- [ ] Test stop_on_failure behavior
- [ ] Test CLI exit codes

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Coverage > 90%

---

## 3. Task Dependencies

```
T08-01-01 (Models) ─────────────┐
                                 │
T08-01-02 (Failure Codes) ──────┼──→ T08-01-04 (Pipeline) ──→ T08-01-05 (CLI)
                                 │                                   │
T08-01-03 (Port) ───────────────┘                                   │
                                                                     ↓
                                               T08-01-06 (JSON) ←───┘
                                                                     │
                                                                     ↓
                                               T08-01-07 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T08-01-01 | Low | Simple dataclasses |
| T08-01-02 | Low | Enum definition |
| T08-01-03 | Low | Protocol definition |
| T08-01-04 | Medium | Orchestration logic |
| T08-01-05 | Medium | CLI integration |
| T08-01-06 | Low | JSON serialization |
| T08-01-07 | Medium | Comprehensive tests |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
