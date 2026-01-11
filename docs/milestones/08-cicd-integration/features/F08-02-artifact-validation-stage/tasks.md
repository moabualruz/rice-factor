# Feature F08-02: Artifact Validation Stage - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-02-01 | Implement ArtifactValidator adapter | Pending | P0 |
| T08-02-02 | Add schema validation check | Pending | P0 |
| T08-02-03 | Add draft artifact detection | Pending | P0 |
| T08-02-04 | Add locked artifact change detection | Pending | P0 |
| T08-02-05 | Add CLI command | Pending | P0 |
| T08-02-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T08-02-01: Implement ArtifactValidator Adapter

**Objective**: Create the Stage 1 validator adapter.

**Files to Create**:
- [ ] `rice_factor/adapters/ci/__init__.py`
- [ ] `rice_factor/adapters/ci/artifact_validator.py`

**Implementation**:
- [ ] Create `ArtifactValidator` class implementing `CIValidatorPort`
- [ ] Implement artifact discovery (scan `artifacts/` directory)
- [ ] Skip metadata files (`_meta/`)
- [ ] Return `CIStageResult` with failures

**Acceptance Criteria**:
- [ ] Discovers all artifacts in repository
- [ ] Returns structured results

---

### T08-02-02: Add Schema Validation Check

**Objective**: Validate JSON Schema for all artifacts.

**Implementation**:
- [ ] Load artifact from JSON file
- [ ] Validate against appropriate schema using existing `ArtifactValidator`
- [ ] Create `SCHEMA_VALIDATION_FAILED` failure on error
- [ ] Include validation error details in failure

**Acceptance Criteria**:
- [ ] Invalid artifacts are detected
- [ ] Error message includes specific validation issue

---

### T08-02-03: Add Draft Artifact Detection

**Objective**: Detect and reject draft artifacts in CI.

**Implementation**:
- [ ] Check `status` field of each artifact
- [ ] Create `DRAFT_ARTIFACT_PRESENT` failure if status is "draft"
- [ ] Include artifact path and ID in failure

**Acceptance Criteria**:
- [ ] Draft artifacts cause CI failure
- [ ] Remediation guidance is actionable

---

### T08-02-04: Add Locked Artifact Change Detection

**Objective**: Detect modifications to locked artifacts.

**Implementation**:
- [ ] For artifacts with status "locked", check git history
- [ ] Use `git diff` to detect changes to locked artifact files
- [ ] Create `LOCKED_ARTIFACT_MODIFIED` failure on change
- [ ] Compare against base branch (for PRs)

**Acceptance Criteria**:
- [ ] Locked artifact modifications are detected
- [ ] Works in PR and push contexts

---

### T08-02-05: Add CLI Command

**Objective**: Add `rice-factor ci validate-artifacts` command.

**Implementation**:
- [ ] Add command to `ci.py` command group
- [ ] Wire up `ArtifactValidator` adapter
- [ ] Add `--json` output option
- [ ] Exit with code 1 on failure

**Acceptance Criteria**:
- [ ] Command runs artifact validation
- [ ] Output shows all failures

---

### T08-02-06: Write Unit Tests

**Objective**: Test artifact validation logic.

**Files to Create**:
- [ ] `tests/unit/adapters/ci/test_artifact_validator.py`

**Test Cases**:
- [ ] Test valid artifact passes
- [ ] Test draft artifact fails
- [ ] Test schema invalid fails
- [ ] Test locked artifact change fails
- [ ] Test multiple failures reported

**Acceptance Criteria**:
- [ ] All edge cases covered
- [ ] Tests use fixtures for mock repos

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
