# Feature F08-05: Audit Verification Stage - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T08-05-01 | Implement AuditVerifier adapter | **Complete** | P0 |
| T08-05-02 | Parse execution log | **Complete** | P0 |
| T08-05-03 | Detect orphaned code changes | Deferred | P0 |
| T08-05-04 | Verify diff hashes | **Complete** | P1 |
| T08-05-05 | Add CLI command | **Complete** | P0 |
| T08-05-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T08-05-01: Implement AuditVerifier Adapter

**Objective**: Create the Stage 5 validator adapter.

**Files Created**:
- [x] `rice_factor/adapters/ci/audit_verifier.py`

**Implementation**:
- [x] Create `AuditVerificationAdapter` class implementing `CIValidatorPort`
- [x] Load audit directory structure
- [x] Handle missing audit directory
- [x] Return `CIStageResult` with failures

**Acceptance Criteria**:
- [x] Implements CIValidatorPort protocol
- [x] Handles missing audit gracefully

---

### T08-05-02: Parse Execution Log

**Objective**: Load and parse the execution audit log.

**Implementation**:
- [x] Load `audit/executions.log` file
- [x] Parse JSON log entries (one per line)
- [x] Extract operation metadata (timestamp, executor, artifact, status)
- [x] Detect malformed entries and report as AUDIT_INTEGRITY_VIOLATION
- [x] Handle empty/missing log file gracefully

**Expected Log Format**:
```json
{"timestamp": "ISO-8601", "executor": "scaffold", "artifact": "...", "status": "success", "diff": "audit/diffs/..."}
```

**Acceptance Criteria**:
- [x] Log is correctly parsed
- [x] Malformed entries are reported but don't crash

---

### T08-05-03: Detect Orphaned Code Changes

**Status**: Deferred

**Rationale**: This requires git commit-level analysis to correlate commits with audit entries. The current implementation focuses on audit log and diff integrity. Orphaned code detection can be added when a more comprehensive git integration is needed.

---

### T08-05-04: Verify Diff Hashes

**Objective**: Ensure audit trail integrity.

**Implementation**:
- [x] For each diff file referenced in audit log, verify it exists
- [x] If `audit/_meta/hashes.json` exists, verify SHA-256 hashes
- [x] Create `AUDIT_HASH_CHAIN_BROKEN` on mismatch
- [x] Configurable via `verify_hashes` parameter

**Acceptance Criteria**:
- [x] Tampered diffs detected
- [x] Hash algorithm is SHA-256

---

### T08-05-05: Add CLI Command

**Objective**: Add `rice-factor ci validate-audit` command.

**Implementation**:
- [x] Add command to `ci.py` command group (already existed)
- [x] Wire up `AuditVerificationAdapter` adapter
- [x] Add `--json` output option
- [x] Exit with code 1 on failure

**Acceptance Criteria**:
- [x] Command runs audit verification
- [x] Clear output for integrity issues

---

### T08-05-06: Write Unit Tests

**Objective**: Test audit verification logic.

**Files Created**:
- [x] `tests/unit/adapters/ci/test_audit_verifier.py`

**Test Cases** (15 tests):
- [x] Test valid audit log passes
- [x] Test malformed entry fails
- [x] Test missing required fields fails
- [x] Test existing diff file passes
- [x] Test missing diff file fails
- [x] Test entry without diff passes
- [x] Test valid hashes pass
- [x] Test hash mismatch fails
- [x] Test no hash file passes
- [x] Test hash verification disabled
- [x] Test reports all failures
- [x] Test duration tracking

**Acceptance Criteria**:
- [x] All scenarios covered
- [x] Fixtures for audit structures

---

## 3. Task Dependencies

```
T08-05-01 (Adapter) ──→ T08-05-02 (Parse Log) ──┬──→ T08-05-03 (Orphaned) [Deferred]
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
| T08-05-03 | Medium | Deferred |
| T08-05-04 | Low | Hash computation |
| T08-05-05 | Low | CLI wiring |
| T08-05-06 | Medium | Fixture setup |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | Core tasks complete - 15 tests passing, T08-05-03 deferred |
