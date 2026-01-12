# Feature: F04-05 System Prompts

## Status: Complete

## Description

Define and manage the system prompts for each compiler pass. These prompts implement the "LLM as compiler" philosophy and enforce the hard contract from the specification.

## Requirements Reference

- 03-Artifact-Builder.md: 3.3 Global System Prompt (Canonical)
- 03-Artifact-Builder.md: 3.5-3.10 Pass-specific prompts
- M04-U-003: The LLM shall emit no explanations or reasoning
- M04-U-004: The LLM shall emit no source code

## Tasks

### Prompts Module Setup
- [x] Create `rice_factor/domain/prompts/__init__.py`
  - [x] Define `PromptManager` class
  - [x] Implement `get_system_prompt(pass_type) -> str`
    - [x] Combine base + pass-specific prompt
  - [x] Implement `get_base_prompt() -> str`
    - [x] Return global system prompt
  - [x] Implement `get_pass_prompt(pass_type) -> str`
    - [x] Return pass-specific prompt
  - [x] Implement `get_full_prompt(pass_type, context, include_schema) -> str`
    - [x] Combine system prompt + context + schema

### Global System Prompt
- [x] Create `rice_factor/domain/prompts/base.py`
  - [x] Define `BASE_SYSTEM_PROMPT` constant (verbatim from spec)
    ```
    SYSTEM PROMPT — ARTIFACT BUILDER

    You are an Artifact Builder.

    You are a compiler stage in a deterministic development system.

    Rules:
    * You do not generate source code.
    * You do not explain decisions.
    * You do not include reasoning or commentary.
    * You output valid JSON only.
    * You generate exactly one artifact per invocation.
    * You must conform exactly to the provided JSON Schema.
    * If required information is missing or ambiguous, you must fail with:

    { "error": "missing_information", "details": "<description>" }

    Any deviation from these rules is a failure.
    ```
  - [x] Define `FAILURE_FORMAT_MISSING_INFO` and `FAILURE_FORMAT_INVALID_REQUEST` constants
  - [x] Define `HARD_CONTRACT_RULES` list with all 7 rules

### Pass-Specific Prompts
- [x] Create `rice_factor/domain/prompts/project_planner.py`
  - [x] Define `PROJECT_PLANNER_PROMPT` constant
  - [x] Include purpose: "Translate human requirements to system decomposition"
  - [x] List allowed inputs
  - [x] List forbidden inputs
  - [x] List failure conditions (undefined terms, conflicts, missing arch)

- [x] Create `rice_factor/domain/prompts/architecture_planner.py`
  - [x] Define `ARCHITECTURE_PLANNER_PROMPT` constant
  - [x] Include purpose: "Define dependency laws"
  - [x] List rules: mechanically enforceable, no vague constraints

- [x] Create `rice_factor/domain/prompts/scaffold_planner.py`
  - [x] Define `SCAFFOLD_PLANNER_PROMPT` constant
  - [x] Include purpose: "Define structure only"
  - [x] List rules: no logic, descriptions required, idiomatic paths

- [x] Create `rice_factor/domain/prompts/test_designer.py`
  - [x] Define `TEST_DESIGNER_PROMPT` constant
  - [x] Include purpose: "Define correctness contract"
  - [x] List rules: behavior not implementation, minimal but complete, no mocking internal state

- [x] Create `rice_factor/domain/prompts/implementation_planner.py`
  - [x] Define `IMPLEMENTATION_PLANNER_PROMPT` constant
  - [x] Include purpose: "Create small reviewable units of work"
  - [x] List rules: exactly one target, ordered steps, reference relevant tests only
  - [x] Note: TINY context requirement

- [x] Create `rice_factor/domain/prompts/refactor_planner.py`
  - [x] Define `REFACTOR_PLANNER_PROMPT` constant
  - [x] Include purpose: "Plan structural change without behavior change"
  - [x] List rules: tests remain valid, explicit operations, partial allowed

### Schema Injection
- [x] Create `rice_factor/domain/prompts/schema_injector.py`
  - [x] Define `SchemaInjector` class
  - [x] Implement `inject_schema(prompt, artifact_type, placeholder) -> str`
    - [x] Load schema from `schemas/` directory
    - [x] Format schema as JSON string
    - [x] Insert into prompt at designated location (or append if no placeholder)
  - [x] Implement `load_schema(artifact_type) -> dict`
    - [x] Read JSON file from schemas directory
    - [x] Cache schemas for performance via `@lru_cache`
  - [x] Implement `format_schema_for_prompt(artifact_type) -> str`
  - [x] Define `SchemaNotFoundError` exception

### Prompt Exports
- [x] Update module exports to expose PromptManager, SchemaInjector, all prompts

### Unit Tests
- [x] Create `tests/unit/domain/prompts/test_prompt_manager.py`
  - [x] Test `get_base_prompt()` returns canonical prompt
  - [x] Test `get_pass_prompt(PROJECT)` returns project planner prompt
  - [x] Test `get_system_prompt(PROJECT)` combines base + pass prompts
  - [x] Test all 6 pass prompts are defined
  - [x] Test prompts contain required elements (purpose, rules)
  - [x] Test `get_full_prompt()` includes context and schema

- [x] Create `tests/unit/domain/prompts/test_base.py`
  - [x] Test `BASE_SYSTEM_PROMPT` contains all 7 rules
  - [x] Test `FAILURE_FORMAT` templates are valid JSON-like

- [x] Create `tests/unit/domain/prompts/test_schema_injector.py`
  - [x] Test `load_schema` loads valid JSON for all artifact types
  - [x] Test `load_schema` raises `SchemaNotFoundError` for missing schema
  - [x] Test `inject_schema` replaces placeholder or appends
  - [x] Test schema caching works

## Acceptance Criteria

- [x] Global system prompt matches spec exactly (verbatim)
- [x] Each pass has purpose, inputs, rules, and failure conditions
- [x] Prompts are pure strings (no external dependencies)
- [x] Schema injection works for all 8 artifact types
- [x] PromptManager provides easy access to all prompts
- [x] All tests pass (69 tests)
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/prompts/__init__.py` | CREATE | PromptManager class |
| `rice_factor/domain/prompts/base.py` | CREATE | Global system prompt |
| `rice_factor/domain/prompts/project_planner.py` | CREATE | Project planner prompt |
| `rice_factor/domain/prompts/architecture_planner.py` | CREATE | Architecture planner prompt |
| `rice_factor/domain/prompts/scaffold_planner.py` | CREATE | Scaffold planner prompt |
| `rice_factor/domain/prompts/test_designer.py` | CREATE | Test designer prompt |
| `rice_factor/domain/prompts/implementation_planner.py` | CREATE | Implementation planner prompt |
| `rice_factor/domain/prompts/refactor_planner.py` | CREATE | Refactor planner prompt |
| `rice_factor/domain/prompts/schema_injector.py` | CREATE | Schema injection utility |
| `tests/unit/domain/prompts/test_prompt_manager.py` | CREATE | PromptManager tests |
| `tests/unit/domain/prompts/test_base.py` | CREATE | Base prompt tests |
| `tests/unit/domain/prompts/test_schema_injector.py` | CREATE | Schema injector tests |

## Dependencies

- F04-01: LLM Protocol Interface (CompilerPassType)
- M02: Artifact System (ArtifactType for schema loading)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation verified complete - 69 tests pass |
