# Feature: F03-03 Plan Commands

## Status: Complete

## Description

Implement the `rice-factor plan` subcommand app with all planning commands: project, architecture, tests, impl, and refactor. These commands generate planning artifacts via stub LLM integration (actual LLM implementation in M04).

## Requirements Reference

- M03-U-002: All commands shall support `--help` for documentation
- M03-U-003: All commands shall support `--dry-run` where applicable
- Commands Table:
  - `rice-factor plan project` - Generate ProjectPlan (P0)
  - `rice-factor plan architecture` - Generate ArchitecturePlan (P1)
  - `rice-factor plan tests` - Generate TestPlan (P0)
  - `rice-factor plan impl <file>` - Generate ImplementationPlan (P0)
  - `rice-factor plan refactor <goal>` - Generate RefactorPlan (P1)

## Tasks

### Plan Subcommand App
- [x] Refactor `rice_factor/entrypoints/cli/commands/plan.py`
  - [x] Create `plan_app = typer.Typer()` subcommand app
  - [x] Register plan_app in main.py with `app.add_typer(plan_app, name="plan")`

### Stub LLM Service
- [x] Create `rice_factor/adapters/llm/stub.py`
  - [x] Define `StubLLMAdapter` class
  - [x] Implement `generate_project_plan()` - returns placeholder ProjectPlan
  - [x] Implement `generate_architecture_plan()` - returns placeholder ArchitecturePlan
  - [x] Implement `generate_test_plan()` - returns placeholder TestPlan
  - [x] Implement `generate_implementation_plan(file)` - returns placeholder ImplementationPlan
  - [x] Implement `generate_refactor_plan(goal)` - returns placeholder RefactorPlan
  - [x] All stubs return valid artifact payloads

### Plan Project Command
- [x] Implement `@plan_app.command("project")`
  - [x] Check phase (must be INIT+)
  - [x] Call stub LLM to generate ProjectPlan payload
  - [x] Create ArtifactEnvelope with payload
  - [x] Save via ArtifactService
  - [x] Display artifact summary with Rich
  - [x] Support `--dry-run` option

### Plan Architecture Command
- [x] Implement `@plan_app.command("architecture")`
  - [x] Check phase (must have ProjectPlan approved)
  - [x] Call stub LLM to generate ArchitecturePlan payload
  - [x] Create ArtifactEnvelope with dependency on ProjectPlan
  - [x] Save via ArtifactService
  - [x] Display artifact summary
  - [x] Support `--dry-run` option

### Plan Tests Command
- [x] Implement `@plan_app.command("tests")`
  - [x] Check phase (must be SCAFFOLDED+)
  - [x] Call stub LLM to generate TestPlan payload
  - [x] Create ArtifactEnvelope with dependencies
  - [x] Save via ArtifactService
  - [x] Display artifact summary
  - [x] Support `--dry-run` option

### Plan Impl Command
- [x] Implement `@plan_app.command("impl")`
  - [x] Accept `file` argument (target file path)
  - [x] Check phase (must be TEST_LOCKED+)
  - [x] Call stub LLM to generate ImplementationPlan payload
  - [x] Create ArtifactEnvelope with dependencies
  - [x] Save via ArtifactService
  - [x] Display plan steps with Rich
  - [x] Support `--dry-run` option

### Plan Refactor Command
- [x] Implement `@plan_app.command("refactor")`
  - [x] Accept `goal` argument (refactoring goal)
  - [x] Check phase (must be TEST_LOCKED+)
  - [x] Call stub LLM to generate RefactorPlan payload
  - [x] Create ArtifactEnvelope with dependencies
  - [x] Save via ArtifactService
  - [x] Display operations preview
  - [x] Support `--dry-run` option

### Unit Tests
- [x] Create `tests/unit/adapters/llm/test_stub.py`
  - [x] Test all stub generators return valid payloads
  - [x] Test payload structure and constraints
- [x] Create `tests/unit/entrypoints/cli/commands/test_plan.py`
  - [x] Test `plan project` creates artifact
  - [x] Test `plan project --dry-run` doesn't save
  - [x] Test `plan architecture` requires ProjectPlan
  - [x] Test `plan tests` creates TestPlan artifact
  - [x] Test `plan impl <file>` creates ImplementationPlan
  - [x] Test `plan refactor <goal>` creates RefactorPlan
  - [x] Test phase gating blocks commands appropriately
  - [x] Test `--help` for all subcommands

### Integration Tests
- [ ] Create `tests/integration/cli/test_plan_flow.py` (Deferred to M07)
  - [ ] Test full plan project -> approve -> plan architecture flow
  - [ ] Test artifacts are correctly saved to filesystem
  - [ ] Test artifact dependencies are recorded

## Acceptance Criteria

- [x] `rice-factor plan --help` shows all plan subcommands
- [x] `rice-factor plan project` creates ProjectPlan artifact
- [x] `rice-factor plan architecture` creates ArchitecturePlan artifact
- [x] `rice-factor plan tests` creates TestPlan artifact
- [x] `rice-factor plan impl <file>` creates ImplementationPlan artifact
- [x] `rice-factor plan refactor <goal>` creates RefactorPlan artifact
- [x] All commands integrate with ArtifactService from M02
- [x] Phase gating prevents out-of-order execution
- [x] `--dry-run` works for all commands
- [x] All tests pass (43+ new tests added: 21 stub tests + 22 plan command tests)
- [x] mypy passes (source code)
- [x] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/plan.py` | Plan subcommand app (rewritten) |
| `rice_factor/adapters/llm/stub.py` | Stub LLM adapter (created) |
| `rice_factor/adapters/llm/__init__.py` | Export StubLLMAdapter |
| `rice_factor/entrypoints/cli/main.py` | Register plan app with add_typer |
| `tests/unit/adapters/llm/__init__.py` | Test package init (created) |
| `tests/unit/adapters/llm/test_stub.py` | Stub adapter tests (21 tests) |
| `tests/unit/entrypoints/cli/commands/test_plan.py` | Plan command tests (22 tests) |
| `tests/unit/test_cli.py` | Updated help text assertion |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - 379 total tests passing |
