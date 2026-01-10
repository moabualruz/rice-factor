# Milestone 03: CLI Core - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

The CLI Core milestone implements the complete command-line interface for Rice-Factor. The CLI serves as the primary human interaction point, orchestrating all workflows through a phase-gated command system that enforces the project's seven principles.

**Key Design Goals:**
- Phase-gated commands prevent workflow violations
- All commands integrate with M02's artifact system
- Stubs for LLM (M04), Executor (M05), and Validation (M06) logic
- Clear, actionable output via Rich console

---

## 2. Architecture

### 2.1 CLI Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI Layer (Typer)                            │
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │   init   │ │   plan   │ │ scaffold │ │   impl   │ │  approve │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │            │         │
│  ┌────┴────────────┴────────────┴────────────┴────────────┴─────┐  │
│  │                    CLI Utilities (utils.py)                   │  │
│  │  • Error handling  • Confirmation prompts  • Rich output      │  │
│  └──────────────────────────────┬────────────────────────────────┘  │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼────────────────────────────────────┐
│                         Domain Services                              │
│                                  │                                   │
│  ┌──────────────────┐   ┌───────┴────────┐   ┌──────────────────┐  │
│  │  PhaseService    │   │ ArtifactService │   │   InitService    │  │
│  │  (phase gating)  │   │  (from M02)     │   │  (questionnaire) │  │
│  └──────────────────┘   └────────────────┘   └──────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼────────────────────────────────────┐
│                         Adapters (M02)                               │
│                                  │                                   │
│  ┌──────────────────┐   ┌───────┴────────┐   ┌──────────────────┐  │
│  │ StorageAdapter   │   │   Validator    │   │    Registry      │  │
│  └──────────────────┘   └────────────────┘   └──────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Hexagonal File Organization

```
rice_factor/
├── domain/
│   └── services/
│       ├── phase_service.py      # Phase gating logic
│       └── init_service.py       # Initialization service
│
├── entrypoints/
│   └── cli/
│       ├── main.py               # Typer app entry point
│       ├── utils.py              # Shared CLI utilities
│       └── commands/
│           ├── __init__.py
│           ├── init.py           # rice-factor init
│           ├── plan.py           # rice-factor plan <type>
│           ├── scaffold.py       # rice-factor scaffold
│           ├── impl.py           # rice-factor impl <file>
│           ├── review.py         # rice-factor review
│           ├── apply.py          # rice-factor apply
│           ├── test.py           # rice-factor test
│           ├── diagnose.py       # rice-factor diagnose
│           ├── approve.py        # rice-factor approve
│           ├── lock.py           # rice-factor lock
│           ├── refactor.py       # rice-factor refactor <subcommand>
│           ├── validate.py       # rice-factor validate
│           ├── override.py       # rice-factor override
│           └── resume.py         # rice-factor resume
│
└── config/
    └── container.py              # DI wiring (extended for CLI)
```

---

## 3. CLI Framework Design

### 3.1 Typer Application Structure

```python
# rice_factor/entrypoints/cli/main.py
import typer
from rich.console import Console

app = typer.Typer(
    name="rice-factor",
    help="LLM-assisted software development system",
    no_args_is_help=True,
)

# Register subcommand apps
app.add_typer(plan_app, name="plan")
app.add_typer(refactor_app, name="refactor")

# Register standalone commands
app.command()(init_command)
app.command()(scaffold_command)
app.command()(impl_command)
app.command()(review_command)
app.command()(apply_command)
app.command()(test_command)
app.command()(diagnose_command)
app.command()(approve_command)
app.command()(lock_command)
app.command()(validate_command)
app.command()(override_command)
app.command()(resume_command)

console = Console()
```

### 3.2 Command Organization

| Command Type | Pattern | Example |
|--------------|---------|---------|
| Standalone | `rice-factor <cmd>` | `rice-factor init` |
| Subcommand App | `rice-factor <app> <cmd>` | `rice-factor plan project` |
| With Arguments | `rice-factor <cmd> <arg>` | `rice-factor impl src/main.py` |
| With Options | `rice-factor <cmd> --opt` | `rice-factor apply --dry-run` |

### 3.3 Rich Console Integration

```python
# rice_factor/entrypoints/cli/utils.py
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def success(message: str) -> None:
    """Display success message."""
    console.print(f"[green]✓[/green] {message}")

def warning(message: str) -> None:
    """Display warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")

def error(message: str) -> None:
    """Display error message."""
    console.print(f"[red]✗[/red] {message}")

def confirm(message: str, default: bool = False) -> bool:
    """Prompt for confirmation."""
    return typer.confirm(message, default=default)
```

---

## 4. Phase Gating System

### 4.1 Phase State Machine

```
┌──────────────┐
│  UNINIT      │  No .project/ directory
└──────┬───────┘
       │ init
       ▼
┌──────────────┐
│  INIT        │  .project/ exists, no artifacts
└──────┬───────┘
       │ plan project + approve
       ▼
┌──────────────┐
│  PLANNING    │  ProjectPlan approved
└──────┬───────┘
       │ plan architecture + approve + scaffold
       ▼
┌──────────────┐
│  SCAFFOLDED  │  ScaffoldPlan executed
└──────┬───────┘
       │ plan tests + approve + lock
       ▼
┌──────────────┐
│  TEST_LOCKED │  TestPlan locked (immutable)
└──────┬───────┘
       │ plan impl + impl + apply
       ▼
┌──────────────┐
│  IMPLEMENTING│  Active development loop
└──────────────┘
```

### 4.2 Phase Service Design

```python
# rice_factor/domain/services/phase_service.py
from enum import Enum
from pathlib import Path

class Phase(str, Enum):
    UNINIT = "uninit"
    INIT = "init"
    PLANNING = "planning"
    SCAFFOLDED = "scaffolded"
    TEST_LOCKED = "test_locked"
    IMPLEMENTING = "implementing"

class PhaseService:
    """Determines project phase and validates command execution."""

    def __init__(self, project_root: Path, artifact_service: ArtifactService):
        self.project_root = project_root
        self.artifact_service = artifact_service

    def get_current_phase(self) -> Phase:
        """Determine current project phase from artifacts."""
        ...

    def can_execute(self, command: str) -> bool:
        """Check if command is allowed in current phase."""
        ...

    def get_blocking_reason(self, command: str) -> str | None:
        """Return user-friendly message if command is blocked."""
        ...
```

### 4.3 Command Prerequisites

| Command | Required Phase | Prerequisites |
|---------|---------------|---------------|
| `init` | UNINIT | None |
| `plan project` | INIT+ | .project/ exists |
| `plan architecture` | PLANNING+ | ProjectPlan approved |
| `scaffold` | PLANNING+ | ProjectPlan + ArchitecturePlan approved |
| `plan tests` | SCAFFOLDED+ | Scaffold executed |
| `lock tests` | SCAFFOLDED+ | TestPlan approved |
| `plan impl` | TEST_LOCKED+ | TestPlan locked |
| `impl` | TEST_LOCKED+ | ImplementationPlan exists |
| `apply` | TEST_LOCKED+ | Approved diff exists |
| `test` | TEST_LOCKED+ | Code exists |
| `refactor *` | TEST_LOCKED+ | RefactorPlan for apply |

---

## 5. Command Designs

### 5.1 Init Command

```python
# rice_factor/entrypoints/cli/commands/init.py
@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing"),
) -> None:
    """Initialize a new Rice-Factor project."""
    # 1. Check if .project/ exists
    # 2. Create .project/ directory
    # 3. Run interactive questionnaire
    # 4. Generate template files:
    #    - requirements.md
    #    - constraints.md
    #    - glossary.md
    #    - non_goals.md
    #    - risks.md
```

### 5.2 Plan Commands (Subcommand App)

```python
# rice_factor/entrypoints/cli/commands/plan.py
plan_app = typer.Typer(name="plan", help="Generate planning artifacts")

@plan_app.command("project")
def plan_project(dry_run: bool = False) -> None:
    """Generate ProjectPlan artifact."""
    # 1. Check phase (must be INIT+)
    # 2. Stub: Generate placeholder ProjectPlan
    # 3. Save via ArtifactService
    # 4. Display result

@plan_app.command("architecture")
def plan_architecture(dry_run: bool = False) -> None:
    """Generate ArchitecturePlan artifact."""

@plan_app.command("tests")
def plan_tests(dry_run: bool = False) -> None:
    """Generate TestPlan artifact."""

@plan_app.command("impl")
def plan_impl(file: str, dry_run: bool = False) -> None:
    """Generate ImplementationPlan for a file."""

@plan_app.command("refactor")
def plan_refactor(goal: str, dry_run: bool = False) -> None:
    """Generate RefactorPlan artifact."""
```

### 5.3 Scaffold Command

```python
# rice_factor/entrypoints/cli/commands/scaffold.py
@app.command()
def scaffold(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only"),
) -> None:
    """Create file structure from ScaffoldPlan."""
    # 1. Check phase (ProjectPlan + ArchitecturePlan approved)
    # 2. Load ScaffoldPlan artifact
    # 3. For each file in plan:
    #    - Create parent directories
    #    - Create empty file with TODO comment
    # 4. Confirmation required before execution
```

### 5.4 Implementation Commands

```python
# rice_factor/entrypoints/cli/commands/impl.py
@app.command()
def impl(
    file: str = typer.Argument(..., help="Target file path"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Generate implementation diff for a file."""
    # 1. Check phase (TEST_LOCKED+)
    # 2. Load ImplementationPlan for file
    # 3. Stub: Generate placeholder diff
    # 4. Save diff to audit/diffs/
    # 5. Display diff preview

# rice_factor/entrypoints/cli/commands/review.py
@app.command()
def review() -> None:
    """Show pending diff for approval."""
    # 1. Load latest unapproved diff
    # 2. Display: diff, plan steps, test expectations
    # 3. Prompt: approve / reject / re-plan

# rice_factor/entrypoints/cli/commands/apply.py
@app.command()
def apply(
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Apply approved diff."""
    # 1. Check for approved diff
    # 2. Stub: Apply diff (git apply placeholder)
    # 3. Confirmation required

# rice_factor/entrypoints/cli/commands/test.py
@app.command()
def test() -> None:
    """Run test suite."""
    # 1. Stub: Run native test runner
    # 2. Emit ValidationResult artifact
    # 3. Display results

# rice_factor/entrypoints/cli/commands/diagnose.py
@app.command()
def diagnose() -> None:
    """Analyze test/validation failures."""
    # 1. Load latest ValidationResult
    # 2. Analyze failures
    # 3. Produce FailureReport artifact
```

### 5.5 Approval Commands

```python
# rice_factor/entrypoints/cli/commands/approve.py
@app.command()
def approve(
    artifact: str = typer.Argument(..., help="Artifact path or ID"),
) -> None:
    """Approve an artifact."""
    # 1. Resolve artifact by path or ID
    # 2. Call ArtifactService.approve()
    # 3. Record in audit log
    # 4. Display confirmation

# rice_factor/entrypoints/cli/commands/lock.py
@app.command()
def lock(
    artifact: str = typer.Argument(..., help="Artifact path (TestPlan only)"),
) -> None:
    """Lock an artifact (TestPlan only)."""
    # 1. Verify artifact is TestPlan
    # 2. Call ArtifactService.lock()
    # 3. Display immutability warning
```

### 5.6 Refactor Commands (Subcommand App)

```python
# rice_factor/entrypoints/cli/commands/refactor.py
refactor_app = typer.Typer(name="refactor", help="Refactoring operations")

@refactor_app.command("check")
def refactor_check() -> None:
    """Verify refactor capability support."""
    # 1. Load RefactorPlan
    # 2. Check language/operation matrix (stub)
    # 3. Report unsupported operations

@refactor_app.command("dry-run")
def refactor_dry_run() -> None:
    """Preview refactor changes."""
    # 1. Load RefactorPlan
    # 2. Generate diffs (stub)
    # 3. Display preview only

@refactor_app.command("apply")
def refactor_apply(
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Apply refactor with full test suite."""
    # 1. Check RefactorPlan approved
    # 2. Apply operations (stub)
    # 3. Run full test suite
    # 4. Confirmation required
```

### 5.7 Validation Command

```python
# rice_factor/entrypoints/cli/commands/validate.py
@app.command()
def validate() -> None:
    """Run all validations."""
    # 1. Run schema validation (via M02 validators)
    # 2. Stub: Run architecture rules
    # 3. Stub: Run tests
    # 4. Stub: Run lint
    # 5. Aggregate into ValidationResult artifact
    # 6. Display results with Rich table
```

### 5.8 Override & Recovery Commands

```python
# rice_factor/entrypoints/cli/commands/override.py
@app.command()
def override(
    reason: str = typer.Option(..., "--reason", "-r", help="Justification (required)"),
) -> None:
    """Override blocked operation with audit trail."""
    # 1. Require --reason (non-empty)
    # 2. Record override in audit log
    # 3. Flag for future reconciliation
    # 4. Display warning about manual override

# rice_factor/entrypoints/cli/commands/resume.py
@app.command()
def resume() -> None:
    """Resume after failure."""
    # 1. Reconstruct state from artifacts + audit
    # 2. Identify interrupted operation
    # 3. Resume from last safe point
```

---

## 6. Output & UX Design

### 6.1 Rich Console Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| Panel | Command headers, summaries | `Panel("Initializing project...")` |
| Table | List artifacts, validation results | Columns: Name, Status, Path |
| Progress | Long operations | Spinner during LLM calls |
| Tree | Directory structures | Scaffold preview |
| Syntax | Code diffs, file contents | Highlighted diff output |

### 6.2 Progress Indicators

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
    task = progress.add_task("Generating plan...", total=None)
    # Long operation
```

### 6.3 Error Display

```python
from rich.panel import Panel

def display_error(title: str, message: str, hint: str | None = None) -> None:
    content = f"[red]{message}[/red]"
    if hint:
        content += f"\n\n[dim]Hint: {hint}[/dim]"
    console.print(Panel(content, title=f"[red]{title}[/red]", border_style="red"))
```

### 6.4 Confirmation Prompts

```python
def confirm_destructive(action: str, target: str) -> bool:
    """Confirm destructive action with explicit typing."""
    console.print(f"[yellow]Warning:[/yellow] This will {action} [bold]{target}[/bold]")
    return typer.confirm("Are you sure?", default=False)
```

---

## 7. Stub Strategy

Since M03 focuses on CLI structure, many commands will use stubs for logic implemented in later milestones:

| Stub Type | Milestone | Description |
|-----------|-----------|-------------|
| LLM invocation | M04 | Return placeholder artifacts |
| Diff generation | M05 | Return mock diff |
| Diff application | M05 | Log operation, no actual changes |
| Test execution | M06 | Return mock ValidationResult |
| Lint execution | M06 | Return mock results |
| Architecture rules | M06 | Return mock validation |

**Stub Pattern:**
```python
def stub_llm_generate_plan(plan_type: str) -> dict:
    """Stub: Returns placeholder artifact payload."""
    return {
        "stub": True,
        "message": f"LLM integration pending (Milestone 04)",
        "plan_type": plan_type,
    }
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/unit/entrypoints/cli/test_utils.py
def test_success_output(capsys):
    """Test success message formatting."""

# tests/unit/domain/services/test_phase_service.py
def test_phase_detection_uninit():
    """No .project/ = UNINIT phase."""

def test_can_execute_init_in_uninit():
    """Init command allowed in UNINIT."""

def test_cannot_scaffold_before_planning():
    """Scaffold blocked without approved plans."""
```

### 8.2 Integration Tests

```python
# tests/integration/cli/test_init_flow.py
def test_init_creates_project_directory(tmp_path):
    """init command creates .project/ with all files."""

# tests/integration/cli/test_plan_flow.py
def test_plan_project_creates_artifact(tmp_path):
    """plan project creates ProjectPlan artifact."""
```

### 8.3 CLI Invocation Tests

```python
from typer.testing import CliRunner
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()

def test_help_shows_all_commands():
    result = runner.invoke(app, ["--help"])
    assert "init" in result.output
    assert "plan" in result.output
    assert "scaffold" in result.output
```

---

## 9. Error Handling

### 9.1 Exception Types

```python
# rice_factor/domain/failures/cli_errors.py
class CLIError(RiceFactorError):
    """Base class for CLI errors."""

class PhaseError(CLIError):
    """Command not allowed in current phase."""

class MissingPrerequisiteError(CLIError):
    """Required artifact/state not present."""

class ConfirmationRequired(CLIError):
    """User did not confirm destructive action."""
```

### 9.2 Error Handler Decorator

```python
# rice_factor/entrypoints/cli/utils.py
from functools import wraps

def handle_errors(f):
    """Decorator to convert exceptions to user-friendly CLI errors."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except PhaseError as e:
            error(f"Phase error: {e}")
            raise typer.Exit(1)
        except ArtifactNotFoundError as e:
            error(f"Artifact not found: {e}")
            raise typer.Exit(1)
    return wrapper
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone design |
