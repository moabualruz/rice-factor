# Feature: F04-06 Structured Output Enforcement

## Status: Pending

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
- [ ] Create `rice_factor/domain/services/json_extractor.py`
  - [ ] Define `JSONExtractor` class
  - [ ] Implement `extract(raw_response: str) -> str`
    - [ ] Handle raw JSON responses (starts with `{`)
    - [ ] Handle markdown code fences (```json ... ```)
    - [ ] Handle triple backticks without language tag
    - [ ] Strip leading/trailing whitespace
    - [ ] Raise `InvalidJSONError` if no JSON found
  - [ ] Implement `_find_json_in_fences(response: str) -> str | None`
    - [ ] Use regex to find JSON within code fences
  - [ ] Implement `_has_multiple_json_objects(response: str) -> bool`
    - [ ] Detect multiple top-level JSON objects
    - [ ] Raise `MultipleArtifactsError` if found
  - [ ] Implement `_has_explanatory_text(response: str, json_str: str) -> bool`
    - [ ] Check for significant text outside JSON
    - [ ] Raise `ExplanatoryTextError` if found

### Output Validator
- [ ] Create `rice_factor/domain/services/output_validator.py`
  - [ ] Define `OutputValidator` class
  - [ ] Implement `__init__(schema_dir: Path)`
  - [ ] Implement `validate(json_str: str, artifact_type: ArtifactType) -> dict`
    - [ ] Parse JSON string to dict
    - [ ] Validate against envelope schema
    - [ ] Validate payload against type-specific schema
    - [ ] Check for code in payload
    - [ ] Return validated dict or raise error
  - [ ] Implement `_parse_json(json_str: str) -> dict`
    - [ ] Use json.loads with error handling
    - [ ] Raise `InvalidJSONError` on parse failure
  - [ ] Implement `_validate_schema(data: dict, artifact_type: ArtifactType)`
    - [ ] Load schema for artifact type
    - [ ] Use jsonschema library
    - [ ] Raise `SchemaViolationError` on mismatch
  - [ ] Implement `_check_for_code(data: dict)`
    - [ ] Delegate to CodeDetector
    - [ ] Raise `CodeInOutputError` if found

### Code Detector
- [ ] Create `rice_factor/domain/services/code_detector.py`
  - [ ] Define `CodeDetector` class
  - [ ] Implement `contains_code(data: Any) -> tuple[bool, str | None]`
    - [ ] Recursively check all string values
    - [ ] Return (found, location) tuple
  - [ ] Implement `_is_code_snippet(text: str) -> bool`
    - [ ] Check for common code patterns:
      - [ ] `def `, `class `, `import `, `from ` (Python)
      - [ ] `function `, `const `, `let `, `var ` (JavaScript)
      - [ ] `fn `, `impl `, `struct `, `mod ` (Rust)
      - [ ] `func `, `package `, `type ` (Go)
      - [ ] Generic: `{`, `}`, `=>`, `->`, `()` combinations
    - [ ] Check for code block markers (```)
    - [ ] Avoid false positives on prose descriptions
  - [ ] Implement `_is_likely_code(text: str) -> float`
    - [ ] Return confidence score 0.0-1.0
    - [ ] Consider syntax density
    - [ ] Consider indentation patterns

### Error Types
- [ ] Update `rice_factor/domain/failures/llm_errors.py`
  - [ ] Define `LLMOutputError(LLMError)` base class
  - [ ] Define `InvalidJSONError(LLMOutputError)`
    - [ ] Include raw response snippet
    - [ ] Include parse error message
  - [ ] Define `SchemaViolationError(LLMOutputError)`
    - [ ] Include schema path
    - [ ] Include validation errors
  - [ ] Define `CodeInOutputError(LLMOutputError)`
    - [ ] Include location in artifact
    - [ ] Include code snippet
  - [ ] Define `MultipleArtifactsError(LLMOutputError)`
    - [ ] Include count of objects found
  - [ ] Define `ExplanatoryTextError(LLMOutputError)`
    - [ ] Include text snippet

### Integration with Validator Port
- [ ] Update `rice_factor/adapters/validators/artifact_validator.py`
  - [ ] Add `validate_llm_output(raw_response, artifact_type) -> dict`
  - [ ] Integrate JSONExtractor
  - [ ] Integrate OutputValidator
  - [ ] Return validated artifact or raise appropriate error

### Service Exports
- [ ] Update `rice_factor/domain/services/__init__.py`
  - [ ] Export `JSONExtractor`
  - [ ] Export `OutputValidator`
  - [ ] Export `CodeDetector`
- [ ] Update `rice_factor/domain/failures/__init__.py`
  - [ ] Export all LLM output error types

### Unit Tests
- [ ] Create `tests/unit/domain/services/test_json_extractor.py`
  - [ ] Test extraction from raw JSON string
  - [ ] Test extraction from ```json fenced block
  - [ ] Test extraction from ``` fenced block (no lang)
  - [ ] Test rejection of non-JSON response
  - [ ] Test rejection of multiple JSON objects
  - [ ] Test rejection of JSON with explanatory text
  - [ ] Test edge cases (empty response, whitespace only)

- [ ] Create `tests/unit/domain/services/test_output_validator.py`
  - [ ] Test valid artifact passes validation
  - [ ] Test invalid JSON raises InvalidJSONError
  - [ ] Test schema violation raises SchemaViolationError
  - [ ] Test code detection raises CodeInOutputError
  - [ ] Test validation for each artifact type

- [ ] Create `tests/unit/domain/services/test_code_detector.py`
  - [ ] Test Python code detection (`def foo():`)
  - [ ] Test JavaScript code detection (`function bar()`)
  - [ ] Test Rust code detection (`fn main()`)
  - [ ] Test Go code detection (`func main()`)
  - [ ] Test code block detection (```)
  - [ ] Test false positive avoidance (prose with "function" word)
  - [ ] Test nested structure traversal

- [ ] Create `tests/unit/domain/failures/test_llm_output_errors.py`
  - [ ] Test error hierarchy
  - [ ] Test error message formatting
  - [ ] Test error attributes

## Acceptance Criteria

- [ ] Valid JSON is extracted from various response formats
- [ ] Invalid JSON is rejected with clear error message
- [ ] Schema violations are caught and reported with details
- [ ] Code in output is detected and rejected
- [ ] Multiple artifacts are rejected
- [ ] Explanatory text outside JSON is rejected
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

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
