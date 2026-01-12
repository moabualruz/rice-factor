# F15-03: OpenAI-Compatible Generic Adapter - Tasks

---

## Tasks

### T15-03-01: Create Generic OpenAI-Compat Adapter
- [x] Files: `rice_factor/adapters/llm/openai_compat_adapter.py`
- Created OpenAICompatClient and OpenAICompatAdapter classes

### T15-03-02: Implement Configurable Base URL
- [x] Files: `rice_factor/adapters/llm/openai_compat_adapter.py`
- Fully configurable base_url, supports any OpenAI-compatible endpoint

### T15-03-03: Implement Model Auto-Discovery
- [x] Files: `rice_factor/adapters/llm/openai_compat_adapter.py`
- list_models() via /v1/models endpoint, KNOWN_PROVIDERS default models

### T15-03-04: Support LM Studio Integration
- [x] Files: `rice_factor/adapters/llm/openai_compat_adapter.py`
- Provider "lmstudio" with default URL http://localhost:1234/v1

### T15-03-05: Support LocalAI Integration
- [x] Files: `rice_factor/adapters/llm/openai_compat_adapter.py`
- Provider "localai" with default URL http://localhost:8080/v1
- Also supports "tgi" (Text Generation Inference) and "generic"

### T15-03-06: Unit Tests for OpenAI-Compat Adapter
- [x] Files: `tests/unit/adapters/llm/test_openai_compat_adapter.py`
- 37 tests covering providers, client, adapter, and config

---

## Actual Test Count: 37
