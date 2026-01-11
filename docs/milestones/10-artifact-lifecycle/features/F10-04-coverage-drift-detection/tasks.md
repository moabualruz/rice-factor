# Feature F10-04: Coverage Drift Detection - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-04-01 | Create CoverageMonitorPort | Pending | P0 |
| T10-04-02 | Implement coverage adapter | Pending | P0 |
| T10-04-03 | Store baseline in TestPlan | Pending | P0 |
| T10-04-04 | Calculate coverage drift | Pending | P0 |
| T10-04-05 | Add audit coverage command | Pending | P1 |
| T10-04-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T10-04-01: Create CoverageMonitorPort

**Objective**: Define port for coverage monitoring.

**Files to Create**:
- [ ] `rice_factor/domain/ports/coverage.py`

**Implementation**:
```python
from abc import ABC, abstractmethod


class CoverageMonitorPort(ABC):
    """Port for test coverage monitoring."""

    @abstractmethod
    def get_current_coverage(self) -> float:
        """Get current test coverage percentage."""
        ...

    @abstractmethod
    def get_baseline_coverage(
        self,
        test_plan: ArtifactEnvelope,
    ) -> float:
        """Get baseline coverage from TestPlan."""
        ...

    @abstractmethod
    def calculate_drift(
        self,
        test_plan: ArtifactEnvelope,
    ) -> float:
        """Calculate coverage drift (baseline - current)."""
        ...

    @abstractmethod
    def update_baseline(
        self,
        test_plan: ArtifactEnvelope,
        coverage: float,
    ) -> None:
        """Update baseline coverage in TestPlan."""
        ...
```

**Acceptance Criteria**:
- [ ] Port follows hexagonal pattern
- [ ] All methods abstractmethod
- [ ] Clear type hints

---

### T10-04-02: Implement Coverage Adapter

**Objective**: Adapter to measure actual coverage.

**Files to Create**:
- [ ] `rice_factor/adapters/coverage/pytest_adapter.py`

**Implementation**:
```python
import subprocess
import json
from pathlib import Path


class PytestCoverageAdapter:
    """Coverage adapter using pytest-cov."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.coverage_file = project_root / "coverage.json"

    def get_current_coverage(self) -> float:
        """Run tests with coverage and return percentage."""
        result = subprocess.run(
            [
                "pytest",
                "--cov=rice_factor",
                "--cov-report=json",
                "-q",
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        if not self.coverage_file.exists():
            raise CoverageError("Coverage report not generated")

        with open(self.coverage_file) as f:
            data = json.load(f)

        return data["totals"]["percent_covered"]

    def get_baseline_coverage(
        self,
        test_plan: ArtifactEnvelope,
    ) -> float:
        """Extract baseline from TestPlan payload."""
        return test_plan.payload.get("baseline_coverage", 0.0)

    def calculate_drift(
        self,
        test_plan: ArtifactEnvelope,
    ) -> float:
        """Calculate drift: positive = coverage decreased."""
        baseline = self.get_baseline_coverage(test_plan)
        current = self.get_current_coverage()
        return baseline - current
```

**Acceptance Criteria**:
- [ ] Runs pytest with coverage
- [ ] Parses JSON report
- [ ] Handles missing report

---

### T10-04-03: Store Baseline in TestPlan

**Objective**: Store baseline coverage when TestPlan is locked.

**Files to Modify**:
- [ ] `rice_factor/domain/artifacts/test_plan.py`
- [ ] `rice_factor/domain/services/artifact_service.py`

**TestPlan Payload Extension**:
```python
class TestPlanPayload:
    # Existing fields...

    # Coverage tracking
    baseline_coverage: float | None = None
    baseline_recorded_at: datetime | None = None
```

**Lock Behavior**:
```python
def lock_tests(self, test_plan_id: str) -> None:
    test_plan = self.storage.load(test_plan_id)

    # Record baseline coverage when locking
    coverage = self.coverage_monitor.get_current_coverage()
    test_plan.payload["baseline_coverage"] = coverage
    test_plan.payload["baseline_recorded_at"] = datetime.now().isoformat()

    test_plan.status = ArtifactStatus.LOCKED
    self.storage.save(test_plan)
```

**Acceptance Criteria**:
- [ ] Baseline recorded on lock
- [ ] Timestamp recorded
- [ ] Existing payload preserved

---

### T10-04-04: Calculate Coverage Drift

**Objective**: Detect when coverage has degraded.

**Files to Modify**:
- [ ] `rice_factor/adapters/coverage/pytest_adapter.py`
- [ ] `rice_factor/domain/services/lifecycle_service.py`

**Drift Calculation**:
```python
def calculate_drift(
    self,
    test_plan: ArtifactEnvelope,
) -> float:
    """
    Calculate coverage drift.

    Returns:
        Positive value = coverage decreased (bad)
        Negative value = coverage increased (good)
        Zero = no change
    """
    baseline = self.get_baseline_coverage(test_plan)
    if baseline == 0:
        return 0.0  # No baseline to compare

    current = self.get_current_coverage()
    return baseline - current
```

**Integration with LifecycleService**:
```python
def evaluate_all(self) -> list[PolicyResult]:
    for artifact in self.artifact_store.list_all():
        # ...
        if artifact.artifact_type == "TestPlan" and self.coverage_monitor:
            coverage_drift = self.coverage_monitor.calculate_drift(artifact)
        # ...
```

**Acceptance Criteria**:
- [ ] Drift calculation correct
- [ ] Handles missing baseline
- [ ] Integrates with lifecycle

---

### T10-04-05: Add Audit Coverage Command

**Objective**: CLI command to check coverage drift.

**Files to Create/Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/audit.py`

**Command**:
```bash
rice-factor audit coverage [--json]
```

**Output**:
```
Coverage Drift Report
=====================

TestPlan: test-plan-001
  Baseline: 95.0% (recorded 2025-10-01)
  Current: 87.5%
  Drift: -7.5%
  Threshold: 10%
  Status: OK (within threshold)

TestPlan: test-plan-002
  Baseline: 90.0% (recorded 2025-09-15)
  Current: 75.2%
  Drift: -14.8%
  Threshold: 10%
  Status: EXCEEDS THRESHOLD

Summary: 1 of 2 TestPlans exceed drift threshold
```

**Acceptance Criteria**:
- [ ] Shows all TestPlans
- [ ] Includes baseline and current
- [ ] Shows threshold status
- [ ] Exit code reflects status

---

### T10-04-06: Write Unit Tests

**Objective**: Test coverage monitoring.

**Files to Create**:
- [ ] `tests/unit/adapters/coverage/test_pytest_adapter.py`
- [ ] `tests/unit/domain/services/test_coverage_integration.py`

**Test Cases**:
- [ ] Get current coverage
- [ ] Get baseline from TestPlan
- [ ] Calculate positive drift
- [ ] Calculate negative drift
- [ ] Calculate zero drift
- [ ] Missing baseline handling
- [ ] Drift triggers policy

**Acceptance Criteria**:
- [ ] Adapter logic tested
- [ ] Integration tested
- [ ] Edge cases covered

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
