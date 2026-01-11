# Milestone 15: Local LLM Orchestration - Requirements

> **Status**: Planned
> **Priority**: P0 (Cost reduction, privacy, offline mode)
> **Dependencies**: None

---

## 1. Overview

Support locally installed AI agents (Ollama, vLLM, LM Studio, LocalAI) alongside cloud providers (Claude, OpenAI) with automatic fallback and intelligent routing.

### Current State

- Only Claude and OpenAI adapters exist
- No local LLM provider support
- No provider fallback mechanism
- No model capability registry

### Target State

- 4+ local LLM providers supported (Ollama, vLLM, LM Studio, LocalAI)
- Automatic provider fallback on failure
- Model registry with capability metadata
- Cost and latency tracking per provider
- Full offline mode support

---

## 2. Requirements

### REQ-15-01: Ollama Adapter

**Description**: Integrate Ollama for simple local LLM deployment.

**Acceptance Criteria**:
- [ ] `ollama_adapter.py` implements LLMPort protocol
- [ ] Connects to Ollama REST API (localhost:11434)
- [ ] Supports model listing, loading, and generation
- [ ] Handles streaming responses
- [ ] Auto-detects Ollama availability

**Tool**: [Ollama](https://github.com/ollama/ollama)

---

### REQ-15-02: vLLM Adapter

**Description**: Integrate vLLM for high-throughput production deployment.

**Acceptance Criteria**:
- [ ] `vllm_adapter.py` implements LLMPort protocol
- [ ] Uses OpenAI-compatible API endpoint
- [ ] Supports batch processing for higher throughput
- [ ] Configurable base URL for distributed deployment
- [ ] Health check endpoint monitoring

**Tool**: [vLLM](https://docs.vllm.ai/)

---

### REQ-15-03: OpenAI-Compatible Generic Adapter

**Description**: Generic adapter for any OpenAI-compatible API.

**Acceptance Criteria**:
- [ ] `openai_compat_adapter.py` works with any OpenAI-API server
- [ ] Configurable base URL and API key
- [ ] Supports: LM Studio, LocalAI, Groq, Together AI, etc.
- [ ] Model auto-discovery via /models endpoint
- [ ] Streaming support

---

### REQ-15-04: Provider Fallback Chain

**Description**: Automatic failover between providers.

**Acceptance Criteria**:
- [ ] `provider_selector.py` implements fallback logic
- [ ] Priority-based provider selection
- [ ] Automatic retry on provider failure
- [ ] Configurable retry count and timeout
- [ ] Strategies: priority, round_robin, cost_based

---

### REQ-15-05: Model Registry

**Description**: Registry of available models per provider with capabilities.

**Acceptance Criteria**:
- [ ] `model_registry.yaml` defines model capabilities
- [ ] Model size, context length, strengths
- [ ] Capability tags: code, chat, reasoning, vision
- [ ] Auto-sync with available models
- [ ] CLI command: `rice-factor models`

---

### REQ-15-06: Cost & Latency Tracking

**Description**: Track usage metrics per provider.

**Acceptance Criteria**:
- [ ] Token usage tracking per request
- [ ] Cost estimation for cloud providers
- [ ] Latency metrics (time to first token, total time)
- [ ] Exportable metrics (JSON, Prometheus)
- [ ] CLI command: `rice-factor usage`

---

## 3. Configuration Schema

```yaml
# rice_factor/config/llm_providers.yaml
providers:
  cloud:
    claude:
      enabled: true
      api_key_env: ANTHROPIC_API_KEY
      models: [claude-sonnet-4-20250514, claude-opus-4-20250514]
      priority: 1
      cost_per_1k_input: 0.003
      cost_per_1k_output: 0.015
    openai:
      enabled: true
      api_key_env: OPENAI_API_KEY
      models: [gpt-4o, gpt-4-turbo]
      priority: 2
      cost_per_1k_input: 0.005
      cost_per_1k_output: 0.015

  local:
    ollama:
      enabled: true
      base_url: http://localhost:11434
      models: [codestral, qwen3-coder, deepseek-coder-v3]
      priority: 3
      cost_per_1k_input: 0  # Local = free
      cost_per_1k_output: 0
    vllm:
      enabled: false
      base_url: http://localhost:8000
      models: [codestral-22b]
      priority: 4
    lmstudio:
      enabled: false
      base_url: http://localhost:1234
      models: []  # Auto-discover
      priority: 5

fallback:
  strategy: priority  # priority | round_robin | cost_based
  max_retries: 3
  timeout_seconds: 30
  retry_delay_seconds: 1
```

---

## 4. Non-Functional Requirements

### NFR-15-01: Latency
- Local provider detection < 100ms
- Fallback switching < 500ms
- First token latency tracking

### NFR-15-02: Reliability
- Graceful handling of provider unavailability
- No data loss on provider switch
- Request completion guarantee (within retry limits)

### NFR-15-03: Offline Mode
- Full functionality with local providers only
- Clear error when all providers unavailable
- Configuration validation at startup

---

## 5. Exit Criteria

- [ ] Ollama models work for artifact generation
- [ ] vLLM production deployment supported
- [ ] Automatic fallback when provider unavailable
- [ ] Cost tracking per provider
- [ ] Model capability registry guides model selection
- [ ] Offline mode with local models only
- [ ] All tests passing
- [ ] Documentation updated

---

## 6. Estimated Test Count

~45 tests (unit + integration per adapter)
