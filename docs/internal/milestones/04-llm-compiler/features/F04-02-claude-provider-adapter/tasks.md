# Feature: F04-02 Claude Provider Adapter

## Status: Complete

## Description

Implement the Claude API adapter that implements `LLMPort`. This is the primary LLM provider for Rice-Factor, using the Anthropic SDK.

## Requirements Reference

- M04-U-007: LLM temperature shall be 0.0-0.2 for determinism
- 03-Artifact-Builder.md: 3.12 Determinism Controls (temp 0-0.2, top-p <= 0.3, no streaming)

## Tasks

### Claude Adapter Implementation
- [x] Create `rice_factor/adapters/llm/claude.py`
  - [x] Define `ClaudeAdapter` class implementing `LLMPort`
  - [x] Implement `__init__(api_key, model, config: LLMParameters)`
  - [x] Implement `generate(pass_type, context, schema) -> CompilerResult`
    - [x] Build system message from PromptManager
    - [x] Build user message from context
    - [x] Inject schema into prompt
    - [x] Call Claude API with determinism parameters
    - [x] Extract JSON from response
    - [x] Return `CompilerResult`
  - [x] Implement `_build_messages(pass_type, context, schema) -> list[dict]`
  - [x] Implement `_extract_json(response) -> str`
    - [x] Handle markdown code fences
    - [x] Handle raw JSON
  - [x] Enforce determinism: temperature=0.0, top_p=0.3, no streaming

### Claude API Client
- [x] Create `rice_factor/adapters/llm/claude_client.py`
  - [x] Define `ClaudeClient` class
  - [x] Implement `__init__(api_key, timeout)`
  - [x] Implement `create_message(model, messages, **kwargs) -> dict`
  - [x] Implement retry logic with exponential backoff
    - [x] Retry on transient errors (5xx, timeout)
    - [x] Max 3 retries with 1s, 2s, 4s delays
  - [x] Implement rate limit handling
    - [x] Respect Retry-After header
  - [x] Implement timeout handling
  - [x] Support both direct API and future Bedrock endpoints (flag)

### Configuration Management
- [x] Update `rice_factor/config/defaults.yaml`
  - [x] Add `llm.provider` setting (default: claude)
  - [x] Add `llm.model` setting (default: claude-3-5-sonnet-20241022)
  - [x] Add `llm.temperature` setting (default: 0.0)
  - [x] Add `llm.top_p` setting (default: 0.3)
  - [x] Add `llm.max_tokens` setting (default: 4096)
  - [x] Add `llm.timeout` setting (default: 120)
  - [x] Add `llm.max_retries` setting (default: 3)

### Adapter Registration
- [x] Update `rice_factor/adapters/llm/__init__.py`
  - [x] Export `ClaudeAdapter`
  - [x] Export `ClaudeClient`
  - [x] Export `create_claude_adapter_from_config`

### Unit Tests
- [x] Create `tests/unit/adapters/llm/test_claude.py`
  - [x] Test adapter instantiation with valid config
  - [x] Test `_build_messages` creates correct structure
  - [x] Test determinism parameters are enforced
  - [x] Test `_extract_json` from raw JSON
  - [x] Test `_extract_json` from markdown fenced JSON
  - [x] Test successful `generate` returns CompilerResult with payload
  - [x] Test `generate` handles API error
  - [x] Test `generate` handles timeout
  - [x] Mock `anthropic.Anthropic` for all tests
- [x] Create `tests/unit/adapters/llm/test_claude_client.py`
  - [x] Test retry logic on 5xx errors
  - [x] Test rate limit handling
  - [x] Test timeout raises `LLMTimeoutError`
  - [x] Test successful API call

## Acceptance Criteria

- [x] `ClaudeAdapter` implements `LLMPort` protocol
- [x] API key loaded from environment variable
- [x] Determinism parameters enforced (temp=0.0, top_p=0.3)
- [x] JSON correctly extracted from various response formats
- [x] Retry logic handles transient failures
- [x] Rate limiting is respected
- [x] Timeout handling prevents hanging
- [x] All tests pass (mocked API)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/llm/claude.py` | CREATE | Claude adapter implementation |
| `rice_factor/adapters/llm/claude_client.py` | CREATE | Low-level API client |
| `rice_factor/adapters/llm/__init__.py` | UPDATE | Export adapters |
| `rice_factor/config/defaults.yaml` | UPDATE | Add Claude configuration |
| `pyproject.toml` | UPDATE | Add anthropic to mypy overrides |
| `tests/unit/adapters/llm/test_claude.py` | CREATE | Claude adapter tests (18 tests) |
| `tests/unit/adapters/llm/test_claude_client.py` | CREATE | Client tests (14 tests) |

## Dependencies

- F04-01: LLM Protocol Interface (LLMPort, CompilerResult)
- F04-05: System Prompts (PromptManager)
- F04-06: Structured Output Enforcement (JSON extraction)
- F04-07: Error Handling (LLMAPIError, LLMTimeoutError)

## External Dependencies

- `anthropic` Python SDK (optional - graceful fallback when not installed)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | F04-02 implementation complete - Claude adapter with retry logic, rate limit handling, determinism controls |
