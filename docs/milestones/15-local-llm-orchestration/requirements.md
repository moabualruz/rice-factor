# Milestone 15: LLM Orchestration - Requirements

> **Status**: Complete
> **Priority**: P0 (Cost reduction, privacy, offline mode, CLI integration)
> **Dependencies**: None

---

## 1. Overview

Support multiple orchestration modes for AI-assisted code generation:

1. **API Providers** - Cloud and local REST API services (Claude, OpenAI, Ollama, vLLM)
2. **CLI Agents** - Agentic coding tools that run as terminal applications (Claude Code, Codex CLI, Gemini CLI, Qwen Code, Aider, OpenCode)

This dual-mode architecture enables:
- **Cost optimization** via local models and CLI tools with free tiers
- **Privacy** via fully local execution
- **Flexibility** via pluggable adapters for any provider type
- **Redundancy** via fallback chains across both modes

### Current State

- Only Claude and OpenAI API adapters exist
- No local LLM provider support
- No CLI agent orchestration
- No provider fallback mechanism
- No model capability registry

### Target State

- 4+ API providers supported (Ollama, vLLM, LM Studio, LocalAI)
- 6+ CLI agent adapters (Claude Code, Codex, Gemini CLI, Qwen Code, Aider, OpenCode)
- Automatic provider/agent fallback on failure
- Model registry with capability metadata
- Cost and latency tracking per provider
- Full offline mode support
- CLI agent task delegation

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

### REQ-15-07: Claude Code CLI Adapter

**Description**: Integrate Claude Code CLI for agentic coding tasks.

**Acceptance Criteria**:
- [ ] `claude_code_adapter.py` implements CLIAgentPort protocol
- [ ] Spawns `claude` process with task prompt
- [ ] Captures stdout/stderr for response parsing
- [ ] Supports `--print` mode for non-interactive output
- [ ] Auto-detects Claude Code availability (`which claude`)
- [ ] Configurable timeout and working directory

**Tool**: [Claude Code CLI](https://github.com/anthropics/claude-code)

---

### REQ-15-08: OpenAI Codex CLI Adapter

**Description**: Integrate OpenAI Codex CLI for agentic coding tasks.

**Acceptance Criteria**:
- [ ] `codex_adapter.py` implements CLIAgentPort protocol
- [ ] Spawns `codex exec` for non-interactive execution
- [ ] Parses JSON output with `--output-format json`
- [ ] Supports model selection (`--model`)
- [ ] Auto-detects Codex availability
- [ ] Configurable approval mode (suggest, auto-edit, full-auto)

**Tool**: [OpenAI Codex CLI](https://github.com/openai/codex)

---

### REQ-15-09: Gemini CLI Adapter

**Description**: Integrate Google Gemini CLI for agentic coding tasks.

**Acceptance Criteria**:
- [ ] `gemini_cli_adapter.py` implements CLIAgentPort protocol
- [ ] Spawns `gemini` process with task prompt
- [ ] Supports sandbox mode configuration
- [ ] Leverages ReAct loop capabilities
- [ ] Auto-detects Gemini CLI availability
- [ ] Configurable tool permissions

**Tool**: [Gemini CLI](https://github.com/google-gemini/gemini-cli)

---

### REQ-15-10: Qwen Code CLI Adapter

**Description**: Integrate Qwen Code CLI for agentic coding tasks.

**Acceptance Criteria**:
- [ ] `qwen_code_adapter.py` implements CLIAgentPort protocol
- [ ] Spawns `qwen-code` process with task prompt
- [ ] Supports OAuth authentication or API key
- [ ] Leverages plan mode capabilities
- [ ] Auto-detects Qwen Code availability
- [ ] Supports local model routing via Ollama

**Tool**: [Qwen Code CLI](https://github.com/QwenLM/qwen-code)

---

### REQ-15-11: Aider CLI Adapter

**Description**: Integrate Aider for AI pair programming tasks.

**Acceptance Criteria**:
- [ ] `aider_adapter.py` implements CLIAgentPort protocol
- [ ] Spawns `aider` with `--message` for non-interactive mode
- [ ] Supports `--yes` for auto-accepting changes
- [ ] Configurable model selection (`--model`)
- [ ] Auto-detects Aider availability
- [ ] Supports local models via `--model ollama/codestral`

**Tool**: [Aider](https://github.com/Aider-AI/aider)

---

### REQ-15-12: CLI Agent Protocol

**Description**: Define protocol for CLI agent adapters.

**Acceptance Criteria**:
- [ ] `CLIAgentPort` protocol with `execute_task()` method
- [ ] Task input as structured prompt or file path
- [ ] Response includes: success, output, files_modified, duration
- [ ] Standardized error handling across adapters
- [ ] Timeout and cancellation support
- [ ] Working directory configuration

---

### REQ-15-13: OpenCode CLI Adapter

**Description**: Integrate OpenCode CLI for agentic coding tasks.

**Acceptance Criteria**:
- [ ] `opencode_adapter.py` implements CLIAgentPort protocol
- [ ] Spawns `opencode run` for non-interactive execution
- [ ] Parses JSON output with `--format json`
- [ ] Supports model selection (`--model provider/model`)
- [ ] Auto-detects OpenCode availability (`which opencode`)
- [ ] Supports server attach mode (`--attach`) for faster execution
- [ ] Session resume capability (`--session`, `--continue`)

**Tool**: [OpenCode CLI](https://opencode.ai/)

---

## 3. Configuration Schema

```yaml
# rice_factor/config/llm_providers.yaml
providers:
  # API-based providers (REST/HTTP)
  api:
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

  # CLI-based agents (subprocess execution)
  cli:
    claude_code:
      enabled: true
      command: claude
      args: ["--print", "--output-format", "json"]
      priority: 10
      timeout_seconds: 300
      capabilities: [code_generation, refactoring, testing]
      free_tier: false  # Requires Claude Pro/Max
    codex:
      enabled: true
      command: codex
      args: ["exec", "--output-format", "json"]
      priority: 11
      timeout_seconds: 300
      approval_mode: suggest  # suggest | auto-edit | full-auto
      capabilities: [code_generation, refactoring]
      free_tier: true  # Free tier available
    gemini_cli:
      enabled: true
      command: gemini
      args: []
      priority: 12
      timeout_seconds: 300
      sandbox_mode: true
      capabilities: [code_generation, file_manipulation, command_execution]
      free_tier: true  # 1000 requests/day free
    qwen_code:
      enabled: true
      command: qwen-code
      args: []
      priority: 13
      timeout_seconds: 300
      capabilities: [code_generation, refactoring, planning]
      free_tier: true  # 2000 requests/day with OAuth
    aider:
      enabled: true
      command: aider
      args: ["--yes", "--no-auto-commits"]
      priority: 14
      timeout_seconds: 600
      model: claude-3-5-sonnet  # or ollama/codestral for local
      capabilities: [code_generation, refactoring, git_integration]
      free_tier: true  # Open source, pay per LLM usage
    opencode:
      enabled: true
      command: opencode
      args: ["run", "--format", "json"]
      priority: 15
      timeout_seconds: 300
      model: anthropic/claude-4-sonnet  # provider/model format
      attach_url: null  # Optional: http://localhost:4096 for server mode
      capabilities: [code_generation, refactoring, file_manipulation, command_execution]
      free_tier: true  # Open source, pay per LLM usage

fallback:
  strategy: priority  # priority | round_robin | cost_based | api_first | cli_first
  max_retries: 3
  timeout_seconds: 30
  retry_delay_seconds: 1
  prefer_mode: api  # api | cli | auto (auto selects based on task)
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

### API Providers
- [ ] Ollama models work for artifact generation
- [ ] vLLM production deployment supported
- [ ] OpenAI-compatible adapter works with LM Studio, LocalAI
- [ ] Automatic fallback when provider unavailable
- [ ] Cost tracking per provider

### CLI Agents
- [ ] Claude Code CLI executes tasks and returns structured output
- [ ] Codex CLI executes tasks in non-interactive mode
- [ ] Gemini CLI executes tasks with sandbox support
- [ ] Qwen Code CLI executes tasks with OAuth or API key
- [ ] Aider executes tasks in non-interactive mode
- [ ] OpenCode CLI executes tasks with JSON output and server attach mode
- [ ] CLI agent auto-detection works correctly

### General
- [ ] Model/agent capability registry guides selection
- [ ] Offline mode with local models and CLI agents
- [ ] Fallback works across both API and CLI modes
- [ ] All tests passing
- [ ] Documentation updated

---

## 6. Estimated Test Count

~85 tests (unit + integration per adapter)
- API adapters: ~30 tests
- CLI adapters: ~45 tests (includes OpenCode)
- Provider selector & fallback: ~10 tests
