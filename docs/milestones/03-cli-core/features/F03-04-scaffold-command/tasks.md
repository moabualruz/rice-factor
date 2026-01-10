# Feature: F03-04 Scaffold Command

## Status: Pending

## Description

Implement the `rice-factor scaffold` command to create the file structure from an approved ScaffoldPlan artifact. Creates empty files with TODO comments, no logic or tests.

## Requirements Reference

- M03-U-003: All commands shall support `--dry-run` where applicable
- M03-U-004: All destructive commands shall require confirmation
- Commands Table: `rice-factor scaffold` - Create file structure (P0)

## Tasks

### Scaffold Service
- [ ] Create `rice_factor/domain/services/scaffold_service.py`
  - [ ] Define `ScaffoldService` class
  - [ ] Implement `get_scaffold_plan()` - load ScaffoldPlan artifact
  - [ ] Implement `validate_prerequisites()` - check ProjectPlan + ArchitecturePlan approved
  - [ ] Implement `scaffold(plan, dry_run)` - create file structure
  - [ ] Implement `generate_todo_comment(file_entry)` - create TODO header
  - [ ] Handle different file kinds (source, test, config, doc)

### TODO Comment Templates
- [ ] Define TODO comment templates for each file kind:
  - [ ] Source files: `# TODO: Implement <description>`
  - [ ] Test files: `# TODO: Implement tests for <target>`
  - [ ] Config files: `# TODO: Configure <description>`
  - [ ] Doc files: `<!-- TODO: Document <description> -->`
- [ ] Support language-specific comment styles based on file extension

### Scaffold Command Implementation
- [ ] Update `rice_factor/entrypoints/cli/commands/scaffold.py`
  - [ ] Check phase (ProjectPlan + ArchitecturePlan must be approved)
  - [ ] Load ScaffoldPlan artifact
  - [ ] Display preview of files to be created
  - [ ] Require confirmation before execution
  - [ ] Create directories and files with Rich progress
  - [ ] Display summary with created files count
  - [ ] Support `--dry-run` option (preview only)

### File Creation Logic
- [ ] Implement file creation:
  - [ ] Create parent directories if they don't exist
  - [ ] Create empty file with TODO comment header
  - [ ] Skip existing files (with warning)
  - [ ] Track created vs skipped files

### Rich Output
- [ ] Display scaffold preview with Rich Tree
- [ ] Show file kind icons/colors
- [ ] Progress bar for file creation
- [ ] Summary table with created/skipped counts

### Unit Tests
- [ ] Create `tests/unit/domain/services/test_scaffold_service.py`
  - [ ] Test `validate_prerequisites()` passes with approved plans
  - [ ] Test `validate_prerequisites()` fails without approved plans
  - [ ] Test `scaffold()` creates correct directory structure
  - [ ] Test `scaffold()` creates files with TODO comments
  - [ ] Test `generate_todo_comment()` for each file kind
  - [ ] Test skipping existing files
- [ ] Create `tests/unit/entrypoints/cli/commands/test_scaffold.py`
  - [ ] Test scaffold command requires approved plans
  - [ ] Test scaffold command with valid ScaffoldPlan
  - [ ] Test `--dry-run` doesn't create files
  - [ ] Test confirmation prompt is shown
  - [ ] Test `--help` shows documentation

### Integration Tests
- [ ] Create `tests/integration/cli/test_scaffold_flow.py`
  - [ ] Test full scaffold flow with approved plans
  - [ ] Test created files have correct TODO content
  - [ ] Test directory structure matches ScaffoldPlan

## Acceptance Criteria

- [ ] `rice-factor scaffold` creates file structure from ScaffoldPlan
- [ ] Command blocked until ProjectPlan and ArchitecturePlan approved
- [ ] Files created with appropriate TODO comments
- [ ] `--dry-run` previews without creating files
- [ ] Confirmation required before execution
- [ ] Existing files are skipped with warning
- [ ] Clear summary of created/skipped files
- [ ] All tests pass (20+ tests)
- [ ] mypy passes
- [ ] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/services/scaffold_service.py` | Scaffold service |
| `rice_factor/entrypoints/cli/commands/scaffold.py` | Scaffold command |
| `tests/unit/domain/services/test_scaffold_service.py` | Service tests |
| `tests/unit/entrypoints/cli/commands/test_scaffold.py` | Command tests |
| `tests/integration/cli/test_scaffold_flow.py` | Integration tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
