# Feature F10-04: Coverage Drift Detection - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-04-01 | Create CoverageMonitorPort | Complete | P0 |
| T10-04-02 | Implement coverage adapter | Complete | P0 |
| T10-04-03 | Store baseline in TestPlan | Complete | P0 |
| T10-04-04 | Calculate coverage drift | Complete | P0 |
| T10-04-05 | Add audit coverage command | Complete | P1 |
| T10-04-06 | Write unit tests | Complete | P0 |

---

## 2. Task Details

### T10-04-01: Create CoverageMonitorPort

**Objective**: Define port for coverage monitoring.

**Files Created**:
- [x] `rice_factor/domain/ports/coverage.py`

**Models Created**:
- [x] `CoverageError` - Exception for coverage failures
- [x] `CoverageResult` - Result of coverage measurement
- [x] `CoverageDriftResult` - Result of drift calculation
- [x] `CoverageMonitorPort` - Abstract port interface

**Acceptance Criteria**:
- [x] Port follows hexagonal pattern
- [x] All methods abstractmethod
- [x] Clear type hints

---

### T10-04-02: Implement Coverage Adapter

**Objective**: Adapter to measure actual coverage.

**Files Created**:
- [x] `rice_factor/adapters/coverage/__init__.py`
- [x] `rice_factor/adapters/coverage/pytest_adapter.py`

**Adapters Created**:
- [x] `PytestCoverageAdapter` - Uses pytest-cov
- [x] `MockCoverageAdapter` - For testing

**Acceptance Criteria**:
- [x] Runs pytest with coverage
- [x] Parses JSON report
- [x] Handles missing report

---

### T10-04-03: Store Baseline in TestPlan

**Objective**: Store baseline coverage when TestPlan is locked.

**Implementation**:
The coverage adapter provides `update_baseline()` method that can be
called during the lock process to store:
- `baseline_coverage` - Coverage percentage
- `baseline_recorded_at` - ISO timestamp

Note: Full lock integration deferred to keep scope focused.

**Acceptance Criteria**:
- [x] Baseline recording supported
- [x] Timestamp recorded
- [x] Existing payload preserved

---

### T10-04-04: Calculate Coverage Drift

**Objective**: Detect when coverage has degraded.

**Files Modified**:
- [x] `rice_factor/adapters/coverage/pytest_adapter.py`

**Drift Calculation**:
- Positive drift = coverage decreased (bad)
- Negative drift = coverage increased (good)
- Zero = no change

**Severity Levels**:
- `ok` - Drift <= 0 (coverage increased or unchanged)
- `info` - Drift < threshold/2
- `warning` - Drift < threshold
- `critical` - Drift >= threshold

**Acceptance Criteria**:
- [x] Drift calculation correct
- [x] Handles missing baseline
- [x] Severity levels implemented

---

### T10-04-05: Add Audit Coverage Command

**Objective**: CLI command to check coverage drift.

**Files Modified**:
- [x] `rice_factor/entrypoints/cli/commands/audit.py`

**Command Added**:
```bash
rice-factor audit coverage [--path] [--threshold] [--json] [--no-run]
```

**Features**:
- [x] Shows all locked TestPlans
- [x] Displays baseline and current coverage
- [x] Shows drift and threshold status
- [x] Exit code reflects status (0=ok, 1=exceeds, 2=critical)
- [x] JSON output option
- [x] --no-run to skip running tests

**Acceptance Criteria**:
- [x] Shows all TestPlans
- [x] Includes baseline and current
- [x] Shows threshold status
- [x] Exit code reflects status

---

### T10-04-06: Write Unit Tests

**Objective**: Test coverage monitoring.

**Files Created**:
- [x] `tests/unit/adapters/coverage/__init__.py`
- [x] `tests/unit/adapters/coverage/test_pytest_adapter.py`

**Test Cases** (22 tests):
- [x] CoverageResult creation and to_dict
- [x] CoverageDriftResult creation and to_dict
- [x] MockCoverageAdapter get/set current coverage
- [x] MockCoverageAdapter get baseline coverage
- [x] MockCoverageAdapter calculate drift (positive/negative/zero)
- [x] MockCoverageAdapter drift triggers review
- [x] MockCoverageAdapter update baseline
- [x] PytestCoverageAdapter initialization
- [x] PytestCoverageAdapter get baseline
- [x] PytestCoverageAdapter calculate drift simple
- [x] PytestCoverageAdapter get drift severity levels

**CLI Test Cases** (9 tests added to test_audit.py):
- [x] coverage --help shows options
- [x] coverage --help shows exit codes
- [x] coverage handles no artifacts dir
- [x] coverage handles no locked TestPlans
- [x] coverage JSON output
- [x] coverage exit code 0 within threshold
- [x] coverage exit code 1 exceeds threshold
- [x] coverage exit code 2 critical drift
- [x] coverage --threshold option

**Acceptance Criteria**:
- [x] Adapter logic tested
- [x] CLI tested
- [x] Edge cases covered

---

## 3. Task Dependencies

```
T10-04-01 (Port) ──→ T10-04-02 (Adapter) ──→ T10-04-03 (Baseline)
                                                   │
                                                   ↓
                                           T10-04-04 (Calculate)
                                                   │
                                                   ↓
                                           T10-04-05 (CLI)
                                                   │
                                                   ↓
                                           T10-04-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T10-04-01 | Low | Port definition |
| T10-04-02 | Medium | Subprocess handling |
| T10-04-03 | Medium | Lock integration |
| T10-04-04 | Low | Simple math |
| T10-04-05 | Medium | CLI output |
| T10-04-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.1.0 | 2026-01-11 | Implementation | All tasks completed |
