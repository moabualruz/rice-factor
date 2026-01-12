# Feature F09-03: Audit Drift Command - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T09-03-01 | Create audit command group | **Complete** | P0 |
| T09-03-02 | Implement drift subcommand | **Complete** | P0 |
| T09-03-03 | Add JSON output format | **Complete** | P1 |
| T09-03-04 | Add rich table output | **Complete** | P1 |
| T09-03-05 | Add exit code handling | **Complete** | P0 |
| T09-03-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T09-03-01: Create Audit Command Group

**Objective**: Add `audit` command group to CLI.

**Files Created**:
- [x] `rice_factor/entrypoints/cli/commands/audit.py`

**Files Modified**:
- [x] `rice_factor/entrypoints/cli/main.py` - Added audit import and registration
- [x] `rice_factor/entrypoints/cli/commands/__init__.py` - Added audit export

**Implementation**:
- [x] Created Typer app for audit commands
- [x] Registered with main app via `add_typer()`

**Acceptance Criteria**:
- [x] `rice-factor audit --help` works
- [x] Subcommands accessible

---

### T09-03-02: Implement Drift Subcommand

**Objective**: Implement `rice-factor audit drift` command.

**Files Modified**:
- [x] `rice_factor/entrypoints/cli/commands/audit.py`

**Implementation**:
- [x] `audit_drift` function with all options
- [x] `--path` option for project root
- [x] `--code-dir` option for source directory
- [x] `--threshold` option for override

**Acceptance Criteria**:
- [x] Command runs drift analysis
- [x] Code directory configurable
- [x] Threshold overridable

---

### T09-03-03: Add JSON Output Format

**Objective**: Support `--json` flag for machine-readable output.

**Implementation**:
- [x] `--json` option added to command
- [x] JSON output via DriftReport.to_dict()
- [x] Plain print() for clean JSON (no Rich formatting)

**Acceptance Criteria**:
- [x] Valid JSON output
- [x] All report fields included
- [x] Pipe-friendly format

---

### T09-03-04: Add Rich Table Output

**Objective**: Pretty-print drift report with Rich.

**Implementation**:
- [x] `_display_drift_report()` function
- [x] Rich Panel for status header
- [x] Rich Table grouped by signal type
- [x] Severity color-coding
- [x] Summary footer with counts

**Acceptance Criteria**:
- [x] Signals grouped by type
- [x] Severity color-coded
- [x] Summary footer shown

---

### T09-03-05: Add Exit Code Handling

**Objective**: Exit with proper codes for CI integration.

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | No drift detected |
| 1 | Drift detected but below threshold |
| 2 | Reconciliation required (threshold exceeded or critical) |

**Implementation**:
- [x] Exit 0 when no signals
- [x] Exit 1 when signals < threshold
- [x] Exit 2 when threshold exceeded or critical signal present

**Acceptance Criteria**:
- [x] CI can check exit code
- [x] Codes documented in help

---

### T09-03-06: Write Unit Tests

**Objective**: Test CLI command end-to-end.

**Files Created**:
- [x] `tests/unit/entrypoints/cli/commands/test_audit.py` (14 tests)

**Test Cases**:
- [x] test_help_shows_description
- [x] test_help_shows_drift_command
- [x] test_drift_help_shows_options
- [x] test_drift_help_shows_exit_codes
- [x] test_drift_runs_without_error
- [x] test_drift_json_output
- [x] test_drift_exit_code_1_when_drift_below_threshold
- [x] test_drift_exit_code_2_when_threshold_exceeded
- [x] test_drift_exit_code_2_on_critical_signal
- [x] test_drift_threshold_option
- [x] test_drift_code_dir_option
- [x] test_drift_displays_signals_grouped_by_type
- [x] test_drift_shows_summary
- [x] test_finds_project_root_from_subdirectory

**Acceptance Criteria**:
- [x] All CLI options tested
- [x] Output formats verified
- [x] 14 tests passing

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
| 1.0.1 | 2026-01-11 | Implementation | All tasks complete - 14 tests passing |
