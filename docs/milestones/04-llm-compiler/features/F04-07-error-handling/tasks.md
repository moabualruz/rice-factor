# Feature: F04-07 Error Handling

## Status: Pending

## Description

Implement comprehensive error handling for LLM failures, including explicit failure responses from the LLM, API errors, timeout handling, and integration with the failure recovery model via FailureReport artifacts.

## Requirements Reference

- M04-U-006: The LLM shall fail explicitly if information is missing
- M04-U-010: Blocking failures shall create FailureReport artifacts
- M04-E-002: As soon as validation fails, the system shall reject and emit failure report
- M04-E-003: As soon as LLM returns `missing_information` error, the system shall halt for human input
- 03-Artifact-Builder.md: 3.11 Explicit Failure Handling
- item-05: Failure Taxonomy, FailureReport artifact

## Tasks

### LLM Error Types
- [ ] Create `rice_factor/domain/failures/llm_errors.py`
  - [ ] Define `LLMError(Exception)` base class
    - [ ] Include `message`, `details`, `recoverable` attributes
  - [ ] Define `LLMAPIError(LLMError)`
    - [ ] For provider API failures (5xx, network errors)
    - [ ] Include `status_code`, `provider`
  - [ ] Define `LLMTimeoutError(LLMError)`
    - [ ] For request timeout
    - [ ] Include `timeout_seconds`
  - [ ] Define `LLMRateLimitError(LLMError)`
    - [ ] For rate limiting responses
    - [ ] Include `retry_after` seconds
  - [ ] Define `LLMMissingInformationError(LLMError)`
    - [ ] For explicit LLM `missing_information` response
    - [ ] Include `missing_items` list
    - [ ] `recoverable = False` (needs human input)
  - [ ] Define `LLMInvalidRequestError(LLMError)`
    - [ ] For explicit LLM `invalid_request` response
    - [ ] Include `invalid_reason`

### Failure Parser
- [ ] Create `rice_factor/domain/services/failure_parser.py`
  - [ ] Define `FailureParser` class
  - [ ] Implement `parse(response: str) -> LLMError | None`
    - [ ] Try to parse response as JSON
    - [ ] Check for `error` key
    - [ ] Handle `{"error": "missing_information", "details": "..."}`
    - [ ] Handle `{"error": "invalid_request", "details": "..."}`
    - [ ] Return appropriate error type or None if not an error
  - [ ] Implement `is_failure_response(data: dict) -> bool`
    - [ ] Check if dict has `error` key
  - [ ] Implement `_create_error(error_type: str, details: str) -> LLMError`
    - [ ] Map error type string to error class

### FailureReport Payload
- [ ] Create `rice_factor/domain/artifacts/payloads/failure_report.py`
  - [ ] Define `FailureReportPayload(BaseModel)`
    - [ ] `phase: str` - lifecycle phase where failure occurred
    - [ ] `artifact_id: str | None` - related artifact if any
    - [ ] `category: str` - error category (missing_information, invalid_request, api_error, etc.)
    - [ ] `summary: str` - human-readable summary
    - [ ] `details: dict` - detailed error information
    - [ ] `blocking: bool` - whether this blocks progress
    - [ ] `recovery_action: str` - recommended action (human_input_required, retry, abort)
    - [ ] `timestamp: datetime`
  - [ ] Add validation for required fields

### FailureReport Schema
- [ ] Create `schemas/failure_report.schema.json`
  - [ ] Define JSON Schema matching FailureReportPayload
  - [ ] Include required fields
  - [ ] Include enum values for category, recovery_action

### Artifact Type Update
- [ ] Update `rice_factor/domain/artifacts/enums.py`
  - [ ] Add `FAILURE_REPORT = "failure_report"` to ArtifactType enum

### Failure Service
- [ ] Create `rice_factor/domain/services/failure_service.py`
  - [ ] Define `FailureService` class
  - [ ] Implement `__init__(storage, audit_service)`
  - [ ] Implement `create_failure_report(error: LLMError, context: dict) -> ArtifactEnvelope`
    - [ ] Create FailureReportPayload from error
    - [ ] Create ArtifactEnvelope with FAILURE_REPORT type
    - [ ] Set status to DRAFT (can be resolved)
    - [ ] Save to storage
    - [ ] Log to audit trail
    - [ ] Return envelope
  - [ ] Implement `is_recoverable(error: LLMError) -> bool`
    - [ ] Check error's `recoverable` attribute
    - [ ] API errors and timeouts are recoverable (retry)
    - [ ] Missing information is not recoverable (needs human)
  - [ ] Implement `get_recovery_action(error: LLMError) -> str`
    - [ ] Return "retry" for API/timeout errors
    - [ ] Return "human_input_required" for missing info
    - [ ] Return "abort" for invalid request
  - [ ] Implement `resolve_failure(failure_id: str, resolution: str)`
    - [ ] Update failure report status
    - [ ] Log resolution to audit

### Error Handler Decorator
- [ ] Create `rice_factor/domain/services/llm_error_handler.py`
  - [ ] Define `@handle_llm_errors` decorator
  - [ ] Catch `LLMError` and subclasses
  - [ ] Log error with full context
  - [ ] Create FailureReport for blocking errors
  - [ ] Re-raise with enhanced context
  - [ ] Support retry logic for recoverable errors

### Error Exports
- [ ] Update `rice_factor/domain/failures/__init__.py`
  - [ ] Export all LLM error types
- [ ] Update `rice_factor/domain/services/__init__.py`
  - [ ] Export `FailureService`
  - [ ] Export `FailureParser`
- [ ] Update `rice_factor/domain/artifacts/payloads/__init__.py`
  - [ ] Export `FailureReportPayload`

### Unit Tests
- [ ] Create `tests/unit/domain/failures/test_llm_errors.py`
  - [ ] Test `LLMError` base class
  - [ ] Test `LLMAPIError` with status code
  - [ ] Test `LLMTimeoutError` with timeout value
  - [ ] Test `LLMRateLimitError` with retry_after
  - [ ] Test `LLMMissingInformationError` is not recoverable
  - [ ] Test `LLMInvalidRequestError`
  - [ ] Test error message formatting

- [ ] Create `tests/unit/domain/services/test_failure_parser.py`
  - [ ] Test parsing `missing_information` error response
  - [ ] Test parsing `invalid_request` error response
  - [ ] Test parsing non-error response returns None
  - [ ] Test parsing invalid JSON returns None
  - [ ] Test `is_failure_response` detection

- [ ] Create `tests/unit/domain/services/test_failure_service.py`
  - [ ] Test `create_failure_report` creates valid envelope
  - [ ] Test `is_recoverable` for each error type
  - [ ] Test `get_recovery_action` returns correct action
  - [ ] Test failure report saved to storage
  - [ ] Test audit trail logging

- [ ] Create `tests/unit/domain/artifacts/payloads/test_failure_report.py`
  - [ ] Test payload creation with all fields
  - [ ] Test payload validation
  - [ ] Test timestamp auto-generation

## Acceptance Criteria

- [ ] All LLM error types defined with appropriate attributes
- [ ] Explicit LLM failures (`missing_information`, `invalid_request`) parsed correctly
- [ ] FailureReport artifacts created for blocking failures
- [ ] Recovery actions correctly identified for each error type
- [ ] Errors logged with full context to audit trail
- [ ] `@handle_llm_errors` decorator provides consistent error handling
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/domain/failures/llm_errors.py` | CREATE | LLM error types |
| `rice_factor/domain/services/failure_parser.py` | CREATE | LLM failure response parser |
| `rice_factor/domain/artifacts/payloads/failure_report.py` | CREATE | FailureReport payload model |
| `rice_factor/domain/services/failure_service.py` | CREATE | Failure handling service |
| `rice_factor/domain/services/llm_error_handler.py` | CREATE | Error handler decorator |
| `rice_factor/domain/artifacts/enums.py` | UPDATE | Add FAILURE_REPORT type |
| `rice_factor/domain/failures/__init__.py` | UPDATE | Export LLM errors |
| `rice_factor/domain/services/__init__.py` | UPDATE | Export failure services |
| `rice_factor/domain/artifacts/payloads/__init__.py` | UPDATE | Export FailureReportPayload |
| `schemas/failure_report.schema.json` | CREATE | JSON Schema for FailureReport |
| `tests/unit/domain/failures/test_llm_errors.py` | CREATE | Error tests |
| `tests/unit/domain/services/test_failure_parser.py` | CREATE | Parser tests |
| `tests/unit/domain/services/test_failure_service.py` | CREATE | Service tests |
| `tests/unit/domain/artifacts/payloads/test_failure_report.py` | CREATE | Payload tests |

## Dependencies

- F04-01: LLM Protocol Interface (for integration)
- M02: Artifact System (ArtifactEnvelope, storage, ArtifactType enum)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
