# F15-01: Ollama Adapter - Tasks

---

## Tasks

### T15-01-01: Create Ollama Adapter Base
- [x] Files: `rice_factor/adapters/llm/ollama_adapter.py`
- Created OllamaClient and OllamaAdapter classes

### T15-01-02: Implement generate() Method
- [x] Files: `rice_factor/adapters/llm/ollama_adapter.py`
- Implemented sync generate() with httpx/requests fallback

### T15-01-03: Implement Streaming Support
- [x] Files: `rice_factor/adapters/llm/ollama_adapter.py`
- Implemented async streaming via generate_async()

### T15-01-04: Implement list_models() Method
- [x] Files: `rice_factor/adapters/llm/ollama_adapter.py`
- Uses /api/tags endpoint

### T15-01-05: Implement is_available() Health Check
- [x] Files: `rice_factor/adapters/llm/ollama_adapter.py`
- Checks server root endpoint, supports sync and async

### T15-01-06: Add Ollama to Provider Configuration
- [x] Files: `rice_factor/adapters/llm/__init__.py`
- Added OllamaAdapter to __init__.py exports and LLMAdapter type alias
- Added create_ollama_adapter_from_config factory function
- Updated create_llm_adapter_from_config to support "ollama" provider

### T15-01-07: Unit Tests for Ollama Adapter
- [x] Files: `tests/unit/adapters/llm/test_ollama_adapter.py`
- 28 tests covering client, adapter, and config

---

## Actual Test Count: 28
