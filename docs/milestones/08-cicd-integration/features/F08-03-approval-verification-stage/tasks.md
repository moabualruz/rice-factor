# Feature F08-03: Approval Verification Stage - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-03-01 | Implement ApprovalVerifier adapter | **Complete** | P0 |
| T08-03-02 | Load approvals metadata | **Complete** | P0 |
| T08-03-03 | Cross-check artifact IDs | **Complete** | P0 |
| T08-03-04 | Add CLI command | **Complete** | P0 |
| T08-03-05 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T08-03-01: Implement ApprovalVerifier Adapter

**Objective**: Create the Stage 2 validator adapter.

**Files Created**:
- [x] `rice_factor/adapters/ci/approval_verifier.py`

**Implementation**:
- [x] Create `ApprovalVerificationAdapter` class implementing `CIValidatorPort`
- [x] Load `artifacts/_meta/approvals.json`
- [x] Handle missing metadata file
- [x] Return `CIStageResult` with failures

**Acceptance Criteria**:
- [x] Implements CIValidatorPort protocol
- [x] Handles edge cases gracefully

---

### T08-03-02: Load Approvals Metadata

**Objective**: Parse and validate approvals.json.

**Implementation**:
- [x] Load JSON from `artifacts/_meta/approvals.json`
- [x] Validate structure matches expected schema
- [x] Create `APPROVAL_METADATA_MISSING` if file corrupted
- [x] Extract approved artifact IDs into a set

**Expected Schema**:
```json
{
  "approvals": [
    {
      "artifact_id": "uuid",
      "approved_by": "human",
      "approved_at": "ISO-8601"
    }
  ]
}
```

**Acceptance Criteria**:
- [x] Metadata is correctly parsed
- [x] Missing/corrupted file is handled

---

### T08-03-03: Cross-Check Artifact IDs

**Objective**: Verify all artifacts have approval entries.

**Implementation**:
- [x] Load all artifacts from repository
- [x] Extract artifact IDs
- [x] Compare against approved IDs set
- [x] Create `ARTIFACT_NOT_APPROVED` for each missing approval
- [x] Include artifact type and path in failure
- [x] Skip draft artifacts (don't need approval)

**Acceptance Criteria**:
- [x] All unapproved artifacts detected
- [x] Failure includes remediation command

---

### T08-03-04: Add CLI Command

**Objective**: Add `rice-factor ci validate-approvals` command.

**Implementation**:
- [x] Add command to `ci.py` command group
- [x] Wire up `ApprovalVerificationAdapter` adapter
- [x] Add `--json` output option
- [x] Exit with code 1 on failure

**Acceptance Criteria**:
- [x] Command runs approval verification
- [x] Lists all unapproved artifacts

---

### T08-03-05: Write Unit Tests

**Objective**: Test approval verification logic.

**Files Created**:
- [x] `tests/unit/adapters/ci/test_approval_verifier.py`

**Test Cases** (15 tests):
- [x] Test all approved passes
- [x] Test missing approval fails
- [x] Test missing metadata file handled
- [x] Test invalid metadata JSON fails
- [x] Test partial approval fails
- [x] Test empty repository passes
- [x] Test draft artifacts skipped
- [x] Test locked artifacts need approval
- [x] Test skips metadata and approval files

**Acceptance Criteria**:
- [x] All scenarios covered
- [x] Fixtures for various states

---

## 3. Task Dependencies

```
T08-03-01 (Adapter) ──→ T08-03-02 (Load) ──→ T08-03-03 (Cross-check)
                                                        │
                                                        ↓
                                            T08-03-04 (CLI) ──→ T08-03-05 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T08-03-01 | Low | Adapter skeleton |
| T08-03-02 | Low | JSON parsing |
| T08-03-03 | Medium | Set comparison logic |
| T08-03-04 | Low | CLI wiring |
| T08-03-05 | Medium | Multiple test scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | All tasks complete - 15 tests passing |
