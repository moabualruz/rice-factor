# Feature F09-01: Drift Detection Service - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-01-01 | Create drift domain models | Pending | P0 |
| T09-01-02 | Implement DriftDetector port | Pending | P0 |
| T09-01-03 | Implement orphan code detection | Pending | P0 |
| T09-01-04 | Implement orphan plan detection | Pending | P0 |
| T09-01-05 | Implement refactor hotspot detection | Pending | P1 |
| T09-01-06 | Implement full analysis | Pending | P0 |
| T09-01-07 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T09-01-01: Create Drift Domain Models

**Objective**: Define core models for drift detection.

**Files to Create**:
- [ ] `rice_factor/domain/models/drift.py`

**Implementation**:
- [ ] Define `DriftSignalType` enum
- [ ] Define `DriftSeverity` enum
- [ ] Create `DriftSignal` dataclass
- [ ] Create `DriftReport` dataclass
- [ ] Add serialization methods (`to_dict`)

**Acceptance Criteria**:
- [ ] All 4 drift signal types defined
- [ ] Severity levels match spec
- [ ] Models are JSON-serializable

---

### T09-01-02: Implement DriftDetector Port

**Objective**: Define the drift detector port interface.

**Files to Create**:
- [ ] `rice_factor/domain/ports/drift.py`

**Implementation**:
```python
class DriftDetectorPort(Protocol):
    def detect_orphan_code(self, code_dir: Path) -> list[DriftSignal]: ...
    def detect_orphan_plans(self) -> list[DriftSignal]: ...
    def detect_undocumented_behavior(self) -> list[DriftSignal]: ...
    def detect_refactor_hotspots(self, threshold: int) -> list[DriftSignal]: ...
    def full_analysis(self, code_dir: Path) -> DriftReport: ...
```

**Acceptance Criteria**:
- [ ] Port follows hexagonal architecture
- [ ] All detection methods defined
- [ ] Protocol pattern used

---

### T09-01-03: Implement Orphan Code Detection

**Objective**: Detect code files not covered by any plan.

**Files to Create**:
- [ ] `rice_factor/domain/services/drift_detector.py`

**Implementation**:
- [ ] Scan code directory for source files
- [ ] Load all ImplementationPlan artifacts
- [ ] Extract target files from plans
- [ ] Compare and find uncovered files
- [ ] Create DriftSignal for each orphan

**Acceptance Criteria**:
- [ ] Finds all uncovered files
- [ ] Respects ignore patterns
- [ ] Includes file path in signal

---

### T09-01-04: Implement Orphan Plan Detection

**Objective**: Detect plans targeting non-existent files.

**Files to Modify**:
- [ ] `rice_factor/domain/services/drift_detector.py`

**Implementation**:
- [ ] Load all ImplementationPlan artifacts
- [ ] Check if each target file exists
- [ ] Create DriftSignal for missing targets
- [ ] Include artifact ID in signal

**Acceptance Criteria**:
- [ ] Detects all orphan plans
- [ ] Links signal to artifact ID
- [ ] Suggests archival action

---

### T09-01-05: Implement Refactor Hotspot Detection

**Objective**: Identify frequently refactored areas.

**Files to Modify**:
- [ ] `rice_factor/domain/services/drift_detector.py`

**Implementation**:
- [ ] Query audit log for refactor events
- [ ] Count refactors per file path
- [ ] Apply time window filter
- [ ] Create signals for hotspots

**Acceptance Criteria**:
- [ ] Uses audit log data
- [ ] Configurable threshold
- [ ] Configurable time window

---

### T09-01-06: Implement Full Analysis

**Objective**: Combine all detectors into single report.

**Files to Modify**:
- [ ] `rice_factor/domain/services/drift_detector.py`

**Implementation**:
- [ ] Call all detection methods
- [ ] Aggregate signals
- [ ] Build DriftReport
- [ ] Calculate threshold status

**Acceptance Criteria**:
- [ ] All 4 signal types included
- [ ] Report includes metadata
- [ ] Threshold correctly evaluated

---

### T09-01-07: Write Unit Tests

**Objective**: Test drift detection logic.

**Files to Create**:
- [ ] `tests/unit/domain/services/test_drift_detector.py`
- [ ] `tests/unit/domain/models/test_drift.py`

**Test Cases**:
- [ ] Orphan code detected correctly
- [ ] Orphan plans detected correctly
- [ ] Refactor hotspots detected
- [ ] Empty report when no drift
- [ ] Threshold evaluation works
- [ ] Signal serialization works

**Acceptance Criteria**:
- [ ] All detection scenarios covered
- [ ] Edge cases tested

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

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
