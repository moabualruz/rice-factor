# Feature: F03-03 Plan Commands

## Status: Pending

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
- [ ] Refactor `rice_factor/entrypoints/cli/commands/plan.py`
  - [ ] Create `plan_app = typer.Typer()` subcommand app
  - [ ] Register plan_app in main.py with `app.add_typer(plan_app, name="plan")`

### Stub LLM Service
- [ ] Create `rice_factor/adapters/llm/stub.py`
  - [ ] Define `StubLLMAdapter` class
  - [ ] Implement `generate_project_plan()` - returns placeholder ProjectPlan
  - [ ] Implement `generate_architecture_plan()` - returns placeholder ArchitecturePlan
  - [ ] Implement `generate_test_plan()` - returns placeholder TestPlan
  - [ ] Implement `generate_implementation_plan(file)` - returns placeholder ImplementationPlan
  - [ ] Implement `generate_refactor_plan(goal)` - returns placeholder RefactorPlan
  - [ ] All stubs return valid artifact payloads with `stub: true` marker

### Plan Project Command
- [ ] Implement `@plan_app.command("project")`
  - [ ] Check phase (must be INIT+)
  - [ ] Call stub LLM to generate ProjectPlan payload
  - [ ] Create ArtifactEnvelope with payload
  - [ ] Save via ArtifactService
  - [ ] Display artifact summary with Rich
  - [ ] Support `--dry-run` option

### Plan Architecture Command
- [ ] Implement `@plan_app.command("architecture")`
  - [ ] Check phase (must have ProjectPlan approved)
  - [ ] Call stub LLM to generate ArchitecturePlan payload
  - [ ] Create ArtifactEnvelope with dependency on ProjectPlan
  - [ ] Save via ArtifactService
  - [ ] Display artifact summary
  - [ ] Support `--dry-run` option

### Plan Tests Command
- [ ] Implement `@plan_app.command("tests")`
  - [ ] Check phase (must be SCAFFOLDED+)
  - [ ] Call stub LLM to generate TestPlan payload
  - [ ] Create ArtifactEnvelope with dependencies
  - [ ] Save via ArtifactService
  - [ ] Display artifact summary
  - [ ] Support `--dry-run` option

### Plan Impl Command
- [ ] Implement `@plan_app.command("impl")`
  - [ ] Accept `file` argument (target file path)
  - [ ] Check phase (must be TEST_LOCKED+)
  - [ ] Load related tests for the file
  - [ ] Call stub LLM to generate ImplementationPlan payload
  - [ ] Create ArtifactEnvelope with dependencies
  - [ ] Save via ArtifactService
  - [ ] Display plan steps with Rich
  - [ ] Support `--dry-run` option

### Plan Refactor Command
- [ ] Implement `@plan_app.command("refactor")`
  - [ ] Accept `goal` argument (refactoring goal)
  - [ ] Check phase (must be TEST_LOCKED+)
  - [ ] Call stub LLM to generate RefactorPlan payload
  - [ ] Create ArtifactEnvelope with dependencies
  - [ ] Save via ArtifactService
  - [ ] Display operations preview
  - [ ] Support `--dry-run` option

### Unit Tests
- [ ] Create `tests/unit/adapters/llm/test_stub.py`
  - [ ] Test all stub generators return valid payloads
  - [ ] Test stub marker is present
- [ ] Create `tests/unit/entrypoints/cli/commands/test_plan.py`
  - [ ] Test `plan project` creates artifact
  - [ ] Test `plan project --dry-run` doesn't save
  - [ ] Test `plan architecture` requires ProjectPlan
  - [ ] Test `plan tests` creates TestPlan artifact
  - [ ] Test `plan impl <file>` creates ImplementationPlan
  - [ ] Test `plan refactor <goal>` creates RefactorPlan
  - [ ] Test phase gating blocks commands appropriately
  - [ ] Test `--help` for all subcommands

### Integration Tests
- [ ] Create `tests/integration/cli/test_plan_flow.py`
  - [ ] Test full plan project -> approve -> plan architecture flow
  - [ ] Test artifacts are correctly saved to filesystem
  - [ ] Test artifact dependencies are recorded

## Acceptance Criteria

- [ ] `rice-factor plan --help` shows all plan subcommands
- [ ] `rice-factor plan project` creates ProjectPlan artifact
- [ ] `rice-factor plan architecture` creates ArchitecturePlan artifact
- [ ] `rice-factor plan tests` creates TestPlan artifact
- [ ] `rice-factor plan impl <file>` creates ImplementationPlan artifact
- [ ] `rice-factor plan refactor <goal>` creates RefactorPlan artifact
- [ ] All commands integrate with ArtifactService from M02
- [ ] Phase gating prevents out-of-order execution
- [ ] `--dry-run` works for all commands
- [ ] All tests pass (30+ tests)
- [ ] mypy passes
- [ ] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/plan.py` | Plan subcommand app |
| `rice_factor/adapters/llm/stub.py` | Stub LLM adapter |
| `rice_factor/entrypoints/cli/main.py` | Register plan_app |
| `tests/unit/adapters/llm/test_stub.py` | Stub adapter tests |
| `tests/unit/entrypoints/cli/commands/test_plan.py` | Plan command tests |
| `tests/integration/cli/test_plan_flow.py` | Integration tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
