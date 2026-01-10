# Feature: F04-07 Error Handling

## Status: Complete

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
- [x] Create `rice_factor/domain/failures/llm_errors.py`
  - [x] Define `LLMError(Exception)` base class
    - [x] Include `message`, `details`, `recoverable` attributes
  - [x] Define `LLMAPIError(LLMError)`
    - [x] For provider API failures (5xx, network errors)
    - [x] Include `status_code`, `provider`
  - [x] Define `LLMTimeoutError(LLMError)`
    - [x] For request timeout
    - [x] Include `timeout_seconds`
  - [x] Define `LLMRateLimitError(LLMError)`
    - [x] For rate limiting responses
    - [x] Include `retry_after` seconds
  - [x] Define `LLMMissingInformationError(LLMError)`
    - [x] For explicit LLM `missing_information` response
    - [x] Include `missing_items` list
    - [x] `recoverable = False` (needs human input)
  - [x] Define `LLMInvalidRequestError(LLMError)`
    - [x] For explicit LLM `invalid_request` response
    - [x] Include `invalid_reason`

### Failure Parser
- [x] Create `rice_factor/domain/services/failure_parser.py`
  - [x] Define `FailureParser` class
  - [x] Implement `parse(response: str) -> LLMError | None`
    - [x] Try to parse response as JSON
    - [x] Check for `error` key
    - [x] Handle `{"error": "missing_information", "details": "..."}`
    - [x] Handle `{"error": "invalid_request", "details": "..."}`
    - [x] Return appropriate error type or None if not an error
  - [x] Implement `is_failure_response(data: dict) -> bool`
    - [x] Check if dict has `error` key
  - [x] Implement `_create_error(error_type: str, details: str) -> LLMError`
    - [x] Map error type string to error class

### FailureReport Payload
- [x] Create `rice_factor/domain/artifacts/payloads/failure_report.py`
  - [x] Define `FailureReportPayload(BaseModel)`
    - [x] `phase: str` - lifecycle phase where failure occurred
    - [x] `artifact_id: str | None` - related artifact if any
    - [x] `category: str` - error category (missing_information, invalid_request, api_error, etc.)
    - [x] `summary: str` - human-readable summary
    - [x] `details: dict` - detailed error information
    - [x] `blocking: bool` - whether this blocks progress
    - [x] `recovery_action: str` - recommended action (human_input_required, retry, abort)
    - [x] `timestamp: datetime`
  - [x] Add validation for required fields

### FailureReport Schema
- [x] Create `schemas/failure_report.schema.json`
  - [x] Define JSON Schema matching FailureReportPayload
  - [x] Include required fields
  - [x] Include enum values for category, recovery_action

### Artifact Type Update
- [x] Update `rice_factor/domain/artifacts/enums.py`
  - [x] Add `FAILURE_REPORT = "FailureReport"` to ArtifactType enum

### Failure Service
- [x] Create `rice_factor/domain/services/failure_service.py`
  - [x] Define `FailureService` class
  - [x] Implement `__init__(save_callback, load_callback)` (uses callbacks instead of direct storage)
  - [x] Implement `create_failure_report(error: LLMError, phase, artifact_id, raw_response) -> ArtifactEnvelope`
    - [x] Create FailureReportPayload from error
    - [x] Create ArtifactEnvelope with FAILURE_REPORT type
    - [x] Set status to DRAFT (can be resolved)
    - [x] Save via callback if provided
    - [x] Return envelope
  - [x] Implement `is_recoverable(error: LLMError) -> bool`
    - [x] Check error's `recoverable` attribute
    - [x] API errors and timeouts are recoverable (retry)
    - [x] Missing information is not recoverable (needs human)
  - [x] Implement `get_recovery_action(error: LLMError) -> RecoveryAction`
    - [x] Return RETRY for API/timeout errors
    - [x] Return HUMAN_INPUT_REQUIRED for missing info
    - [x] Return FIX_AND_RETRY for invalid request
  - [x] Implement `resolve_failure(failure_id: str, resolution: str)`
    - [x] Update failure report status to APPROVED
    - [x] Add resolution to details

### Error Handler Decorator
- [x] Create `rice_factor/domain/services/llm_error_handler.py`
  - [x] Define `@handle_llm_errors` decorator
  - [x] Catch `LLMError` and subclasses
  - [x] Log error with full context
  - [x] Create FailureReport for blocking errors
  - [x] Re-raise with enhanced context
  - [x] Support retry logic for recoverable errors
  - [x] Define `LLMErrorHandler` context manager (alternative to decorator)

### Error Exports
- [x] Update `rice_factor/domain/failures/__init__.py`
  - [x] Export all LLM error types
- [x] Update `rice_factor/domain/services/__init__.py`
  - [x] Export `FailureService`
  - [x] Export `FailureParser`
- [x] Update `rice_factor/domain/artifacts/payloads/__init__.py`
  - [x] Export `FailureReportPayload`

### Unit Tests
- [x] Create `tests/unit/domain/failures/test_llm_errors.py`
  - [x] Test `LLMError` base class
  - [x] Test `LLMAPIError` with status code
  - [x] Test `LLMTimeoutError` with timeout value
  - [x] Test `LLMRateLimitError` with retry_after
  - [x] Test `LLMMissingInformationError` is not recoverable
  - [x] Test `LLMInvalidRequestError`
  - [x] Test error message formatting

- [x] Create `tests/unit/domain/services/test_failure_parser.py`
  - [x] Test parsing `missing_information` error response
  - [x] Test parsing `invalid_request` error response
  - [x] Test parsing non-error response returns None
  - [x] Test parsing invalid JSON returns None
  - [x] Test `is_failure_response` detection

- [x] Create `tests/unit/domain/services/test_failure_service.py`
  - [x] Test `create_failure_report` creates valid envelope
  - [x] Test `is_recoverable` for each error type
  - [x] Test `get_recovery_action` returns correct action
  - [x] Test failure report saved to storage
  - [x] Test resolve_failure updates status

- [x] Create `tests/unit/domain/artifacts/payloads/test_failure_report.py`
  - [x] Test payload creation with all fields
  - [x] Test payload validation
  - [x] Test timestamp auto-generation

## Acceptance Criteria

- [x] All LLM error types defined with appropriate attributes
- [x] Explicit LLM failures (`missing_information`, `invalid_request`) parsed correctly
- [x] FailureReport artifacts created for blocking failures
- [x] Recovery actions correctly identified for each error type
- [x] Errors logged with full context via decorator/context manager
- [x] `@handle_llm_errors` decorator provides consistent error handling
- [x] All tests pass (98 tests)
- [x] mypy passes
- [x] ruff passes

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
| 2026-01-10 | Implementation verified complete - 98 tests pass |
