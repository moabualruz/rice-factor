# Feature: F07-03 Scaffolding Integration

## Status: Complete

## Description

Wire the ScaffoldExecutor to the `rice-factor scaffold` CLI command. Generate ScaffoldPlan from approved ProjectPlan and execute scaffolding to create empty files with TODO comments. Update phase to SCAFFOLDED after successful execution.

## Requirements Reference

- M07-WF-002: Scaffold command shall only execute after ProjectPlan approved
- M07-S-003: Scaffold executor shall only create files specified in ScaffoldPlan
- M07-U-004: All operations shall emit audit trail entries
- raw/Phase-01-mvp.md: Section 5.3 (scaffold creates empty files)
- design.md: Section 2.1 (Executors integration)

## Tasks

### ScaffoldPlan Generation
- [x] Wire LLM to generate ScaffoldPlan
  - [x] Use ArtifactBuilder with configured LLM provider
  - [x] Read approved ProjectPlan as context (non-stub mode)
  - [x] Call scaffold compiler pass
  - [x] Validate ScaffoldPlan against schema
  - [x] Save ScaffoldPlan artifact

### ScaffoldExecutor Wiring
- [x] Update `rice_factor/entrypoints/cli/commands/scaffold.py`
  - [x] Load/generate ScaffoldPlan
  - [x] Use ScaffoldService for execution
  - [x] Execute scaffold operation
  - [x] Handle execution result

### Phase Transition
- [x] Update phase after scaffold
  - [x] PhaseService checks phase before scaffold
  - [x] Execute scaffold successfully
  - [x] Phase implicitly transitions based on artifacts

### File Creation
- [x] Verify scaffold creates correct files
  - [x] Source files with TODO comments
  - [x] Test files with TODO comments
  - [x] Correct directory structure
  - [x] No logic in created files

### Audit Trail
- [x] Add audit entry for scaffold execution
  - [x] Record files created count
  - [x] Record files skipped count
  - [x] record_scaffold_executed() method

### Unit Tests
- [x] Update `tests/unit/entrypoints/cli/commands/test_scaffold.py`
  - [x] Test scaffold requires planning phase
  - [x] Test scaffold creates files from ScaffoldPlan
  - [x] Test created files have TODO comments
  - [x] Test artifact is saved
  - [x] Test --stub flag for testing without API calls
  - [x] 20 tests passing

## Acceptance Criteria

- [x] `rice-factor scaffold` requires planning phase (ProjectPlan approved)
- [x] ScaffoldPlan is generated via ArtifactBuilder with LLM
- [x] ScaffoldService creates all files from ScaffoldPlan
- [x] Created files contain TODO comments, no logic
- [x] Audit trail records scaffold operation
- [x] --stub flag allows testing without real LLM calls
- [x] All tests pass (20 tests)
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/entrypoints/cli/commands/scaffold.py` | UPDATED | Wire ArtifactBuilder with LLM |
| `tests/unit/entrypoints/cli/commands/test_scaffold.py` | UPDATED | Added --stub flag to tests |

## Dependencies

- F07-02: Project Planning Integration (ProjectPlan must exist) ✓
- F07-07: Safety Enforcement (file authorization) ✓

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Updated scaffold.py to use ArtifactBuilder with configurable LLM |
| 2026-01-10 | Added --stub flag for testing without API calls |
| 2026-01-10 | Stub mode saves artifact and executes scaffold |
| 2026-01-10 | Added audit trail integration |
| 2026-01-10 | Updated tests to use --stub flag |
| 2026-01-10 | 20 tests passing, mypy and ruff clean |
| 2026-01-10 | Feature complete |
