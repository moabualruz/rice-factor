# Feature F09-03: Audit Drift Command - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-03-01 | Create audit command group | Pending | P0 |
| T09-03-02 | Implement drift subcommand | Pending | P0 |
| T09-03-03 | Add JSON output format | Pending | P1 |
| T09-03-04 | Add rich table output | Pending | P1 |
| T09-03-05 | Add exit code handling | Pending | P0 |
| T09-03-06 | Write integration tests | Pending | P0 |

---

## 2. Task Details

### T09-03-01: Create Audit Command Group

**Objective**: Add `audit` command group to CLI.

**Files to Create/Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/audit.py`
- [ ] `rice_factor/entrypoints/cli/main.py`

**Implementation**:
```python
import typer

app = typer.Typer(help="Audit commands for drift and health checks")

# In main.py:
from .commands import audit
app.add_typer(audit.app, name="audit")
```

**Acceptance Criteria**:
- [ ] `rice-factor audit --help` works
- [ ] Subcommands accessible

---

### T09-03-02: Implement Drift Subcommand

**Objective**: Implement `rice-factor audit drift` command.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/audit.py`

**Implementation**:
```python
@app.command("drift")
def audit_drift(
    code_dir: Path = typer.Option(
        Path("src"),
        "--code-dir", "-d",
        help="Code directory to scan",
    ),
    threshold: int = typer.Option(
        None,
        "--threshold", "-t",
        help="Override drift threshold",
    ),
) -> None:
    """Detect drift between code and artifacts."""
    ...
```

**Acceptance Criteria**:
- [ ] Command runs drift analysis
- [ ] Code directory configurable
- [ ] Threshold overridable

---

### T09-03-03: Add JSON Output Format

**Objective**: Support `--json` flag for machine-readable output.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/audit.py`

**Implementation**:
```python
@app.command("drift")
def audit_drift(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    report = detector.full_analysis(code_dir)

    if json_output:
        import json
        print(json.dumps(report.to_dict(), indent=2))
        return
```

**Acceptance Criteria**:
- [ ] Valid JSON output
- [ ] All report fields included
- [ ] Pipe-friendly format

---

### T09-03-04: Add Rich Table Output

**Objective**: Pretty-print drift report with Rich.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/audit.py`

**Implementation**:
```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

def display_drift_report(report: DriftReport) -> None:
    console = Console()

    # Group by signal type
    for signal_type in DriftSignalType:
        signals = report.by_type(signal_type)
        if signals:
            table = Table(title=signal_type.value)
            table.add_column("Path")
            table.add_column("Severity")
            table.add_column("Description")

            for signal in signals:
                table.add_row(
                    signal.path,
                    signal.severity.value,
                    signal.description,
                )

            console.print(table)
```

**Acceptance Criteria**:
- [ ] Signals grouped by type
- [ ] Severity color-coded
- [ ] Summary footer shown

---

### T09-03-05: Add Exit Code Handling

**Objective**: Exit with proper codes for CI integration.

**Files to Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/audit.py`

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | No drift detected |
| 1 | Drift detected but below threshold |
| 2 | Reconciliation required (threshold exceeded) |

**Implementation**:
```python
if report.requires_reconciliation:
    console.print("[red]RECONCILIATION REQUIRED[/red]")
    raise typer.Exit(2)
elif report.signal_count > 0:
    console.print("[yellow]Drift detected (below threshold)[/yellow]")
    raise typer.Exit(1)
else:
    console.print("[green]No drift detected[/green]")
```

**Acceptance Criteria**:
- [ ] CI can check exit code
- [ ] Codes documented in help

---

### T09-03-06: Write Integration Tests

**Objective**: Test CLI command end-to-end.

**Files to Create**:
- [ ] `tests/integration/cli/test_audit_drift.py`

**Test Cases**:
- [ ] Command runs without error
- [ ] JSON output is valid
- [ ] Exit code 0 when clean
- [ ] Exit code 2 when threshold exceeded
- [ ] Code directory option works
- [ ] Threshold override works

**Acceptance Criteria**:
- [ ] All CLI options tested
- [ ] Output formats verified

---

## 3. Task Dependencies

```
T09-03-01 (Command Group) ──→ T09-03-02 (Drift Command)
                                       │
                         ┌─────────────┼─────────────┐
                         ↓             ↓             ↓
                 T09-03-03 (JSON) T09-03-04 (Rich) T09-03-05 (Exit)
                         │             │             │
                         └─────────────┴─────────────┘
                                       │
                                       ↓
                              T09-03-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T09-03-01 | Low | Typer setup |
| T09-03-02 | Medium | Main logic |
| T09-03-03 | Low | JSON serialization |
| T09-03-04 | Medium | Rich formatting |
| T09-03-05 | Low | Exit handling |
| T09-03-06 | Medium | CLI testing |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
