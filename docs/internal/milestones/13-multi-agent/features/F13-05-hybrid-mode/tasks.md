# Feature F13-05: Hybrid Mode - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T13-05-01 | Implement HybridMode coordinator | Complete | P0 |
| T13-05-02 | Define phase detection | Complete | P0 |
| T13-05-03 | Create mode-per-phase routing | Complete | P0 |
| T13-05-04 | Add phase transition handling | Complete | P1 |
| T13-05-05 | Implement context preservation | Complete | P1 |
| T13-05-06 | Write unit tests | Complete | P0 |

---

## 2. Task Details

### T13-05-01: Implement HybridMode Coordinator

**Objective**: Create hybrid mode coordinator.

**Files to Create**:
- [x] `rice_factor/adapters/agents/hybrid_mode.py`

**Implementation**:
```python
class HybridMode(CoordinatorPort):
    def __init__(
        self,
        phase_modes: dict[str, RunMode],
        mode_coordinators: dict[RunMode, CoordinatorPort],
    ) -> None:
        self.phase_modes = phase_modes
        self.mode_coordinators = mode_coordinators

    async def coordinate(
        self,
        task: str,
        context: dict,
    ) -> CoordinationResult:
        phase = self._detect_phase(task)
        mode = self.phase_modes.get(phase, RunMode.SOLO)
        coordinator = self.mode_coordinators[mode]

        return await coordinator.coordinate(task, context)

    def get_active_agents(self) -> list[Agent]:
        # Return agents from all mode coordinators
        agents = []
        for coord in self.mode_coordinators.values():
            agents.extend(coord.get_active_agents())
        return list(set(agents))  # Deduplicate
```

**Acceptance Criteria**:
- [x] Routes to correct mode
- [x] All coordinators available
- [x] Fallback to solo

---

### T13-05-02: Define Phase Detection

**Objective**: Detect which phase task belongs to.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/hybrid_mode.py`

**Phases**:
| Phase | Task Keywords |
|-------|--------------|
| planning | plan, design, architect |
| implementation | implement, code, scaffold |
| testing | test, verify, validate |
| review | review, approve, check |
| refactoring | refactor, restructure, move |

**Implementation**:
```python
PHASE_KEYWORDS = {
    "planning": ["plan", "design", "architect", "project"],
    "implementation": ["implement", "code", "scaffold", "build"],
    "testing": ["test", "verify", "validate", "check"],
    "review": ["review", "approve", "inspect"],
    "refactoring": ["refactor", "restructure", "rename", "move"],
}

def _detect_phase(self, task: str) -> str:
    task_lower = task.lower()

    for phase, keywords in self.PHASE_KEYWORDS.items():
        if any(kw in task_lower for kw in keywords):
            return phase

    return "default"
```

**Acceptance Criteria**:
- [x] Keywords detected
- [x] Default phase defined
- [x] Case insensitive

---

### T13-05-03: Create Mode-Per-Phase Routing

**Objective**: Route to different modes per phase.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/hybrid_mode.py`

**Configuration Example**:
```yaml
mode: hybrid

phases:
  planning: orchestrator
  implementation: solo
  testing: role_locked
  review: voting
  refactoring: orchestrator
  default: solo
```

**Implementation**:
```python
def _get_coordinator_for_phase(
    self,
    phase: str,
) -> CoordinatorPort:
    mode = self.phase_modes.get(phase)

    if mode is None:
        mode = self.phase_modes.get("default", RunMode.SOLO)

    coordinator = self.mode_coordinators.get(mode)

    if coordinator is None:
        # Fallback to solo mode
        coordinator = self.mode_coordinators[RunMode.SOLO]

    return coordinator
```

**Acceptance Criteria**:
- [x] Phase-to-mode mapping works
- [x] Default fallback
- [x] All modes supported

---

### T13-05-04: Add Phase Transition Handling

**Objective**: Handle transitions between phases.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/hybrid_mode.py`

**Transition Events**:
- Before phase: Log transition, prepare context
- After phase: Store results, update state
- On failure: Handle rollback

**Implementation**:
```python
async def coordinate(
    self,
    task: str,
    context: dict,
) -> CoordinationResult:
    phase = self._detect_phase(task)

    # Pre-transition hook
    await self._on_phase_enter(phase, context)

    try:
        coordinator = self._get_coordinator_for_phase(phase)
        result = await coordinator.coordinate(task, context)

        # Post-transition hook
        await self._on_phase_exit(phase, result)

        return result

    except Exception as e:
        await self._on_phase_error(phase, e)
        raise

async def _on_phase_enter(
    self,
    phase: str,
    context: dict,
) -> None:
    """Called before entering a phase."""
    self.audit_logger.log(f"Entering phase: {phase}")
    self.current_phase = phase

async def _on_phase_exit(
    self,
    phase: str,
    result: CoordinationResult,
) -> None:
    """Called after completing a phase."""
    self.audit_logger.log(f"Completed phase: {phase}")
    self.phase_results[phase] = result
```

**Acceptance Criteria**:
- [x] Transitions logged
- [x] State updated
- [x] Errors handled

---

### T13-05-05: Implement Context Preservation

**Objective**: Preserve context across phases.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/hybrid_mode.py`

**Context Elements**:
- Previous phase results
- Accumulated artifacts
- Decisions made
- Constraints applied

**Implementation**:
```python
class HybridMode(CoordinatorPort):
    def __init__(self, ...):
        ...
        self.phase_results: dict[str, CoordinationResult] = {}
        self.shared_context: dict[str, Any] = {}

    async def coordinate(
        self,
        task: str,
        context: dict,
    ) -> CoordinationResult:
        phase = self._detect_phase(task)

        # Build cumulative context
        enhanced_context = {
            **context,
            "previous_phases": self.phase_results,
            "shared": self.shared_context,
        }

        coordinator = self._get_coordinator_for_phase(phase)
        result = await coordinator.coordinate(task, enhanced_context)

        # Store for future phases
        self.phase_results[phase] = result
        self._update_shared_context(result)

        return result

    def _update_shared_context(
        self,
        result: CoordinationResult,
    ) -> None:
        """Extract sharable context from result."""
        content = result.final_response.content
        if isinstance(content, dict):
            if "decisions" in content:
                self.shared_context["decisions"] = content["decisions"]
            if "artifacts" in content:
                self.shared_context["artifacts"] = content["artifacts"]
```

**Acceptance Criteria**:
- [x] Results preserved
- [x] Context accumulated
- [x] Available to future phases

---

### T13-05-06: Write Unit Tests

**Objective**: Test hybrid mode.

**Files to Create**:
- [x] `tests/unit/adapters/agents/test_hybrid_mode.py`

**Test Cases**:
- [x] Phase detection
- [x] Mode routing
- [x] Phase transitions
- [x] Context preservation
- [x] Default fallback
- [x] Error handling
- [x] Multi-phase workflow

**Acceptance Criteria**:
- [x] All phases tested
- [x] Context verified

---

## 3. Task Dependencies

```
T13-05-01 (Coordinator) ──→ T13-05-02 (Detection) ──→ T13-05-03 (Routing)
                                                           │
                                                           ↓
                                                   T13-05-04 (Transition)
                                                           │
                                                           ↓
                                                   T13-05-05 (Context)
                                                           │
                                                           ↓
                                                   T13-05-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T13-05-01 | Medium | Coordinator setup |
| T13-05-02 | Low | Keyword matching |
| T13-05-03 | Medium | Mode routing |
| T13-05-04 | Medium | Lifecycle hooks |
| T13-05-05 | Medium | State management |
| T13-05-06 | High | Complex scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.1.0 | 2026-01-11 | Implementation | All tasks completed |
