# Feature F08-03: Approval Verification Stage - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-03-01 | Implement ApprovalVerifier adapter | Pending | P0 |
| T08-03-02 | Load approvals metadata | Pending | P0 |
| T08-03-03 | Cross-check artifact IDs | Pending | P0 |
| T08-03-04 | Add CLI command | Pending | P0 |
| T08-03-05 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T08-03-01: Implement ApprovalVerifier Adapter

**Objective**: Create the Stage 2 validator adapter.

**Files to Create**:
- [ ] `rice_factor/adapters/ci/approval_verifier.py`

**Implementation**:
- [ ] Create `ApprovalVerifier` class implementing `CIValidatorPort`
- [ ] Load `artifacts/_meta/approvals.json`
- [ ] Handle missing metadata file
- [ ] Return `CIStageResult` with failures

**Acceptance Criteria**:
- [ ] Implements CIValidatorPort protocol
- [ ] Handles edge cases gracefully

---

### T08-03-02: Load Approvals Metadata

**Objective**: Parse and validate approvals.json.

**Implementation**:
- [ ] Load JSON from `artifacts/_meta/approvals.json`
- [ ] Validate structure matches expected schema
- [ ] Create `APPROVAL_METADATA_MISSING` if file not found
- [ ] Extract approved artifact IDs into a set

**Expected Schema**:
```json
{
  "approvals": [
    {
      "artifact_id": "uuid",
      "approved_by": "human",
      "approved_at": "ISO-8601",
      "status": "approved"
    }
  ]
}
```

**Acceptance Criteria**:
- [ ] Metadata is correctly parsed
- [ ] Missing file is handled

---

### T08-03-03: Cross-Check Artifact IDs

**Objective**: Verify all artifacts have approval entries.

**Implementation**:
- [ ] Load all artifacts from repository
- [ ] Extract artifact IDs
- [ ] Compare against approved IDs set
- [ ] Create `ARTIFACT_NOT_APPROVED` for each missing approval
- [ ] Include artifact type and path in failure

**Acceptance Criteria**:
- [ ] All unapproved artifacts detected
- [ ] Failure includes remediation command

---

### T08-03-04: Add CLI Command

**Objective**: Add `rice-factor ci validate-approvals` command.

**Implementation**:
- [ ] Add command to `ci.py` command group
- [ ] Wire up `ApprovalVerifier` adapter
- [ ] Add `--json` output option
- [ ] Exit with code 1 on failure

**Acceptance Criteria**:
- [ ] Command runs approval verification
- [ ] Lists all unapproved artifacts

---

### T08-03-05: Write Unit Tests

**Objective**: Test approval verification logic.

**Files to Create**:
- [ ] `tests/unit/adapters/ci/test_approval_verifier.py`

**Test Cases**:
- [ ] Test all approved passes
- [ ] Test missing approval fails
- [ ] Test missing metadata file fails
- [ ] Test partial approval fails
- [ ] Test empty repository passes

**Acceptance Criteria**:
- [ ] All scenarios covered
- [ ] Fixtures for various states

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
