# Feature: F04-04 Compiler Pass Framework

## Status: Complete

## Description

Implement the compiler pass orchestration framework that manages LLM invocations for each artifact type. This is the central coordination layer that connects system prompts, context building, and structured output enforcement.

## Requirements Reference

- 03-Artifact-Builder.md: 3.4-3.10 Compiler Passes
- M04-E-001: As soon as the LLM returns output, the system shall validate against JSON Schema
- M04-U-002: Output exactly one artifact per invocation

## Tasks

### Compiler Pass Base Class
- [x] Create `rice_factor/domain/services/compiler_pass.py`
  - [x] Define `CompilerPass` abstract base class
  - [x] Define abstract `pass_type` property -> `CompilerPassType`
  - [x] Define `required_files` property -> `list[str]` (via ContextBuilder)
  - [x] Define `required_artifacts` property -> `list[ArtifactType]` (via ContextBuilder)
  - [x] Define `forbidden_inputs` property -> `list[str]` (via ContextBuilder)
  - [x] Define abstract `output_artifact_type` property -> `ArtifactType`
  - [x] Implement `compile(context, llm_port) -> CompilerResult` template method
    - [x] Call `validate_context(context)`
    - [x] Call `build_prompt(context)`
    - [x] Get output schema via `get_output_schema()`
    - [x] Call `llm_port.generate()`
    - [x] If success, call `validate_output(result.payload)`
    - [x] Return result
  - [x] Implement `validate_context(context)` - raise on invalid via ContextBuilder
  - [x] Implement `build_prompt(context) -> str` - use PromptManager
  - [x] Implement `get_output_schema() -> dict` - load JSON schema via SchemaInjector
  - [x] Implement `validate_output(payload)` - use OutputValidator

### Individual Compiler Passes
- [x] Create `rice_factor/domain/services/passes/__init__.py`
  - [x] Define `PassRegistry` class (singleton pattern)
  - [x] Define `PassNotFoundError` exception
  - [x] Implement `get_pass(pass_type) -> CompilerPass`
  - [x] Implement `get_pass_class(pass_type) -> type[CompilerPass]`
  - [x] Implement `list_passes() -> list[CompilerPassType]`
  - [x] Register all 6 passes
  - [x] Define `get_pass()` convenience function

- [x] Create `rice_factor/domain/services/passes/project_planner.py`
  - [x] Define `ProjectPlannerPass(CompilerPass)`
  - [x] `pass_type = CompilerPassType.PROJECT`
  - [x] Required inputs via ContextBuilder
  - [x] Forbidden inputs via ContextBuilder
  - [x] `output_artifact_type = ArtifactType.PROJECT_PLAN`

- [x] Create `rice_factor/domain/services/passes/architecture_planner.py`
  - [x] Define `ArchitecturePlannerPass(CompilerPass)`
  - [x] `pass_type = CompilerPassType.ARCHITECTURE`
  - [x] Required inputs via ContextBuilder
  - [x] `output_artifact_type = ArtifactType.ARCHITECTURE_PLAN`

- [x] Create `rice_factor/domain/services/passes/scaffold_planner.py`
  - [x] Define `ScaffoldPlannerPass(CompilerPass)`
  - [x] `pass_type = CompilerPassType.SCAFFOLD`
  - [x] Required inputs via ContextBuilder
  - [x] `output_artifact_type = ArtifactType.SCAFFOLD_PLAN`

- [x] Create `rice_factor/domain/services/passes/test_designer.py`
  - [x] Define `TestDesignerPass(CompilerPass)`
  - [x] `pass_type = CompilerPassType.TEST`
  - [x] Required inputs via ContextBuilder
  - [x] `output_artifact_type = ArtifactType.TEST_PLAN`

- [x] Create `rice_factor/domain/services/passes/implementation_planner.py`
  - [x] Define `ImplementationPlannerPass(CompilerPass)`
  - [x] `pass_type = CompilerPassType.IMPLEMENTATION`
  - [x] Required inputs via ContextBuilder (TINY context)
  - [x] `output_artifact_type = ArtifactType.IMPLEMENTATION_PLAN`

- [x] Create `rice_factor/domain/services/passes/refactor_planner.py`
  - [x] Define `RefactorPlannerPass(CompilerPass)`
  - [x] `pass_type = CompilerPassType.REFACTOR`
  - [x] Required inputs via ContextBuilder
  - [x] `output_artifact_type = ArtifactType.REFACTOR_PLAN`

### Artifact Builder Service
- [x] Create `rice_factor/domain/services/artifact_builder.py`
  - [x] Define `ArtifactBuilder` class
  - [x] Define `ArtifactBuilderError` exception
  - [x] Implement `__init__(llm_port, storage, context_builder, failure_service)`
  - [x] Implement `build(pass_type, project_root, target_file, artifacts) -> ArtifactEnvelope`
    - [x] Get pass from registry
    - [x] Build context via ContextBuilder
    - [x] Execute pass
    - [x] If success, create ArtifactEnvelope
    - [x] Save to storage
    - [x] Return envelope
  - [x] Implement `build_with_context(pass_type, context) -> ArtifactEnvelope`
  - [x] Implement `_create_envelope(pass_type, payload) -> ArtifactEnvelope`
    - [x] Generate UUID (automatic via ArtifactEnvelope)
    - [x] Set status to DRAFT
    - [x] Set created_by to LLM
    - [x] Map pass type to artifact type
  - [x] Implement `_create_failure_envelope(pass_type, result, context) -> ArtifactEnvelope`
  - [x] Implement `_create_payload_model(artifact_type, payload) -> BaseModel`

### Service Exports
- [x] Update `rice_factor/domain/services/__init__.py`
  - [x] Export `CompilerPass`
  - [x] Export `ArtifactBuilder`
  - [x] Export `PassRegistry` and `get_pass`

### Unit Tests
- [x] Create `tests/unit/domain/services/test_compiler_pass.py`
  - [x] Test base class cannot be instantiated
  - [x] Test `compile` template method flow (with mock LLM)
  - [x] Test `validate_context` raises on forbidden inputs
  - [x] Test `validate_output` delegates to OutputValidator

- [x] Create `tests/unit/domain/services/passes/test_project_planner.py`
  - [x] Test `pass_type` returns PROJECT
  - [x] Test required inputs
  - [x] Test forbidden inputs includes source code
  - [x] Test successful compilation (mocked LLM)

- [x] Create similar test files for all 6 passes
  - [x] `test_architecture_planner.py`
  - [x] `test_scaffold_planner.py`
  - [x] `test_test_designer.py`
  - [x] `test_implementation_planner.py`
  - [x] `test_refactor_planner.py`

- [x] Create `tests/unit/domain/services/passes/test_pass_registry.py`
  - [x] Test registry returns correct pass for each type
  - [x] Test `PassNotFoundError` raised for invalid type
  - [x] Test singleton pattern
  - [x] Test `list_passes()` returns all types

- [x] Create `tests/unit/domain/services/test_artifact_builder.py`
  - [x] Test `build` orchestrates full flow (mocked components)
  - [x] Test envelope creation with correct metadata
  - [x] Test storage is called on success
  - [x] Test FailureReport created on blocking error

## Acceptance Criteria

- [x] All 6 compiler passes defined with correct input/output specs
- [x] Pass registry returns correct pass for each type
- [x] Context validation enforces required/forbidden inputs
- [x] Output validation enforces schema conformance
- [x] ArtifactBuilder orchestrates full compilation flow
- [x] Artifacts saved with DRAFT status
- [x] All tests pass (117 tests)
- [x] mypy passes
- [x] ruff passes

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
| 2026-01-10 | Implementation verified complete - 117 tests pass |
