# Feature: F03-04 Scaffold Command

## Status: Complete

## Description

Implement the `rice-factor scaffold` command to create the file structure from an approved ScaffoldPlan artifact. Creates empty files with TODO comments, no logic or tests.

## Requirements Reference

- M03-U-003: All commands shall support `--dry-run` where applicable
- M03-U-004: All destructive commands shall require confirmation
- Commands Table: `rice-factor scaffold` - Create file structure (P0)

## Tasks

### Scaffold Service
- [x] Create `rice_factor/domain/services/scaffold_service.py`
  - [x] Define `ScaffoldService` class
  - [x] Implement `scaffold(plan, dry_run)` - create file structure
  - [x] Implement `generate_todo_comment(file_entry)` - create TODO header
  - [x] Handle different file kinds (source, test, config, doc)
  - [x] Implement `preview(plan)` - preview what would be created

### TODO Comment Templates
- [x] Define TODO comment templates for each file kind:
  - [x] Source files: `# TODO: Implement <description>`
  - [x] Test files: `# TODO: Implement tests for <target>`
  - [x] Config files: `# TODO: Configure <description>`
  - [x] Doc files: `<!-- TODO: Document <description> -->`
- [x] Support language-specific comment styles based on file extension
  - [x] Python (.py): Docstring style
  - [x] JavaScript/TypeScript (.js/.ts): // comment style
  - [x] Go (.go): // comment style
  - [x] Rust (.rs): // comment style
  - [x] YAML (.yaml/.yml): # comment style
  - [x] Markdown (.md): HTML comment + heading

### Scaffold Command Implementation
- [x] Update `rice_factor/entrypoints/cli/commands/scaffold.py`
  - [x] Check phase (must be PLANNING phase)
  - [x] Generate ScaffoldPlan via StubLLMAdapter
  - [x] Display preview of files to be created
  - [x] Require confirmation before execution (--yes to skip)
  - [x] Create directories and files with Rich Tree display
  - [x] Display summary with created files count
  - [x] Support `--dry-run` option (preview only)
  - [x] Support `--path` option for project root

### File Creation Logic
- [x] Implement file creation:
  - [x] Create parent directories if they don't exist
  - [x] Create file with TODO comment header
  - [x] Skip existing files (with warning)
  - [x] Track created vs skipped files
  - [x] Report errors for files that couldn't be created

### Rich Output
- [x] Display scaffold preview with Rich Tree
- [x] Show file kind icons/colors
- [x] Summary table with created/skipped counts

### Stub LLM Integration
- [x] Add `generate_scaffold_plan()` to StubLLMAdapter
  - [x] Returns placeholder ScaffoldPlanPayload
  - [x] Includes source, test, and doc files

### Unit Tests
- [x] Create `tests/unit/domain/services/test_scaffold_service.py` (26 tests)
  - [x] Test ScaffoldService initialization
  - [x] Test `generate_todo_comment()` for each file kind and extension
  - [x] Test `scaffold()` creates correct directory structure
  - [x] Test `scaffold()` creates files with TODO comments
  - [x] Test `scaffold()` skips existing files
  - [x] Test `scaffold()` with dry_run mode
  - [x] Test ScaffoldResult success property
  - [x] Test `preview()` method
- [x] Create `tests/unit/entrypoints/cli/commands/test_scaffold.py` (19 tests)
  - [x] Test scaffold command help
  - [x] Test scaffold command requires initialization
  - [x] Test scaffold command requires PLANNING phase
  - [x] Test `--dry-run` doesn't create files
  - [x] Test confirmation prompt is shown
  - [x] Test `--yes` skips confirmation
  - [x] Test files are created with TODO content
  - [x] Test artifact is saved
  - [x] Test existing files are skipped
  - [x] Test summary output
- [x] Update `tests/unit/adapters/llm/test_stub.py` (6 new tests)
  - [x] Test `generate_scaffold_plan()` returns ScaffoldPlanPayload
  - [x] Test includes source, test, and doc files

### Integration Tests
- [ ] Create `tests/integration/cli/test_scaffold_flow.py` (Deferred to M07)
  - [ ] Test full scaffold flow with approved plans
  - [ ] Test created files have correct TODO content
  - [ ] Test directory structure matches ScaffoldPlan

## Acceptance Criteria

- [x] `rice-factor scaffold` creates file structure from ScaffoldPlan
- [x] Command blocked until project is in PLANNING phase
- [x] Files created with appropriate TODO comments
- [x] `--dry-run` previews without creating files
- [x] Confirmation required before execution
- [x] Existing files are skipped with warning
- [x] Clear summary of created/skipped files
- [x] All tests pass (51 new tests: 26 service + 19 command + 6 stub)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/services/scaffold_service.py` | Scaffold service (created) |
| `rice_factor/domain/services/__init__.py` | Export ScaffoldService |
| `rice_factor/entrypoints/cli/commands/scaffold.py` | Scaffold command (rewritten) |
| `rice_factor/adapters/llm/stub.py` | Added generate_scaffold_plan() |
| `tests/unit/domain/services/test_scaffold_service.py` | Service tests (26 tests) |
| `tests/unit/entrypoints/cli/commands/test_scaffold.py` | Command tests (19 tests) |
| `tests/unit/adapters/llm/test_stub.py` | Added scaffold plan tests (6 tests) |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - 430 total tests passing |
