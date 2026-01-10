# Feature: F04-04 Compiler Pass Framework

## Status: Pending

## Description

Implement the compiler pass orchestration framework that manages LLM invocations for each artifact type. This is the central coordination layer that connects system prompts, context building, and structured output enforcement.

## Requirements Reference

- 03-Artifact-Builder.md: 3.4-3.10 Compiler Passes
- M04-E-001: As soon as the LLM returns output, the system shall validate against JSON Schema
- M04-U-002: Output exactly one artifact per invocation

## Tasks

### Compiler Pass Base Class
- [ ] Create `rice_factor/domain/services/compiler_pass.py`
  - [ ] Define `CompilerPass` abstract base class
  - [ ] Define abstract `pass_type` property -> `CompilerPassType`
  - [ ] Define abstract `required_inputs` property -> `list[str]`
  - [ ] Define abstract `forbidden_inputs` property -> `list[str]`
  - [ ] Define abstract `output_artifact_type` property -> `ArtifactType`
  - [ ] Implement `compile(context, llm_port) -> CompilerResult` template method
    - [ ] Call `validate_context(context)`
    - [ ] Call `build_prompt(context)`
    - [ ] Get output schema via `get_output_schema()`
    - [ ] Call `llm_port.generate()`
    - [ ] If success, call `validate_output(result.payload)`
    - [ ] Return result
  - [ ] Implement `validate_context(context)` - raise on invalid
  - [ ] Implement `build_prompt(context) -> str` - use PromptManager
  - [ ] Implement `get_output_schema() -> dict` - load JSON schema
  - [ ] Implement `validate_output(payload)` - use OutputValidator

### Individual Compiler Passes
- [ ] Create `rice_factor/domain/services/passes/__init__.py`
  - [ ] Define `PassRegistry` class
  - [ ] Implement `get_pass(pass_type) -> CompilerPass`
  - [ ] Register all 6 passes
  - [ ] Export all pass classes

- [ ] Create `rice_factor/domain/services/passes/project_planner.py`
  - [ ] Define `ProjectPlannerPass(CompilerPass)`
  - [ ] `pass_type = CompilerPassType.PROJECT`
  - [ ] `required_inputs = ["requirements.md", "constraints.md", "glossary.md"]`
  - [ ] `forbidden_inputs = ["source_code", "tests", "existing_artifacts"]`
  - [ ] `output_artifact_type = ArtifactType.PROJECT_PLAN`

- [ ] Create `rice_factor/domain/services/passes/architecture_planner.py`
  - [ ] Define `ArchitecturePlannerPass(CompilerPass)`
  - [ ] `pass_type = CompilerPassType.ARCHITECTURE`
  - [ ] `required_inputs = ["ProjectPlan:approved", "constraints.md"]`
  - [ ] `forbidden_inputs = []`
  - [ ] `output_artifact_type = ArtifactType.ARCHITECTURE_PLAN`

- [ ] Create `rice_factor/domain/services/passes/scaffold_planner.py`
  - [ ] Define `ScaffoldPlannerPass(CompilerPass)`
  - [ ] `pass_type = CompilerPassType.SCAFFOLD`
  - [ ] `required_inputs = ["ProjectPlan:approved", "ArchitecturePlan:approved"]`
  - [ ] `forbidden_inputs = []`
  - [ ] `output_artifact_type = ArtifactType.SCAFFOLD_PLAN`

- [ ] Create `rice_factor/domain/services/passes/test_designer.py`
  - [ ] Define `TestDesignerPass(CompilerPass)`
  - [ ] `pass_type = CompilerPassType.TEST`
  - [ ] `required_inputs = ["ProjectPlan:approved", "ArchitecturePlan:approved", "ScaffoldPlan:approved", "requirements.md"]`
  - [ ] `forbidden_inputs = []`
  - [ ] `output_artifact_type = ArtifactType.TEST_PLAN`

- [ ] Create `rice_factor/domain/services/passes/implementation_planner.py`
  - [ ] Define `ImplementationPlannerPass(CompilerPass)`
  - [ ] `pass_type = CompilerPassType.IMPLEMENTATION`
  - [ ] `required_inputs = ["TestPlan:approved", "ScaffoldPlan:approved", "target_file"]`
  - [ ] `forbidden_inputs = ["all_other_source_files"]` (TINY context)
  - [ ] `output_artifact_type = ArtifactType.IMPLEMENTATION_PLAN`

- [ ] Create `rice_factor/domain/services/passes/refactor_planner.py`
  - [ ] Define `RefactorPlannerPass(CompilerPass)`
  - [ ] `pass_type = CompilerPassType.REFACTOR`
  - [ ] `required_inputs = ["ArchitecturePlan:approved", "TestPlan:locked", "repo_layout"]`
  - [ ] `forbidden_inputs = []`
  - [ ] `output_artifact_type = ArtifactType.REFACTOR_PLAN`

### Artifact Builder Service
- [ ] Create `rice_factor/domain/services/artifact_builder.py`
  - [ ] Define `ArtifactBuilder` class
  - [ ] Implement `__init__(llm_port, validator, storage, context_builder)`
  - [ ] Implement `build(pass_type, project_root, target_file=None) -> ArtifactEnvelope`
    - [ ] Get pass from registry
    - [ ] Build context via ContextBuilder
    - [ ] Execute pass
    - [ ] If success, create ArtifactEnvelope
    - [ ] Save to storage
    - [ ] Return envelope
  - [ ] Implement `_create_envelope(pass_type, payload) -> ArtifactEnvelope`
    - [ ] Generate UUID
    - [ ] Set status to DRAFT
    - [ ] Set created_by to SYSTEM
    - [ ] Include metadata

### Service Exports
- [ ] Update `rice_factor/domain/services/__init__.py`
  - [ ] Export `CompilerPass`
  - [ ] Export `ArtifactBuilder`
  - [ ] Export `PassRegistry`

### Unit Tests
- [ ] Create `tests/unit/domain/services/test_compiler_pass.py`
  - [ ] Test base class cannot be instantiated
  - [ ] Test `compile` template method flow (with mock LLM)
  - [ ] Test `validate_context` raises on missing inputs
  - [ ] Test `validate_context` raises on forbidden inputs
  - [ ] Test `validate_output` delegates to OutputValidator

- [ ] Create `tests/unit/domain/services/passes/test_project_planner.py`
  - [ ] Test `pass_type` returns PROJECT
  - [ ] Test `required_inputs` includes all 3 files
  - [ ] Test `forbidden_inputs` includes source code
  - [ ] Test successful compilation (mocked LLM)

- [ ] Create similar test files for all 6 passes
  - [ ] `test_architecture_planner.py`
  - [ ] `test_scaffold_planner.py`
  - [ ] `test_test_designer.py`
  - [ ] `test_implementation_planner.py`
  - [ ] `test_refactor_planner.py`

- [ ] Create `tests/unit/domain/services/passes/test_pass_registry.py`
  - [ ] Test registry returns correct pass for each type
  - [ ] Test registry raises for invalid type

- [ ] Create `tests/unit/domain/services/test_artifact_builder.py`
  - [ ] Test `build` orchestrates full flow (mocked components)
  - [ ] Test envelope creation with correct metadata
  - [ ] Test storage is called on success
  - [ ] Test FailureReport created on blocking error

## Acceptance Criteria

- [ ] All 6 compiler passes defined with correct input/output specs
- [ ] Pass registry returns correct pass for each type
- [ ] Context validation enforces required/forbidden inputs
- [ ] Output validation enforces schema conformance
- [ ] ArtifactBuilder orchestrates full compilation flow
- [ ] Artifacts saved with DRAFT status
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/services/compiler_pass.py` | CREATE | Base compiler pass class |
| `rice_factor/domain/services/passes/__init__.py` | CREATE | Pass registry and exports |
| `rice_factor/domain/services/passes/project_planner.py` | CREATE | Project planner pass |
| `rice_factor/domain/services/passes/architecture_planner.py` | CREATE | Architecture planner pass |
| `rice_factor/domain/services/passes/scaffold_planner.py` | CREATE | Scaffold planner pass |
| `rice_factor/domain/services/passes/test_designer.py` | CREATE | Test designer pass |
| `rice_factor/domain/services/passes/implementation_planner.py` | CREATE | Implementation planner pass |
| `rice_factor/domain/services/passes/refactor_planner.py` | CREATE | Refactor planner pass |
| `rice_factor/domain/services/artifact_builder.py` | CREATE | Artifact builder service |
| `rice_factor/domain/services/__init__.py` | UPDATE | Export builder and passes |
| `tests/unit/domain/services/test_compiler_pass.py` | CREATE | Base pass tests |
| `tests/unit/domain/services/passes/*.py` | CREATE | Individual pass tests |
| `tests/unit/domain/services/test_artifact_builder.py` | CREATE | Builder tests |

## Dependencies

- F04-01: LLM Protocol Interface (LLMPort, CompilerPassType, CompilerContext)
- F04-05: System Prompts (PromptManager)
- F04-06: Structured Output Enforcement (OutputValidator)
- F04-07: Error Handling (error types)
- M02: Artifact System (ArtifactEnvelope, storage)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
