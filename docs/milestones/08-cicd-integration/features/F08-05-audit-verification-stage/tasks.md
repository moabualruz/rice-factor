# Feature F08-05: Audit Verification Stage - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-05-01 | Implement AuditVerifier adapter | Pending | P0 |
| T08-05-02 | Parse execution log | Pending | P0 |
| T08-05-03 | Detect orphaned code changes | Pending | P0 |
| T08-05-04 | Verify diff hashes | Pending | P1 |
| T08-05-05 | Add CLI command | Pending | P0 |
| T08-05-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T08-05-01: Implement AuditVerifier Adapter

**Objective**: Create the Stage 5 validator adapter.

**Files to Create**:
- [ ] `rice_factor/adapters/ci/audit_verifier.py`

**Implementation**:
- [ ] Create `AuditVerifier` class implementing `CIValidatorPort`
- [ ] Load audit directory structure
- [ ] Handle missing audit directory
- [ ] Return `CIStageResult` with failures

**Acceptance Criteria**:
- [ ] Implements CIValidatorPort protocol
- [ ] Handles missing audit gracefully

---

### T08-05-02: Parse Execution Log

**Objective**: Load and parse the execution audit log.

**Implementation**:
- [ ] Load `audit/executions.log` file
- [ ] Parse JSON log entries (one per line)
- [ ] Extract operation metadata (timestamp, executor, artifact, status)
- [ ] Create `MISSING_AUDIT_LOG` if file not found
- [ ] Handle malformed log entries

**Expected Log Format**:
```json
{"timestamp": "ISO-8601", "executor": "scaffold", "artifact_id": "uuid", "status": "applied", "diff_path": "audit/diffs/uuid.diff"}
```

**Acceptance Criteria**:
- [ ] Log is correctly parsed
- [ ] Malformed entries are reported but don't crash

---

### T08-05-03: Detect Orphaned Code Changes

**Objective**: Ensure all code changes have audit trail.

**Implementation**:
- [ ] Get list of commits in PR/branch
- [ ] For each commit, check if audit entry exists
- [ ] Create `ORPHANED_CODE_CHANGE` for commits without audit
- [ ] Include commit SHA and message in failure

**Pseudocode** (from spec 3.9):
```python
for commit in PR:
    ensure audit log exists
```

**Acceptance Criteria**:
- [ ] Commits without audit detected
- [ ] Provides clear remediation

---

### T08-05-04: Verify Diff Hashes

**Objective**: Ensure audit trail integrity.

**Implementation**:
- [ ] For each diff file in `audit/diffs/`
- [ ] Compute hash of diff content
- [ ] Compare with stored hash (if metadata exists)
- [ ] Create `AUDIT_INTEGRITY_VIOLATION` on mismatch
- [ ] Optional: store hashes in `audit/_meta/hashes.json`

**Acceptance Criteria**:
- [ ] Tampered diffs detected
- [ ] Hash algorithm is consistent (SHA-256)

---

### T08-05-05: Add CLI Command

**Objective**: Add `rice-factor ci validate-audit` command.

**Implementation**:
- [ ] Add command to `ci.py` command group
- [ ] Wire up `AuditVerifier` adapter
- [ ] Add `--json` output option
- [ ] Exit with code 1 on failure

**Acceptance Criteria**:
- [ ] Command runs audit verification
- [ ] Clear output for integrity issues

---

### T08-05-06: Write Unit Tests

**Objective**: Test audit verification logic.

**Files to Create**:
- [ ] `tests/unit/adapters/ci/test_audit_verifier.py`

**Test Cases**:
- [ ] Test complete audit trail passes
- [ ] Test missing audit log fails
- [ ] Test orphaned commit fails
- [ ] Test hash mismatch fails
- [ ] Test empty repository passes

**Acceptance Criteria**:
- [ ] All scenarios covered
- [ ] Fixtures for audit structures

---

## 3. Task Dependencies

```
T08-05-01 (Adapter) ──→ T08-05-02 (Parse Log) ──┬──→ T08-05-03 (Orphaned)
                                                 │
                                                 └──→ T08-05-04 (Hashes)
                                                              │
                                                              ↓
                                                   T08-05-05 (CLI)
                                                              │
                                                              ↓
                                                   T08-05-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T08-05-01 | Low | Adapter skeleton |
| T08-05-02 | Medium | Log parsing |
| T08-05-03 | Medium | Git commit analysis |
| T08-05-04 | Low | Hash computation |
| T08-05-05 | Low | CLI wiring |
| T08-05-06 | Medium | Fixture setup |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
