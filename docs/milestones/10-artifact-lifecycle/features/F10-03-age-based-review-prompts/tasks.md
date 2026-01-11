# Feature F10-03: Age-Based Review Prompts - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-03-01 | Create LifecycleService | Pending | P0 |
| T10-03-02 | Implement review prompt generation | Pending | P0 |
| T10-03-03 | Add work blocking check | Pending | P0 |
| T10-03-04 | Integrate with CLI commands | Pending | P0 |
| T10-03-05 | Add record review functionality | Pending | P1 |
| T10-03-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T10-03-01: Create LifecycleService

**Objective**: Central service for lifecycle management.

**Files to Create**:
- [ ] `rice_factor/domain/services/lifecycle_service.py`

**Implementation**:
```python
class LifecycleService:
    """Manages artifact lifecycle and policy evaluation."""

    def __init__(
        self,
        artifact_store: StoragePort,
        policies: dict[str, LifecyclePolicy],
        arch_validator: ArchitectureValidatorPort | None = None,
        coverage_monitor: CoverageMonitorPort | None = None,
    ) -> None:
        self.artifact_store = artifact_store
        self.policies = policies
        self.arch_validator = arch_validator
        self.coverage_monitor = coverage_monitor

    def evaluate_all(self) -> list[PolicyResult]: ...
    def get_blocking_issues(self) -> list[PolicyResult]: ...
    def generate_age_report(self) -> AgeReport: ...
```

**Acceptance Criteria**:
- [ ] Service follows domain patterns
- [ ] Supports optional validators
- [ ] Evaluates all artifacts

---

### T10-03-02: Implement Review Prompt Generation

**Objective**: Generate actionable review prompts.

**Files to Modify**:
- [ ] `rice_factor/domain/services/lifecycle_service.py`

**Prompt Types**:

| Urgency | Message |
|---------|---------|
| INFORMATIONAL | "FYI: {artifact} is {age} months old" |
| RECOMMENDED | "{artifact} should be reviewed (age: {age} months)" |
| REQUIRED | "Review required: {artifact} ({reason})" |
| MANDATORY | "BLOCKING: {artifact} must be reviewed before proceeding" |

**Implementation**:
```python
def generate_prompts(self) -> list[ReviewPrompt]:
    prompts = []
    results = self.evaluate_all()

    for result in results:
        if not result.triggers:
            continue

        prompt = ReviewPrompt(
            artifact_id=result.artifact_id,
            artifact_type=result.artifact_type,
            urgency=result.urgency,
            message=self._format_message(result),
            actions=self._suggested_actions(result),
        )
        prompts.append(prompt)

    return prompts
```

**Acceptance Criteria**:
- [ ] Prompts are actionable
- [ ] Messages include relevant details
- [ ] Suggested actions provided

---

### T10-03-03: Add Work Blocking Check

**Objective**: Prevent new work when mandatory review pending.

**Files to Modify**:
- [ ] `rice_factor/domain/services/lifecycle_service.py`
- [ ] `rice_factor/domain/services/artifact_service.py`

**Integration Points**:
- [ ] `rice-factor plan` checks before planning
- [ ] `rice-factor impl` checks before implementation
- [ ] `rice-factor scaffold` checks before scaffolding

**Implementation**:
```python
def check_can_proceed(self) -> tuple[bool, list[PolicyResult]]:
    """Check if new work can proceed."""
    blocking = self.get_blocking_issues()
    can_proceed = len(blocking) == 0
    return can_proceed, blocking

# In ArtifactService:
def create(self, artifact_type: str, payload: dict) -> ArtifactEnvelope:
    can_proceed, blocking = self.lifecycle_service.check_can_proceed()
    if not can_proceed:
        raise LifecycleBlockingError(blocking)
    # ... continue with creation
```

**Acceptance Criteria**:
- [ ] Mandatory issues block work
- [ ] Clear error message shown
- [ ] Bypass mechanism available

---

### T10-03-04: Integrate with CLI Commands

**Objective**: Show prompts in relevant commands.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/plan.py`
- [ ] `rice_factor/entrypoints/cli/commands/impl.py`
- [ ] `rice_factor/entrypoints/cli/main.py`

**Integration**:
```python
# At start of plan command
def plan(ctx: typer.Context, ...):
    lifecycle = container.get(LifecycleService)
    prompts = lifecycle.generate_prompts()

    # Show warnings for RECOMMENDED
    for prompt in prompts:
        if prompt.urgency == ReviewUrgency.RECOMMENDED:
            console.print(f"[yellow]⚠ {prompt.message}[/yellow]")

    # Block for MANDATORY
    blocking = [p for p in prompts if p.urgency == ReviewUrgency.MANDATORY]
    if blocking:
        console.print("[red]Cannot proceed due to blocking issues:[/red]")
        for prompt in blocking:
            console.print(f"  - {prompt.message}")
        raise typer.Exit(1)
```

**Acceptance Criteria**:
- [ ] Warnings shown before blocking
- [ ] Blocking issues stop execution
- [ ] User knows what to do

---

### T10-03-05: Add Record Review Functionality

**Objective**: Allow marking artifacts as reviewed.

**Files to Create/Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/artifact.py`

**Command**:
```bash
rice-factor artifact review <artifact-id> [--notes "Review notes"]
```

**Implementation**:
```python
@app.command("review")
def review_artifact(
    artifact_id: str,
    notes: str = typer.Option(None, "--notes", "-n"),
) -> None:
    """Mark an artifact as reviewed."""
    lifecycle = container.get(LifecycleService)
    lifecycle.record_review(artifact_id, notes)

    console.print(f"✓ Artifact {artifact_id} marked as reviewed")
```

**Acceptance Criteria**:
- [ ] Review timestamp updated
- [ ] Optional notes saved
- [ ] Clears blocking status

---

### T10-03-06: Write Unit Tests

**Objective**: Test review prompt system.

**Files to Create**:
- [ ] `tests/unit/domain/services/test_lifecycle_service.py`

**Test Cases**:
- [ ] Generate prompts for old artifacts
- [ ] No prompts for fresh artifacts
- [ ] Work blocking with mandatory issues
- [ ] Work allowed without blocking issues
- [ ] Record review updates timestamp
- [ ] Record review clears blocking
- [ ] Prompt messages are formatted correctly

**Acceptance Criteria**:
- [ ] All scenarios tested
- [ ] Integration points verified

---

## 3. Task Dependencies

```
T10-03-01 (Service) ──→ T10-03-02 (Prompts) ──→ T10-03-03 (Blocking)
                                                      │
                                           ┌──────────┴──────────┐
                                           ↓                     ↓
                                   T10-03-04 (CLI)       T10-03-05 (Review)
                                           │                     │
                                           └──────────┬──────────┘
                                                      ↓
                                              T10-03-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T10-03-01 | Medium | Service design |
| T10-03-02 | Medium | Message formatting |
| T10-03-03 | Medium | Integration |
| T10-03-04 | Medium | Multiple commands |
| T10-03-05 | Low | Simple command |
| T10-03-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
