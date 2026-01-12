# Feature F09-01: Drift Detection Service - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-01-01 | Create drift domain models | **Complete** | P0 |
| T09-01-02 | Implement DriftDetector port | **Complete** | P0 |
| T09-01-03 | Implement orphan code detection | **Complete** | P0 |
| T09-01-04 | Implement orphan plan detection | **Complete** | P0 |
| T09-01-05 | Implement refactor hotspot detection | **Complete** | P1 |
| T09-01-06 | Implement full analysis | **Complete** | P0 |
| T09-01-07 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T09-01-01: Create Drift Domain Models

**Objective**: Define core models for drift detection.

**Files Created**:
- [x] `rice_factor/domain/drift/__init__.py`
- [x] `rice_factor/domain/drift/models.py`

**Implementation**:
- [x] Define `DriftSignalType` enum (4 types)
- [x] Define `DriftSeverity` enum (4 levels)
- [x] Create `DriftSignal` dataclass
- [x] Create `DriftReport` dataclass
- [x] Create `DriftConfig` dataclass
- [x] Add serialization methods (`to_dict`)

**Acceptance Criteria**:
- [x] All 4 drift signal types defined
- [x] Severity levels match spec
- [x] Models are JSON-serializable

---

### T09-01-02: Implement DriftDetector Port

**Objective**: Define the drift detector port interface.

**Files Created**:
- [x] `rice_factor/domain/ports/drift.py`

**Implementation**:
- [x] Create `DriftDetectorPort` protocol
- [x] Define `detect_orphan_code` method
- [x] Define `detect_orphan_plans` method
- [x] Define `detect_undocumented_behavior` method
- [x] Define `detect_refactor_hotspots` method
- [x] Define `full_analysis` method

**Acceptance Criteria**:
- [x] Port follows hexagonal architecture
- [x] All detection methods defined
- [x] Protocol pattern used

---

### T09-01-03: Implement Orphan Code Detection

**Objective**: Detect code files not covered by any plan.

**Files Created**:
- [x] `rice_factor/adapters/drift/__init__.py`
- [x] `rice_factor/adapters/drift/detector.py`

**Implementation**:
- [x] Scan code directory for source files
- [x] Load all ImplementationPlan artifacts
- [x] Extract target files from plans
- [x] Compare and find uncovered files
- [x] Create DriftSignal for each orphan
- [x] Respect ignore patterns (tests, __pycache__, etc.)

**Acceptance Criteria**:
- [x] Finds all uncovered files
- [x] Respects ignore patterns
- [x] Includes file path in signal

---

### T09-01-04: Implement Orphan Plan Detection

**Objective**: Detect plans targeting non-existent files.

**Implementation**:
- [x] Load all ImplementationPlan artifacts
- [x] Check if each target file exists
- [x] Load all RefactorPlan artifacts
- [x] Check from/to paths exist
- [x] Create DriftSignal for missing targets
- [x] Include artifact ID in signal

**Acceptance Criteria**:
- [x] Detects all orphan plans
- [x] Links signal to artifact ID
- [x] Suggests archival action

---

### T09-01-05: Implement Refactor Hotspot Detection

**Objective**: Identify frequently refactored areas.

**Implementation**:
- [x] Query audit log for refactor events
- [x] Count refactors per file path
- [x] Apply time window filter
- [x] Create signals for hotspots
- [x] Configurable threshold and window

**Acceptance Criteria**:
- [x] Uses audit log data
- [x] Configurable threshold
- [x] Configurable time window

---

### T09-01-06: Implement Full Analysis

**Objective**: Combine all detectors into single report.

**Implementation**:
- [x] Call all detection methods
- [x] Aggregate signals
- [x] Build DriftReport
- [x] Calculate threshold status
- [x] Track code files scanned and artifacts checked

**Acceptance Criteria**:
- [x] All signal types included (except undocumented behavior - deferred)
- [x] Report includes metadata
- [x] Threshold correctly evaluated

---

### T09-01-07: Write Unit Tests

**Objective**: Test drift detection logic.

**Files Created**:
- [x] `tests/unit/domain/drift/__init__.py`
- [x] `tests/unit/domain/drift/test_models.py` (17 tests)
- [x] `tests/unit/adapters/drift/__init__.py`
- [x] `tests/unit/adapters/drift/test_detector.py` (14 tests)

**Test Cases** (31 tests total):
- [x] Signal types and severity levels
- [x] DriftSignal creation and serialization
- [x] DriftReport properties and filters
- [x] Threshold evaluation
- [x] Critical signal handling
- [x] DriftConfig defaults and patterns
- [x] Orphan code detected correctly
- [x] Orphan plans detected correctly
- [x] Refactor hotspots detected
- [x] Empty report when no drift
- [x] Ignore patterns respected
- [x] Time window filtering

**Acceptance Criteria**:
- [x] All detection scenarios covered
- [x] Edge cases tested
- [x] 31 tests passing

---

## 3. Task Dependencies

```
T09-01-01 (Models) ──→ T09-01-02 (Port) ──→ T09-01-03 (Orphan Code)
                                                    │
                                                    ↓
                                           T09-01-04 (Orphan Plan)
                                                    │
                                                    ↓
                                           T09-01-05 (Hotspots)
                                                    │
                                                    ↓
                                           T09-01-06 (Full Analysis)
                                                    │
                                                    ↓
                                           T09-01-07 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T09-01-01 | Low | Model definitions |
| T09-01-02 | Low | Port interface |
| T09-01-03 | Medium | File scanning logic |
| T09-01-04 | Low | Plan checking |
| T09-01-05 | Medium | Audit log integration |
| T09-01-06 | Low | Aggregation |
| T09-01-07 | Medium | Many scenarios |

---

## 5. Notes

- **Undocumented Behavior Detection**: Complete. Implemented static analysis of test files:
  - Parses test function names and docstrings using Python AST
  - Extracts keywords from requirements.md (bullets, numbered lists, headers, feature IDs)
  - Flags tests that don't match any documented requirement
  - 8 additional tests added (total 35 tests)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | All tasks complete - 31 tests passing |
