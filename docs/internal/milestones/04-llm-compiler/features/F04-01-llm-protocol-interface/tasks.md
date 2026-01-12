# Feature: F04-01 LLM Protocol Interface

## Status: Complete

## Description

Define the abstract LLM interface (Protocol) that all provider adapters must implement. This is the core port in the hexagonal architecture that decouples the domain from specific LLM providers.

## Requirements Reference

- M04-U-001: The LLM shall output valid JSON only
- M04-U-002: The LLM shall output exactly one artifact per invocation
- M04-U-007: LLM temperature shall be 0.0-0.2 for determinism
- 03-Artifact-Builder.md: 3.2 Hard Contract, 3.12 Determinism Controls

## Tasks

### LLM Port Definition
- [ ] Create `rice_factor/domain/ports/llm.py`
  - [ ] Define `LLMPort` Protocol class
  - [ ] Define `generate(pass_type, context, schema) -> CompilerResult` method signature
  - [ ] Include docstrings with contract specification
  - [ ] No external dependencies (Protocol from typing only)

### Compiler Types Module
- [ ] Create `rice_factor/domain/artifacts/compiler_types.py`
  - [ ] Define `CompilerPassType` enum
    - [ ] PROJECT, ARCHITECTURE, SCAFFOLD, TEST, IMPLEMENTATION, REFACTOR
  - [ ] Define `CompilerContext` dataclass
    - [ ] `pass_type: CompilerPassType`
    - [ ] `project_files: dict[str, str]` (path -> content)
    - [ ] `artifacts: dict[str, Any]` (artifact_id -> payload)
    - [ ] `target_file: str | None` (for implementation pass)
  - [ ] Define `CompilerResult` dataclass
    - [ ] `success: bool`
    - [ ] `payload: dict | None`
    - [ ] `error_type: str | None`
    - [ ] `error_details: str | None`
    - [ ] `raw_response: str | None`
  - [ ] Define `LLMParameters` dataclass
    - [ ] `temperature: float` (default 0.0)
    - [ ] `top_p: float` (default 0.3)
    - [ ] `max_tokens: int` (default 4096)
    - [ ] `timeout: int` (default 120)

### Context Builder Service
- [ ] Create `rice_factor/domain/services/context_builder.py`
  - [ ] Define `ContextBuilder` class
  - [ ] Implement `build_context(pass_type, project_root) -> CompilerContext`
    - [ ] Load `.project/` files for planning passes
    - [ ] Load approved artifacts from storage
    - [ ] Handle target file for implementation pass
  - [ ] Implement `validate_inputs(pass_type, context) -> bool`
    - [ ] Check required inputs present per pass type
  - [ ] Implement `check_forbidden_inputs(pass_type, context) -> list[str]`
    - [ ] Return list of forbidden inputs found
  - [ ] Define `PASS_REQUIREMENTS` mapping
    - [ ] Required inputs per pass
    - [ ] Forbidden inputs per pass

### Port Exports
- [ ] Update `rice_factor/domain/ports/__init__.py`
  - [ ] Export `LLMPort`
- [ ] Update `rice_factor/domain/artifacts/__init__.py`
  - [ ] Export `CompilerPassType`
  - [ ] Export `CompilerContext`
  - [ ] Export `CompilerResult`
  - [ ] Export `LLMParameters`
- [ ] Update `rice_factor/domain/services/__init__.py`
  - [ ] Export `ContextBuilder`

### Unit Tests
- [ ] Create `tests/unit/domain/ports/test_llm.py`
  - [ ] Test `LLMPort` is a valid Protocol
  - [ ] Test protocol methods are defined
- [ ] Create `tests/unit/domain/artifacts/test_compiler_types.py`
  - [ ] Test `CompilerPassType` enum has all 6 values
  - [ ] Test `CompilerContext` creation and validation
  - [ ] Test `CompilerResult` for success case
  - [ ] Test `CompilerResult` for error case
  - [ ] Test `LLMParameters` defaults
- [ ] Create `tests/unit/domain/services/test_context_builder.py`
  - [ ] Test `build_context` for PROJECT pass
  - [ ] Test `build_context` for IMPLEMENTATION pass with target file
  - [ ] Test `validate_inputs` returns True for valid context
  - [ ] Test `validate_inputs` returns False for missing inputs
  - [ ] Test `check_forbidden_inputs` detects source code for PROJECT pass
  - [ ] Test `check_forbidden_inputs` returns empty for valid context

## Acceptance Criteria

- [ ] `LLMPort` Protocol defined in `domain/ports/llm.py`
- [ ] All 6 compiler pass types enumerated
- [ ] `CompilerContext` captures all necessary input data
- [ ] `CompilerResult` handles both success and error cases
- [ ] `ContextBuilder` correctly gathers inputs per pass type
- [ ] Forbidden inputs are detected and reported
- [ ] Protocol has no external dependencies (stdlib only)
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/ports/llm.py` | CREATE | LLM port protocol definition |
| `rice_factor/domain/artifacts/compiler_types.py` | CREATE | Compiler-related types |
| `rice_factor/domain/services/context_builder.py` | CREATE | Context builder service |
| `rice_factor/domain/ports/__init__.py` | UPDATE | Export LLMPort |
| `rice_factor/domain/artifacts/__init__.py` | UPDATE | Export compiler types |
| `rice_factor/domain/services/__init__.py` | UPDATE | Export ContextBuilder |
| `tests/unit/domain/ports/test_llm.py` | CREATE | Port tests |
| `tests/unit/domain/artifacts/test_compiler_types.py` | CREATE | Compiler types tests |
| `tests/unit/domain/services/test_context_builder.py` | CREATE | Context builder tests |

## Dependencies

- None (foundation feature)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
