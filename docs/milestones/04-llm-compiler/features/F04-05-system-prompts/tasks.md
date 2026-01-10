# Feature: F04-05 System Prompts

## Status: Pending

## Description

Define and manage the system prompts for each compiler pass. These prompts implement the "LLM as compiler" philosophy and enforce the hard contract from the specification.

## Requirements Reference

- 03-Artifact-Builder.md: 3.3 Global System Prompt (Canonical)
- 03-Artifact-Builder.md: 3.5-3.10 Pass-specific prompts
- M04-U-003: The LLM shall emit no explanations or reasoning
- M04-U-004: The LLM shall emit no source code

## Tasks

### Prompts Module Setup
- [ ] Create `rice_factor/domain/prompts/__init__.py`
  - [ ] Define `PromptManager` class
  - [ ] Implement `get_system_prompt(pass_type) -> str`
    - [ ] Combine base + pass-specific prompt
  - [ ] Implement `get_base_prompt() -> str`
    - [ ] Return global system prompt
  - [ ] Implement `get_pass_prompt(pass_type) -> str`
    - [ ] Return pass-specific prompt
  - [ ] Implement `get_full_prompt(pass_type, context, schema) -> str`
    - [ ] Combine system prompt + context + schema

### Global System Prompt
- [ ] Create `rice_factor/domain/prompts/base.py`
  - [ ] Define `BASE_SYSTEM_PROMPT` constant (verbatim from spec)
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
  - [ ] Define `FAILURE_FORMAT` constant for error responses

### Pass-Specific Prompts
- [ ] Create `rice_factor/domain/prompts/project_planner.py`
  - [ ] Define `PROJECT_PLANNER_PROMPT` constant
  - [ ] Include purpose: "Translate human requirements to system decomposition"
  - [ ] List allowed inputs
  - [ ] List forbidden inputs
  - [ ] List failure conditions (undefined terms, conflicts, missing arch)

- [ ] Create `rice_factor/domain/prompts/architecture_planner.py`
  - [ ] Define `ARCHITECTURE_PLANNER_PROMPT` constant
  - [ ] Include purpose: "Define dependency laws"
  - [ ] List rules: mechanically enforceable, no vague constraints

- [ ] Create `rice_factor/domain/prompts/scaffold_planner.py`
  - [ ] Define `SCAFFOLD_PLANNER_PROMPT` constant
  - [ ] Include purpose: "Define structure only"
  - [ ] List rules: no logic, descriptions required, idiomatic paths

- [ ] Create `rice_factor/domain/prompts/test_designer.py`
  - [ ] Define `TEST_DESIGNER_PROMPT` constant
  - [ ] Include purpose: "Define correctness contract"
  - [ ] List rules: behavior not implementation, minimal but complete, no mocking internal state

- [ ] Create `rice_factor/domain/prompts/implementation_planner.py`
  - [ ] Define `IMPLEMENTATION_PLANNER_PROMPT` constant
  - [ ] Include purpose: "Create small reviewable units of work"
  - [ ] List rules: exactly one target, ordered steps, reference relevant tests only
  - [ ] Note: TINY context requirement

- [ ] Create `rice_factor/domain/prompts/refactor_planner.py`
  - [ ] Define `REFACTOR_PLANNER_PROMPT` constant
  - [ ] Include purpose: "Plan structural change without behavior change"
  - [ ] List rules: tests remain valid, explicit operations, partial allowed

### Schema Injection
- [ ] Create `rice_factor/domain/prompts/schema_injector.py`
  - [ ] Define `SchemaInjector` class
  - [ ] Implement `inject_schema(prompt, artifact_type) -> str`
    - [ ] Load schema from `schemas/` directory
    - [ ] Format schema as JSON string
    - [ ] Insert into prompt at designated location
  - [ ] Implement `load_schema(artifact_type) -> dict`
    - [ ] Read JSON file from schemas directory
    - [ ] Cache schemas for performance

### Prompt Exports
- [ ] Update module exports to expose PromptManager

### Unit Tests
- [ ] Create `tests/unit/domain/prompts/test_prompt_manager.py`
  - [ ] Test `get_base_prompt()` returns canonical prompt
  - [ ] Test `get_pass_prompt(PROJECT)` returns project planner prompt
  - [ ] Test `get_system_prompt(PROJECT)` combines base + pass prompts
  - [ ] Test all 6 pass prompts are defined
  - [ ] Test prompts contain required elements (purpose, rules)
  - [ ] Test `get_full_prompt()` includes context and schema

- [ ] Create `tests/unit/domain/prompts/test_base.py`
  - [ ] Test `BASE_SYSTEM_PROMPT` contains all 7 rules
  - [ ] Test `FAILURE_FORMAT` is valid JSON template

- [ ] Create `tests/unit/domain/prompts/test_schema_injector.py`
  - [ ] Test `load_schema` loads valid JSON
  - [ ] Test `load_schema` raises for missing schema
  - [ ] Test `inject_schema` inserts schema into prompt
  - [ ] Test schema caching works

## Acceptance Criteria

- [ ] Global system prompt matches spec exactly (verbatim)
- [ ] Each pass has purpose, inputs, rules, and schema reference
- [ ] Prompts are pure strings (no external dependencies)
- [ ] Schema injection works for all 7 artifact types
- [ ] PromptManager provides easy access to all prompts
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

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
