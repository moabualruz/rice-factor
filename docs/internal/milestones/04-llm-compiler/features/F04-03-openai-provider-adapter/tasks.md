# Feature: F04-03 OpenAI Provider Adapter

## Status: Complete
## Priority: P1 (Secondary)

## Description

Implement the OpenAI API adapter as an alternative LLM provider, implementing the same `LLMPort` protocol. Supports both OpenAI and Azure OpenAI endpoints.

## Requirements Reference

- M04-U-007: LLM temperature shall be 0.0-0.2 for determinism
- 03-Artifact-Builder.md: 3.12 Determinism Controls

## Tasks

### OpenAI Adapter Implementation
- [x] Create `rice_factor/adapters/llm/openai_adapter.py`
  - [x] Define `OpenAIAdapter` class implementing `LLMPort`
  - [x] Implement `__init__(api_key, model, config: LLMParameters, azure_endpoint=None)`
  - [x] Implement `generate(pass_type, context, schema) -> CompilerResult`
    - [x] Build system message from PromptManager
    - [x] Build user message from context
    - [x] Use JSON mode for structured output (`response_format={"type": "json_object"}`)
    - [x] Call OpenAI API with determinism parameters
    - [x] Extract JSON from response
    - [x] Return `CompilerResult`
  - [x] Implement `_build_messages(pass_type, context, schema) -> list[dict]`
  - [x] Enforce determinism: temperature=0.0, top_p=0.3

### OpenAI API Client
- [x] Create `rice_factor/adapters/llm/openai_client.py`
  - [x] Define `OpenAIClient` class
  - [x] Implement `__init__(api_key, timeout, azure_endpoint=None)`
  - [x] Implement `create_chat_completion(model, messages, **kwargs) -> dict`
  - [x] Implement retry logic with exponential backoff
  - [x] Implement rate limit handling
  - [x] Support Azure OpenAI endpoint configuration
    - [x] Different base URL
    - [x] API version parameter
    - [x] Azure AD authentication option

### Configuration Management
- [x] Update `rice_factor/config/defaults.yaml`
  - [x] Add `openai.model` setting (default: gpt-4-turbo)
  - [x] Add `azure.openai_endpoint` optional setting
  - [x] Add `azure.openai_api_version` optional setting
  - [x] Add `llm.provider` setting (claude | openai | stub)

### Adapter Registration
- [x] Update `rice_factor/adapters/llm/__init__.py`
  - [x] Export `OpenAIAdapter`
  - [x] Export `OpenAIClient`
  - [x] Export `create_openai_adapter_from_config`

### Unit Tests
- [x] Create `tests/unit/adapters/llm/test_openai.py`
  - [x] Test adapter instantiation with valid config
  - [x] Test `_build_messages` creates correct structure
  - [x] Test JSON mode is enabled
  - [x] Test determinism parameters are enforced
  - [x] Test successful `generate` returns CompilerResult with payload
  - [x] Test `generate` handles API error
  - [x] Test `generate` handles timeout
  - [x] Mock `openai.OpenAI` for all tests
- [x] Create `tests/unit/adapters/llm/test_openai_client.py`
  - [x] Test standard OpenAI endpoint
  - [x] Test Azure OpenAI endpoint configuration
  - [x] Test retry logic
  - [x] Test rate limit handling

## Acceptance Criteria

- [x] `OpenAIAdapter` implements `LLMPort` protocol
- [x] API key loaded from environment variable
- [x] JSON mode enabled for structured output
- [x] Determinism parameters enforced
- [x] Azure OpenAI endpoint supported
- [x] Provider can be selected via configuration
- [x] All tests pass (mocked API)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/llm/openai_adapter.py` | CREATE | OpenAI adapter implementation |
| `rice_factor/adapters/llm/openai_client.py` | CREATE | Low-level API client |
| `rice_factor/adapters/llm/__init__.py` | UPDATE | Export adapters |
| `rice_factor/config/defaults.yaml` | UPDATE | Add OpenAI/Azure configuration |
| `pyproject.toml` | UPDATE | Add openai to mypy overrides |
| `tests/unit/adapters/llm/test_openai.py` | CREATE | OpenAI adapter tests (19 tests) |
| `tests/unit/adapters/llm/test_openai_client.py` | CREATE | Client tests (14 tests) |

## Dependencies

- F04-01: LLM Protocol Interface (LLMPort, CompilerResult)
- F04-05: System Prompts (PromptManager)
- F04-06: Structured Output Enforcement (JSON extraction)
- F04-07: Error Handling (LLMAPIError, LLMTimeoutError)

## External Dependencies

- `openai` Python SDK (optional - graceful fallback when not installed)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | F04-03 implementation complete - OpenAI adapter with Azure support, retry logic, JSON mode |
