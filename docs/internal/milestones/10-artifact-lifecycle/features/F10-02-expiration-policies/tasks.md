# Feature F10-02: Expiration Policies - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-02-01 | Create LifecyclePolicy model | Complete | P0 |
| T10-02-02 | Create PolicyResult model | Complete | P0 |
| T10-02-03 | Implement policy evaluation | Complete | P0 |
| T10-02-04 | Add YAML configuration loader | Complete | P1 |
| T10-02-05 | Define default policies | Complete | P0 |
| T10-02-06 | Write unit tests | Complete | P0 |

---

## 2. Task Details

### T10-02-01: Create LifecyclePolicy Model

**Objective**: Define policy structure for artifact types.

**Files Created**:
- [x] `rice_factor/domain/models/lifecycle.py`
- [x] `rice_factor/domain/models/__init__.py`

**Implementation**:
```python
@dataclass
class LifecyclePolicy:
    artifact_type: str
    review_after_months: int = 3
    warning_at_months: int | None = None
    mandatory_on_violation: bool = False
    coverage_drift_threshold: float | None = None
```

**Acceptance Criteria**:
- [x] All policy fields defined
- [x] Sensible defaults provided
- [x] Dataclass is immutable-friendly

---

### T10-02-02: Create PolicyResult Model

**Objective**: Define evaluation result structure.

**Files Modified**:
- [x] `rice_factor/domain/models/lifecycle.py`

**Implementation**:
```python
class ReviewTrigger(str, Enum):
    AGE = "age"
    VIOLATION = "violation"
    DRIFT = "drift"
    MANUAL = "manual"

class ReviewUrgency(str, Enum):
    INFORMATIONAL = "informational"
    RECOMMENDED = "recommended"
    REQUIRED = "required"
    MANDATORY = "mandatory"

@dataclass
class PolicyResult:
    artifact_id: str
    artifact_type: str
    triggers: list[ReviewTrigger]
    urgency: ReviewUrgency
    age_months: float
    violations: list
    coverage_drift: float | None

    @property
    def requires_action(self) -> bool: ...

    @property
    def blocks_work(self) -> bool: ...
```

**Acceptance Criteria**:
- [x] All enums defined
- [x] Result has helper properties
- [x] Serializable to dict via to_dict()

---

### T10-02-03: Implement Policy Evaluation

**Objective**: Add evaluate method to policy.

**Files Modified**:
- [x] `rice_factor/domain/models/lifecycle.py`

**Acceptance Criteria**:
- [x] Age triggers work correctly
- [x] Violation triggers work
- [x] Drift triggers work
- [x] Urgency escalation correct

---

### T10-02-04: Add YAML Configuration Loader

**Objective**: Load policies from config file.

**Files Modified**:
- [x] `rice_factor/domain/models/lifecycle.py` (LifecycleConfig.from_file)

Note: Placed in domain/models rather than config/ to keep all lifecycle logic together.

**Configuration Format**:
```yaml
lifecycle:
  policies:
    ProjectPlan:
      review_after_months: 3
      warning_at_months: 2
    ArchitecturePlan:
      review_after_months: 6
      mandatory_on_violation: true
```

**Acceptance Criteria**:
- [x] YAML parsed correctly
- [x] Missing file uses defaults
- [x] Partial config merged with defaults

---

### T10-02-05: Define Default Policies

**Objective**: Set reasonable defaults per spec.

**Files Modified**:
- [x] `rice_factor/domain/models/lifecycle.py` (DEFAULT_POLICIES)

**Default Policies** (from spec 5.5.3):

| Artifact Type | Review After | Mandatory on Violation | Coverage Drift |
|---------------|--------------|----------------------|----------------|
| ProjectPlan | 3 months | No | - |
| ArchitecturePlan | 6 months | Yes | - |
| TestPlan | 3 months | No | 10% |
| ImplementationPlan | 6 months | No | - |
| ScaffoldPlan | 6 months | No | - |
| RefactorPlan | 3 months | No | - |
| ValidationResult | 1 month | No | - |

**Acceptance Criteria**:
- [x] All artifact types have defaults
- [x] Defaults match specification
- [x] Config overrides work

---

### T10-02-06: Write Unit Tests

**Objective**: Test policy system.

**Files Created**:
- [x] `tests/unit/domain/models/__init__.py`
- [x] `tests/unit/domain/models/test_lifecycle.py`

**Test Cases** (41 tests):
- [x] Policy creation with defaults
- [x] Policy evaluation - age trigger
- [x] Policy evaluation - warning period
- [x] Policy evaluation - violation trigger
- [x] Policy evaluation - drift trigger
- [x] Urgency escalation
- [x] Config loading from YAML
- [x] Config default fallback
- [x] Edge cases (empty file, invalid YAML, partial config)

**Acceptance Criteria**:
- [x] All evaluation paths tested
- [x] Config loading tested
- [x] Edge cases covered

---

## 3. Task Dependencies

```
T10-02-01 (Policy) ──→ T10-02-02 (Result) ──→ T10-02-03 (Evaluate)
                                                     │
                                          ┌──────────┴──────────┐
                                          ↓                     ↓
                                  T10-02-04 (YAML)      T10-02-05 (Defaults)
                                          │                     │
                                          └──────────┬──────────┘
                                                     ↓
                                             T10-02-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T10-02-01 | Low | Dataclass |
| T10-02-02 | Low | Enums + dataclass |
| T10-02-03 | Medium | Evaluation logic |
| T10-02-04 | Low | YAML parsing |
| T10-02-05 | Low | Constants |
| T10-02-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.1.0 | 2026-01-11 | Implementation | All tasks completed |
