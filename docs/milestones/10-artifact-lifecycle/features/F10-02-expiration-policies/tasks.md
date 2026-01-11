# Feature F10-02: Expiration Policies - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-02-01 | Create LifecyclePolicy model | Pending | P0 |
| T10-02-02 | Create PolicyResult model | Pending | P0 |
| T10-02-03 | Implement policy evaluation | Pending | P0 |
| T10-02-04 | Add YAML configuration loader | Pending | P1 |
| T10-02-05 | Define default policies | Pending | P0 |
| T10-02-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T10-02-01: Create LifecyclePolicy Model

**Objective**: Define policy structure for artifact types.

**Files to Create**:
- [ ] `rice_factor/domain/models/lifecycle.py`

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
- [ ] All policy fields defined
- [ ] Sensible defaults provided
- [ ] Dataclass is immutable-friendly

---

### T10-02-02: Create PolicyResult Model

**Objective**: Define evaluation result structure.

**Files to Modify**:
- [ ] `rice_factor/domain/models/lifecycle.py`

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
- [ ] All enums defined
- [ ] Result has helper properties
- [ ] Serializable to dict

---

### T10-02-03: Implement Policy Evaluation

**Objective**: Add evaluate method to policy.

**Files to Modify**:
- [ ] `rice_factor/domain/models/lifecycle.py`

**Implementation**:
```python
def evaluate(
    self,
    artifact: ArtifactEnvelope,
    violations: list | None = None,
    coverage_drift: float | None = None,
) -> PolicyResult:
    triggers = []
    urgency = ReviewUrgency.INFORMATIONAL

    # Check age
    if artifact.age_months >= self.review_after_months:
        triggers.append(ReviewTrigger.AGE)
        urgency = ReviewUrgency.REQUIRED
    elif self._in_warning_period(artifact):
        triggers.append(ReviewTrigger.AGE)
        urgency = ReviewUrgency.RECOMMENDED

    # Check violations
    if violations and self.mandatory_on_violation:
        triggers.append(ReviewTrigger.VIOLATION)
        urgency = ReviewUrgency.MANDATORY

    # Check coverage drift
    if coverage_drift and self.coverage_drift_threshold:
        if coverage_drift >= self.coverage_drift_threshold:
            triggers.append(ReviewTrigger.DRIFT)
            if urgency != ReviewUrgency.MANDATORY:
                urgency = ReviewUrgency.REQUIRED

    return PolicyResult(...)
```

**Acceptance Criteria**:
- [ ] Age triggers work correctly
- [ ] Violation triggers work
- [ ] Drift triggers work
- [ ] Urgency escalation correct

---

### T10-02-04: Add YAML Configuration Loader

**Objective**: Load policies from config file.

**Files to Create**:
- [ ] `rice_factor/config/lifecycle_config.py`

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

**Implementation**:
```python
@classmethod
def from_file(cls, path: Path) -> "LifecycleConfig":
    if not path.exists():
        return cls.default()

    import yaml
    with open(path) as f:
        data = yaml.safe_load(f)

    lifecycle_data = data.get("lifecycle", {})
    policies_data = lifecycle_data.get("policies", {})

    policies = {}
    for artifact_type, policy_data in policies_data.items():
        policies[artifact_type] = LifecyclePolicy(
            artifact_type=artifact_type,
            **policy_data,
        )

    return cls(policies=policies)
```

**Acceptance Criteria**:
- [ ] YAML parsed correctly
- [ ] Missing file uses defaults
- [ ] Partial config merged

---

### T10-02-05: Define Default Policies

**Objective**: Set reasonable defaults per spec.

**Files to Modify**:
- [ ] `rice_factor/config/lifecycle_config.py`

**Default Policies** (from spec 5.5.3):

| Artifact Type | Review After | Mandatory on Violation | Coverage Drift |
|---------------|--------------|----------------------|----------------|
| ProjectPlan | 3 months | No | - |
| ArchitecturePlan | 6 months | Yes | - |
| TestPlan | 3 months | No | 10% |
| ImplementationPlan | 6 months | No | - |

**Acceptance Criteria**:
- [ ] All artifact types have defaults
- [ ] Defaults match specification
- [ ] Config overrides work

---

### T10-02-06: Write Unit Tests

**Objective**: Test policy system.

**Files to Create**:
- [ ] `tests/unit/domain/models/test_lifecycle.py`
- [ ] `tests/unit/config/test_lifecycle_config.py`

**Test Cases**:
- [ ] Policy creation with defaults
- [ ] Policy evaluation - age trigger
- [ ] Policy evaluation - warning period
- [ ] Policy evaluation - violation trigger
- [ ] Policy evaluation - drift trigger
- [ ] Urgency escalation
- [ ] Config loading from YAML
- [ ] Config default fallback

**Acceptance Criteria**:
- [ ] All evaluation paths tested
- [ ] Config loading tested
- [ ] Edge cases covered

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
