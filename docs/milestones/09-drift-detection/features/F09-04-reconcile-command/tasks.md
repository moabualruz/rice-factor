# Feature F09-04: Reconcile Command - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-04-01 | Create ReconciliationService | Pending | P0 |
| T09-04-02 | Implement signal-to-step mapping | Pending | P0 |
| T09-04-03 | Add reconcile CLI command | Pending | P0 |
| T09-04-04 | Implement work freeze check | Pending | P1 |
| T09-04-05 | Add approval integration | Pending | P0 |
| T09-04-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T09-04-01: Create ReconciliationService

**Objective**: Create service for generating reconciliation plans.

**Files to Create**:
- [ ] `rice_factor/domain/services/reconciliation_service.py`

**Implementation**:
```python
class ReconciliationService:
    """Generates reconciliation plans from drift reports."""

    def __init__(
        self,
        artifact_service: ArtifactService,
        llm_port: LLMPort | None = None,
    ) -> None:
        self.artifact_service = artifact_service
        self.llm_port = llm_port

    def generate_plan(self, drift_report: DriftReport) -> ArtifactEnvelope:
        """Generate ReconciliationPlan from drift report."""
        ...
```

**Acceptance Criteria**:
- [ ] Service follows domain patterns
- [ ] Generates valid artifact
- [ ] Optional LLM for enrichment

---

### T09-04-02: Implement Signal-to-Step Mapping

**Objective**: Convert drift signals to reconciliation steps.

**Files to Modify**:
- [ ] `rice_factor/domain/services/reconciliation_service.py`

**Mapping Rules**:
| Signal Type | Action |
|-------------|--------|
| ORPHAN_CODE | CREATE_ARTIFACT |
| ORPHAN_PLAN | ARCHIVE_ARTIFACT |
| UNDOCUMENTED_BEHAVIOR | UPDATE_REQUIREMENTS |
| REFACTOR_HOTSPOT | REVIEW_CODE |

**Implementation**:
```python
def _signal_to_step(
    self,
    signal: DriftSignal,
    priority: int,
) -> ReconciliationStep:
    action_map = {
        DriftSignalType.ORPHAN_CODE: ReconciliationAction.CREATE_ARTIFACT,
        DriftSignalType.ORPHAN_PLAN: ReconciliationAction.ARCHIVE_ARTIFACT,
        # ...
    }
    ...
```

**Acceptance Criteria**:
- [ ] All signal types mapped
- [ ] Priority assigned correctly
- [ ] Reason included from signal

---

### T09-04-03: Add Reconcile CLI Command

**Objective**: Implement `rice-factor reconcile` command.

**Files to Create/Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/reconcile.py`
- [ ] `rice_factor/entrypoints/cli/main.py`

**Implementation**:
```python
@app.command()
def reconcile(
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve",
        help="Skip manual approval step",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show plan without saving",
    ),
) -> None:
    """Generate reconciliation plan for detected drift."""
    ...
```

**Acceptance Criteria**:
- [ ] Generates plan from drift
- [ ] Shows human-readable output
- [ ] Saves artifact to disk

---

### T09-04-04: Implement Work Freeze Check

**Objective**: Block new work when reconciliation pending.

**Files to Modify**:
- [ ] `rice_factor/domain/services/artifact_service.py`

**Implementation**:
```python
def check_work_freeze(self) -> bool:
    """Check if new work is blocked due to pending reconciliation."""
    pending_reconciliations = self.storage.list_by_type("ReconciliationPlan")
    for plan in pending_reconciliations:
        if plan.status == ArtifactStatus.APPROVED:
            continue
        if plan.payload.get("freeze_new_work", True):
            return True
    return False
```

**Integration Points**:
- [ ] `rice-factor plan` checks freeze
- [ ] `rice-factor impl` checks freeze
- [ ] Clear error message shown

**Acceptance Criteria**:
- [ ] Freeze blocks new artifacts
- [ ] Approved plans don't block
- [ ] Clear unblock instructions

---

### T09-04-05: Add Approval Integration

**Objective**: Enable approval workflow for reconciliation plans.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/approve.py`

**Implementation**:
- [ ] Add ReconciliationPlan to approvable types
- [ ] On approval, execute steps if applicable
- [ ] Unfreeze work after approval

**Acceptance Criteria**:
- [ ] `rice-factor approve reconciliation` works
- [ ] Approval unfreezes work
- [ ] Status transitions correct

---

### T09-04-06: Write Unit Tests

**Objective**: Test reconciliation service and command.

**Files to Create**:
- [ ] `tests/unit/domain/services/test_reconciliation_service.py`
- [ ] `tests/integration/cli/test_reconcile.py`

**Test Cases**:
- [ ] Service generates valid plan
- [ ] Signal mapping is correct
- [ ] Work freeze activates
- [ ] Work freeze deactivates on approval
- [ ] CLI dry-run works
- [ ] CLI saves artifact

**Acceptance Criteria**:
- [ ] Service logic tested
- [ ] CLI integration tested
- [ ] Freeze behavior tested

---

## 3. Task Dependencies

```
T09-04-01 (Service) ──→ T09-04-02 (Mapping) ──→ T09-04-03 (CLI)
                                                      │
                                           ┌──────────┴──────────┐
                                           ↓                     ↓
                                   T09-04-04 (Freeze)    T09-04-05 (Approval)
                                           │                     │
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
| T09-04-04 | Medium | Integration points |
| T09-04-05 | Low | Approval extension |
| T09-04-06 | Medium | Multiple scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
