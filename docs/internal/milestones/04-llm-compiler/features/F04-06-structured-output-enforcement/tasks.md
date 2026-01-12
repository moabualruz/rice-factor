# Feature: F04-06 Structured Output Enforcement

## Status: Complete

## Description

Implement the validation layer that ensures LLM outputs conform exactly to the expected JSON schema. This includes JSON extraction, schema validation, and response rejection for non-conforming outputs.

## Requirements Reference

- M04-U-001: The LLM shall output valid JSON only
- M04-U-005: The LLM shall conform exactly to the provided JSON Schema
- M04-E-001: As soon as the LLM returns output, the system shall validate against JSON Schema
- M04-I-001: If LLM outputs non-JSON, then the system shall reject the response
- M04-I-002: If LLM outputs code, then the system shall reject the response
- M04-I-003: If LLM outputs multiple artifacts, then the system shall reject the response

## Tasks

### JSON Extractor
- [x] Create `rice_factor/domain/services/json_extractor.py`
  - [x] Define `JSONExtractor` class
  - [x] Implement `extract(raw_response: str) -> str`
    - [x] Handle raw JSON responses (starts with `{`)
    - [x] Handle markdown code fences (```json ... ```)
    - [x] Handle triple backticks without language tag
    - [x] Strip leading/trailing whitespace
    - [x] Raise `InvalidJSONError` if no JSON found
  - [x] Implement `_find_json_in_fences(response: str) -> str | None`
    - [x] Use regex to find JSON within code fences
  - [x] Implement `_find_json_object(response: str) -> str | None`
    - [x] Match braces to find JSON object boundaries
  - [x] Implement `_has_multiple_json_objects(response: str) -> bool`
    - [x] Detect multiple top-level JSON objects
    - [x] Raise `MultipleArtifactsError` if found
  - [x] Implement `_has_explanatory_text(response: str, json_str: str) -> bool`
    - [x] Check for significant text outside JSON
    - [x] Raise `ExplanatoryTextError` if found
  - [x] Define `extract_json()` convenience function

### Output Validator
- [x] Create `rice_factor/domain/services/output_validator.py`
  - [x] Define `OutputValidator` class
  - [x] Implement `__init__(schema_dir: Path, check_code: bool)`
  - [x] Implement `validate(json_str: str, artifact_type: ArtifactType) -> dict`
    - [x] Parse JSON string to dict
    - [x] Validate payload against type-specific schema
    - [x] Check for code in payload
    - [x] Return validated dict or raise error
  - [x] Implement `validate_envelope(json_str: str) -> dict`
    - [x] Validate against envelope schema
    - [x] Extract artifact type and validate payload
  - [x] Implement `_parse_json(json_str: str) -> dict`
    - [x] Use json.loads with error handling
    - [x] Raise `InvalidJSONError` on parse failure
  - [x] Implement `_validate_schema(data: dict, artifact_type: ArtifactType)`
    - [x] Load schema for artifact type
    - [x] Use jsonschema library
    - [x] Raise `SchemaViolationError` on mismatch
  - [x] Implement `_check_for_code(data: dict)`
    - [x] Delegate to CodeDetector
    - [x] Raise `CodeInOutputError` if found
  - [x] Define `validate_llm_output()` convenience function

### Code Detector
- [x] Create `rice_factor/domain/services/code_detector.py`
  - [x] Define `CodeDetector` class
  - [x] Implement `contains_code(data: Any) -> tuple[bool, str | None]`
    - [x] Recursively check all string values via `_check_recursive()`
    - [x] Return (found, location) tuple
  - [x] Implement `_is_code_snippet(text: str) -> bool`
    - [x] Check for common code patterns:
      - [x] `def `, `class `, `import `, `from ` (Python)
      - [x] `function `, `const `, `let `, `var ` (JavaScript)
      - [x] `fn `, `impl `, `struct `, `mod ` (Rust)
      - [x] `func `, `package `, `type ` (Go)
      - [x] Java patterns (public/private class, etc.)
    - [x] Check for code block markers (```)
    - [x] Avoid false positives on prose descriptions
  - [x] Implement `_is_likely_code(text: str) -> float`
    - [x] Return confidence score 0.0-1.0
    - [x] Consider syntax density via `_calculate_syntax_density()`
    - [x] Consider indentation patterns
  - [x] Define `detect_code()` convenience function

### Error Types
- [x] Update `rice_factor/domain/failures/llm_errors.py`
  - [x] Define `LLMOutputError(LLMError)` base class
  - [x] Define `InvalidJSONError(LLMOutputError)`
    - [x] Include raw response snippet
    - [x] Include parse error message
  - [x] Define `SchemaViolationError(LLMOutputError)`
    - [x] Include schema path
    - [x] Include validation errors list
  - [x] Define `CodeInOutputError(LLMOutputError)`
    - [x] Include location in artifact
    - [x] Include code snippet
  - [x] Define `MultipleArtifactsError(LLMOutputError)`
    - [x] Include count of objects found
  - [x] Define `ExplanatoryTextError(LLMOutputError)`
    - [x] Include text snippet

### Integration with Validator Port
- [x] OutputValidator provides standalone validation
- [x] Convenience functions `validate_llm_output()` and `extract_json()` available
- [x] Integration point available for adapters

### Service Exports
- [x] Update `rice_factor/domain/services/__init__.py`
  - [x] Export `JSONExtractor`
  - [x] Export `OutputValidator`
  - [x] Export `CodeDetector`
- [x] Update `rice_factor/domain/failures/__init__.py`
  - [x] Export all LLM output error types

### Unit Tests
- [x] Create `tests/unit/domain/services/test_json_extractor.py`
  - [x] Test extraction from raw JSON string
  - [x] Test extraction from ```json fenced block
  - [x] Test extraction from ``` fenced block (no lang)
  - [x] Test rejection of non-JSON response
  - [x] Test rejection of multiple JSON objects
  - [x] Test rejection of JSON with explanatory text
  - [x] Test edge cases (empty response, whitespace only)

- [x] Create `tests/unit/domain/services/test_output_validator.py`
  - [x] Test valid artifact passes validation
  - [x] Test invalid JSON raises InvalidJSONError
  - [x] Test schema violation raises SchemaViolationError
  - [x] Test code detection raises CodeInOutputError
  - [x] Test validation for each artifact type

- [x] Create `tests/unit/domain/services/test_code_detector.py`
  - [x] Test Python code detection (`def foo():`)
  - [x] Test JavaScript code detection (`function bar()`)
  - [x] Test Rust code detection (`fn main()`)
  - [x] Test Go code detection (`func main()`)
  - [x] Test code block detection (```)
  - [x] Test false positive avoidance (prose with "function" word)
  - [x] Test nested structure traversal

- [x] LLM output error tests included in test_llm_errors.py

## Acceptance Criteria

- [x] Valid JSON is extracted from various response formats
- [x] Invalid JSON is rejected with clear error message
- [x] Schema violations are caught and reported with details
- [x] Code in output is detected and rejected
- [x] Multiple artifacts are rejected
- [x] Explanatory text outside JSON is rejected
- [x] All tests pass (93 tests)
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/services/json_extractor.py` | CREATE | JSON extraction from LLM output |
| `rice_factor/domain/services/output_validator.py` | CREATE | Output validation service |
| `rice_factor/domain/services/code_detector.py` | CREATE | Code detection in artifacts |
| `rice_factor/domain/failures/llm_errors.py` | UPDATE | Add output error types |
| `rice_factor/domain/failures/__init__.py` | UPDATE | Export LLM errors |
| `rice_factor/domain/services/__init__.py` | UPDATE | Export validation services |
| `rice_factor/adapters/validators/artifact_validator.py` | UPDATE | Add LLM output validation |
| `tests/unit/domain/services/test_json_extractor.py` | CREATE | Extractor tests |
| `tests/unit/domain/services/test_output_validator.py` | CREATE | Validator tests |
| `tests/unit/domain/services/test_code_detector.py` | CREATE | Code detector tests |
| `tests/unit/domain/failures/test_llm_output_errors.py` | CREATE | Error tests |

## Dependencies

- F04-01: LLM Protocol Interface (CompilerResult)
- F04-07: Error Handling (LLMError base class)
- M02: Artifact System (JSON schemas, ArtifactType)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation verified complete - 93 tests pass |
