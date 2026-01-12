# Feature F08-02: Artifact Validation Stage - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-02-01 | Implement ArtifactValidator adapter | **Complete** | P0 |
| T08-02-02 | Add schema validation check | **Complete** | P0 |
| T08-02-03 | Add draft artifact detection | **Complete** | P0 |
| T08-02-04 | Add locked artifact change detection | **Complete** | P0 |
| T08-02-05 | Add CLI command | **Complete** | P0 |
| T08-02-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T08-02-01: Implement ArtifactValidator Adapter

**Objective**: Create the Stage 1 validator adapter.

**Files Created**:
- [x] `rice_factor/adapters/ci/__init__.py`
- [x] `rice_factor/adapters/ci/artifact_validator.py`

**Implementation**:
- [x] Create `ArtifactValidationAdapter` class implementing `CIValidatorPort`
- [x] Implement artifact discovery (scan `artifacts/` directory)
- [x] Skip metadata files (`_meta/`)
- [x] Skip approval files (`.approval.json`)
- [x] Skip index files
- [x] Return `CIStageResult` with failures

**Acceptance Criteria**:
- [x] Discovers all artifacts in repository
- [x] Returns structured results

---

### T08-02-02: Add Schema Validation Check

**Objective**: Validate JSON Schema for all artifacts.

**Implementation**:
- [x] Load artifact from JSON file
- [x] Validate against appropriate schema using existing `ArtifactValidator`
- [x] Create `SCHEMA_VALIDATION_FAILED` failure on error
- [x] Include validation error details in failure

**Acceptance Criteria**:
- [x] Invalid artifacts are detected
- [x] Error message includes specific validation issue

---

### T08-02-03: Add Draft Artifact Detection

**Objective**: Detect and reject draft artifacts in CI.

**Implementation**:
- [x] Check `status` field of each artifact
- [x] Create `DRAFT_ARTIFACT_PRESENT` failure if status is "draft"
- [x] Include artifact path and ID in failure

**Acceptance Criteria**:
- [x] Draft artifacts cause CI failure
- [x] Remediation guidance is actionable

---

### T08-02-04: Add Locked Artifact Change Detection

**Objective**: Detect modifications to locked artifacts.

**Implementation**:
- [x] For artifacts with status "locked", check git history
- [x] Use `git diff` to detect changes to locked artifact files
- [x] Create `LOCKED_ARTIFACT_MODIFIED` failure on change
- [x] Compare against base branch (for PRs)

**Acceptance Criteria**:
- [x] Locked artifact modifications are detected
- [x] Works in PR and push contexts

---

### T08-02-05: Add CLI Command

**Objective**: Add `rice-factor ci validate-artifacts` command.

**Implementation**:
- [x] Add command to `ci.py` command group
- [x] Wire up `ArtifactValidationAdapter` adapter
- [x] Add `--json` output option
- [x] Exit with code 1 on failure

**Acceptance Criteria**:
- [x] Command runs artifact validation
- [x] Output shows all failures

---

### T08-02-06: Write Unit Tests

**Objective**: Test artifact validation logic.

**Files Created**:
- [x] `tests/unit/adapters/ci/__init__.py`
- [x] `tests/unit/adapters/ci/test_artifact_validator.py`

**Test Cases** (17 tests):
- [x] Test valid artifact passes (approved)
- [x] Test draft artifact fails
- [x] Test schema invalid fails (invalid JSON, missing type, unknown type)
- [x] Test locked artifact passes (when not modified)
- [x] Test multiple failures reported
- [x] Test artifact discovery (nested, skips metadata, skips approvals)
- [x] Test duration tracking
- [x] Test base branch configuration

**Acceptance Criteria**:
- [x] All edge cases covered
- [x] Tests use fixtures for mock repos

---

## 3. Task Dependencies

```
T08-02-01 (Adapter) ──→ T08-02-02 (Schema) ──┐
                                              │
                       T08-02-03 (Draft) ────┼──→ T08-02-05 (CLI) ──→ T08-02-06 (Tests)
                                              │
                       T08-02-04 (Locked) ───┘
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T08-02-01 | Low | Adapter skeleton |
| T08-02-02 | Medium | Reuse existing validation |
| T08-02-03 | Low | Simple status check |
| T08-02-04 | Medium | Git integration |
| T08-02-05 | Low | CLI wiring |
| T08-02-06 | Medium | Fixture setup |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | All tasks complete - 17 tests passing |
