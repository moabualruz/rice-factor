# Feature F08-01: CI Pipeline Framework - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-01-01 | Create CI domain models | **Complete** | P0 |
| T08-01-02 | Implement CIFailureCode enum | **Complete** | P0 |
| T08-01-03 | Implement CIValidatorPort protocol | **Complete** | P0 |
| T08-01-04 | Implement CIPipeline orchestrator | **Complete** | P0 |
| T08-01-05 | Create CI CLI command group | **Complete** | P0 |
| T08-01-06 | Add JSON output support | **Complete** | P1 |
| T08-01-07 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T08-01-01: Create CI Domain Models

**Objective**: Create Pydantic models for CI results and failures.

**Files Created**:
- [x] `rice_factor/domain/ci/__init__.py`
- [x] `rice_factor/domain/ci/models.py`

**Implementation**:
- [x] Create `CIFailure` dataclass with code, message, file_path, remediation
- [x] Create `CIStageResult` dataclass with stage, passed, failures, duration
- [x] Create `CIPipelineResult` dataclass with aggregate results
- [x] Add `to_json()` method for JSON serialization

**Acceptance Criteria**:
- [x] All models are immutable (frozen dataclass)
- [x] JSON serialization produces valid output
- [x] Models follow existing domain patterns

---

### T08-01-02: Implement CIFailureCode Enum

**Objective**: Create the canonical CI failure taxonomy as an enum.

**Files Created**:
- [x] `rice_factor/domain/ci/failure_codes.py`

**Implementation**:
- [x] Create `CIFailureCode(str, Enum)` with all failure codes from spec
- [x] Add remediation guide mapping
- [x] Add failure code categories (artifact, approval, invariant, audit)

**Failure Codes**:
- [x] `DRAFT_ARTIFACT_PRESENT`
- [x] `LOCKED_ARTIFACT_MODIFIED`
- [x] `SCHEMA_VALIDATION_FAILED`
- [x] `ARTIFACT_NOT_APPROVED`
- [x] `APPROVAL_METADATA_MISSING`
- [x] `TEST_MODIFICATION_AFTER_LOCK`
- [x] `UNPLANNED_CODE_CHANGE`
- [x] `ARCHITECTURE_VIOLATION`
- [x] `TEST_FAILURE`
- [x] `ORPHANED_CODE_CHANGE`
- [x] `AUDIT_INTEGRITY_VIOLATION`

**Acceptance Criteria**:
- [x] All codes from spec 3.14 are implemented (16 total)
- [x] Each code has remediation guidance

---

### T08-01-03: Implement CIValidatorPort Protocol

**Objective**: Create the protocol interface for CI validators.

**Files Created**:
- [x] `rice_factor/domain/ports/ci_validator.py`

**Implementation**:
- [x] Create `CIValidatorPort` protocol with `validate(repo_root) -> CIStageResult`
- [x] Document interface contract

**Acceptance Criteria**:
- [x] Protocol follows existing port patterns
- [x] Interface is minimal and focused

---

### T08-01-04: Implement CIPipeline Orchestrator

**Objective**: Create the pipeline orchestrator that runs all stages.

**Files Created**:
- [x] `rice_factor/domain/ci/pipeline.py`

**Implementation**:
- [x] Create `CIPipeline` class that accepts validators
- [x] Implement `run()` method that executes stages in order
- [x] Add `stop_on_failure` option
- [x] Calculate total duration
- [x] Aggregate results

**Acceptance Criteria**:
- [x] Stages run in correct order
- [x] Pipeline stops on first failure when configured
- [x] Results are correctly aggregated

---

### T08-01-05: Create CI CLI Command Group

**Objective**: Create the `rice-factor ci` command group.

**Files Created**:
- [x] `rice_factor/entrypoints/cli/commands/ci.py`

**Implementation**:
- [x] Create `ci_app` Typer app
- [x] Add `validate` command for full pipeline
- [x] Add `validate-artifacts` command for Stage 1
- [x] Add `validate-approvals` command for Stage 2
- [x] Add `validate-invariants` command for Stage 3
- [x] Add `validate-audit` command for Stage 5
- [x] Register with main app

**Acceptance Criteria**:
- [x] `rice-factor ci --help` shows all commands
- [x] Commands exit with non-zero on failure
- [x] Output is clear and actionable

---

### T08-01-06: Add JSON Output Support

**Objective**: Add `--json` flag for machine-readable output.

**Implementation**:
- [x] Add `--json` option to all CI commands
- [x] Output JSON to stdout when flag is set
- [x] Ensure JSON is valid and parseable

**Acceptance Criteria**:
- [x] JSON output matches `CIPipelineResult.to_json()` schema
- [x] Human output is default

---

### T08-01-07: Write Unit Tests

**Objective**: Comprehensive test coverage for CI framework.

**Files Created**:
- [x] `tests/unit/domain/ci/__init__.py`
- [x] `tests/unit/domain/ci/test_models.py`
- [x] `tests/unit/domain/ci/test_failure_codes.py`
- [x] `tests/unit/domain/ci/test_pipeline.py`

**Test Cases** (41 tests total):
- [x] Test CIPipelineResult serialization
- [x] Test CIFailure creation
- [x] Test pipeline stage ordering
- [x] Test stop_on_failure behavior
- [x] Test all failure codes exist
- [x] Test category and remediation properties
- [x] Test stage result serialization
- [x] Test exception handling in validators

**Acceptance Criteria**:
- [x] All 41 tests pass
- [x] Comprehensive coverage of models, failure codes, and pipeline

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
| 1.0.1 | 2026-01-11 | Implementation | All tasks complete - 41 tests passing |
