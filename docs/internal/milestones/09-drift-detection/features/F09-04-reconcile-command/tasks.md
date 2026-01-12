# Feature F09-04: Reconcile Command - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-04-01 | Create ReconciliationService | **Complete** | P0 |
| T09-04-02 | Implement signal-to-step mapping | **Complete** | P0 |
| T09-04-03 | Add reconcile CLI command | **Complete** | P0 |
| T09-04-04 | Implement work freeze check | **Complete** | P1 |
| T09-04-05 | Add approval integration | Deferred | P0 |
| T09-04-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T09-04-01: Create ReconciliationService

**Objective**: Create service for generating reconciliation plans.

**Files Created**:
- [x] `rice_factor/domain/services/reconciliation_service.py`

**Implementation**:
- [x] ReconciliationService class
- [x] generate_plan() method
- [x] save_plan() method
- [x] Signal-to-step conversion
- [x] Priority calculation based on severity

**Acceptance Criteria**:
- [x] Service follows domain patterns
- [x] Generates valid artifact
- [x] Exports via services __init__.py

---

### T09-04-02: Implement Signal-to-Step Mapping

**Objective**: Convert drift signals to reconciliation steps.

**Mapping Rules**:
| Signal Type | Action |
|-------------|--------|
| ORPHAN_CODE | CREATE_ARTIFACT |
| ORPHAN_PLAN | ARCHIVE_ARTIFACT |
| UNDOCUMENTED_BEHAVIOR | UPDATE_REQUIREMENTS |
| REFACTOR_HOTSPOT | REVIEW_CODE |

**Implementation**:
- [x] SIGNAL_ACTION_MAP constant
- [x] _signal_to_step() method
- [x] Priority sorting by severity (CRITICAL > HIGH > MEDIUM > LOW)
- [x] Sequential priority renumbering

**Acceptance Criteria**:
- [x] All signal types mapped
- [x] Priority assigned correctly
- [x] Reason included from signal

---

### T09-04-03: Add Reconcile CLI Command

**Objective**: Implement `rice-factor reconcile` command.

**Files Created**:
- [x] `rice_factor/entrypoints/cli/commands/reconcile.py`

**Files Modified**:
- [x] `rice_factor/entrypoints/cli/main.py`
- [x] `rice_factor/entrypoints/cli/commands/__init__.py`

**Options**:
- [x] `--path` - Project root path
- [x] `--code-dir` - Code directory to scan
- [x] `--threshold` - Drift threshold
- [x] `--no-freeze` - Disable work freeze
- [x] `--dry-run` - Preview without saving
- [x] `--json` - JSON output

**Acceptance Criteria**:
- [x] Generates plan from drift
- [x] Shows human-readable output
- [x] Saves artifact to disk

---

### T09-04-04: Implement Work Freeze Check

**Objective**: Block new work when reconciliation pending.

**Implementation**:
- [x] `check_work_freeze()` function in reconciliation_service.py
- [x] Checks for draft ReconciliationPlan with freeze_new_work=True
- [x] Returns (is_frozen, artifact_id) tuple

**Acceptance Criteria**:
- [x] Freeze blocks when draft plan exists
- [x] Approved plans don't block
- [x] Function exported from services

---

### T09-04-05: Add Approval Integration

**Status**: Deferred

**Rationale**: The existing approve command already handles ReconciliationPlan artifacts since it's registered as a valid artifact type. Full integration with work freeze unblocking can be added in a future iteration.

---

### T09-04-06: Write Unit Tests

**Objective**: Test reconciliation service and command.

**Files Created**:
- [x] `tests/unit/domain/services/test_reconciliation_service.py` (19 tests)
- [x] `tests/unit/entrypoints/cli/commands/test_reconcile.py` (11 tests)

**Test Cases** (30 total):
- Signal action mapping (4 tests)
- ReconciliationService.generate_plan (8 tests)
- ReconciliationService.save_plan (2 tests)
- check_work_freeze (5 tests)
- CLI help and options (2 tests)
- No drift scenarios (2 tests)
- Below threshold scenarios (2 tests)
- Plan generation scenarios (4 tests)
- Threshold option (1 test)

**Acceptance Criteria**:
- [x] Service logic tested
- [x] CLI integration tested
- [x] Freeze behavior tested
- [x] 30 tests passing

---

## 3. Task Dependencies

```
T09-04-01 (Service) ──→ T09-04-02 (Mapping) ──→ T09-04-03 (CLI)
                                                      │
                                           ┌──────────┴──────────┐
                                           ↓                     ↓
                                   T09-04-04 (Freeze)    T09-04-05 (Approval)
                                           │                     │ [Deferred]
                                           └──────────┬──────────┘
                                                      ↓
                                              T09-04-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T09-04-01 | Medium | Service design |
| T09-04-02 | Low | Mapping logic |
| T09-04-03 | Medium | CLI implementation |
| T09-04-04 | Low | Check function |
| T09-04-05 | Low | Deferred |
| T09-04-06 | Medium | Multiple scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | Core tasks complete - 30 tests passing, T09-04-05 deferred |
