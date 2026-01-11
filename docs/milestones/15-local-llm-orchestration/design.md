# Milestone 15: Local LLM Orchestration - Design

> **Status**: Planned
> **Priority**: P0

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Orchestration Layer                     │
├─────────────────────────────────────────────────────────────────┤
│  LLMPort (Protocol)                                              │
│    ├── CloudProviders                                            │
│    │   ├── ClaudeAdapter (existing)                              │
│    │   └── OpenAIAdapter (existing)                              │
│    └── LocalProviders (NEW)                                      │
│        ├── OllamaAdapter      # REST API localhost:11434         │
│        ├── VLLMAdapter        # OpenAI-compat API                │
│        ├── LMStudioAdapter    # OpenAI-compat API                │
│        └── LocalAIAdapter     # OpenAI-compat API                │
├─────────────────────────────────────────────────────────────────┤
│  ProviderSelector                                                │
│    ├── Fallback Chain: Claude → OpenAI → Ollama → vLLM          │
│    ├── Cost-based routing                                        │
│    └── Capability-based routing (code vs chat)                   │
├─────────────────────────────────────────────────────────────────┤
│  UsageTracker                                                    │
│    ├── Token counting                                            │
│    ├── Cost calculation                                          │
│    └── Latency metrics                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Package Structure

```
rice_factor/adapters/llm/
├── __init__.py
├── base.py                      # LLMPort protocol (existing)
├── claude_adapter.py            # EXISTING
├── openai_adapter.py            # EXISTING
├── stub_adapter.py              # EXISTING
├── ollama_adapter.py            # NEW: Ollama integration
├── vllm_adapter.py              # NEW: vLLM integration
├── openai_compat_adapter.py     # NEW: Generic OpenAI-compat
├── local_ai_adapter.py          # NEW: LocalAI integration
├── provider_selector.py         # NEW: Fallback/routing logic
└── usage_tracker.py             # NEW: Cost/latency tracking

rice_factor/config/
├── llm_providers.yaml           # NEW: Provider configuration
└── model_registry.yaml          # NEW: Model capabilities

rice_factor/domain/ports/
└── llm.py                       # UPDATE: Add provider metadata
```

---

## 3. Ollama Adapter

```python
# rice_factor/adapters/llm/ollama_adapter.py
import httpx
from typing import AsyncIterator

class OllamaAdapter:
    """Adapter for Ollama local LLM server."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def generate(
        self,
        prompt: str,
        model: str = "codestral",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate completion from Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": stream,
        }

        if stream:
            return self._stream_response(payload)
        else:
            response = await self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            return response.json()["response"]

    async def _stream_response(self, payload: dict) -> AsyncIterator[str]:
        async with self.client.stream("POST", "/api/generate", json=payload) as resp:
            async for line in resp.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]

    async def list_models(self) -> list[str]:
        """List available models."""
        response = await self.client.get("/api/tags")
        response.raise_for_status()
        return [m["name"] for m in response.json().get("models", [])]

    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = await self.client.get("/")
            return response.status_code == 200
        except Exception:
            return False
```

---

## 4. vLLM Adapter

```python
# rice_factor/adapters/llm/vllm_adapter.py
import openai

class VLLMAdapter:
    """Adapter for vLLM server (OpenAI-compatible API)."""

    def __init__(self, base_url: str = "http://localhost:8000/v1"):
        self.client = openai.AsyncOpenAI(
            base_url=base_url,
            api_key="EMPTY",  # vLLM doesn't require API key by default
        )

    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate completion from vLLM."""
        if stream:
            return self._stream_response(prompt, model, temperature, max_tokens)

        response = await self.client.completions.create(
            model=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].text

    async def _stream_response(self, prompt, model, temp, max_tokens):
        stream = await self.client.completions.create(
            model=model,
            prompt=prompt,
            temperature=temp,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].text:
                yield chunk.choices[0].text

    async def list_models(self) -> list[str]:
        """List available models."""
        models = await self.client.models.list()
        return [m.id for m in models.data]

    async def is_available(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
```

---

## 5. Provider Selector

```python
# rice_factor/adapters/llm/provider_selector.py
from enum import Enum
from dataclasses import dataclass

class SelectionStrategy(Enum):
    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"
    COST_BASED = "cost_based"

@dataclass
class ProviderConfig:
    name: str
    adapter: LLMPort
    priority: int
    enabled: bool
    cost_per_1k_input: float
    cost_per_1k_output: float

class ProviderSelector:
    """Selects LLM provider with fallback support."""

    def __init__(
        self,
        providers: list[ProviderConfig],
        strategy: SelectionStrategy = SelectionStrategy.PRIORITY,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
    ):
        self.providers = sorted(
            [p for p in providers if p.enabled],
            key=lambda p: p.priority
        )
        self.strategy = strategy
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self._current_index = 0

    async def generate(self, prompt: str, **kwargs) -> tuple[str, str]:
        """Generate with automatic fallback. Returns (response, provider_name)."""
        errors = []

        for attempt in range(self.max_retries):
            provider = self._select_provider()

            try:
                response = await asyncio.wait_for(
                    provider.adapter.generate(prompt, **kwargs),
                    timeout=self.timeout_seconds,
                )
                return response, provider.name
            except Exception as e:
                errors.append(f"{provider.name}: {e}")
                self._advance_provider()

        raise AllProvidersFailedError(errors)

    def _select_provider(self) -> ProviderConfig:
        if self.strategy == SelectionStrategy.PRIORITY:
            return self.providers[0]
        elif self.strategy == SelectionStrategy.ROUND_ROBIN:
            return self.providers[self._current_index % len(self.providers)]
        elif self.strategy == SelectionStrategy.COST_BASED:
            return min(self.providers, key=lambda p: p.cost_per_1k_input)

    def _advance_provider(self):
        self._current_index += 1
```

---

## 6. Usage Tracker

```python
# rice_factor/adapters/llm/usage_tracker.py
from dataclasses import dataclass, field
from datetime import datetime
import tiktoken

@dataclass
class UsageRecord:
    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float

@dataclass
class UsageTracker:
    """Tracks LLM usage across providers."""

    records: list[UsageRecord] = field(default_factory=list)
    _encoder: tiktoken.Encoding = field(init=False)

    def __post_init__(self):
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def record(
        self,
        provider: str,
        model: str,
        prompt: str,
        response: str,
        latency_ms: float,
        cost_per_1k_input: float,
        cost_per_1k_output: float,
    ):
        input_tokens = len(self._encoder.encode(prompt))
        output_tokens = len(self._encoder.encode(response))

        cost = (
            (input_tokens / 1000) * cost_per_1k_input +
            (output_tokens / 1000) * cost_per_1k_output
        )

        self.records.append(UsageRecord(
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost,
        ))

    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.records)

    def by_provider(self) -> dict[str, float]:
        result = {}
        for r in self.records:
            result[r.provider] = result.get(r.provider, 0) + r.cost_usd
        return result

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        for provider, cost in self.by_provider().items():
            lines.append(f'llm_cost_usd{{provider="{provider}"}} {cost}')
        return "\n".join(lines)
```

---

## 7. Model Registry

```yaml
# rice_factor/config/model_registry.yaml
models:
  # Cloud Models
  claude-sonnet-4-20250514:
    provider: claude
    context_length: 200000
    capabilities: [code, chat, reasoning, vision]
    strengths: Best for complex code generation

  gpt-4o:
    provider: openai
    context_length: 128000
    capabilities: [code, chat, reasoning, vision]
    strengths: Fast, multimodal

  # Local Models
  codestral:
    provider: ollama
    context_length: 32000
    capabilities: [code]
    strengths: Fast code completion, Mistral quality
    size_gb: 12

  qwen3-coder:
    provider: ollama
    context_length: 32000
    capabilities: [code, reasoning]
    strengths: Multi-language, reasoning chains
    size_gb: 4-45  # Depends on quant

  deepseek-coder-v3:
    provider: ollama
    context_length: 128000
    capabilities: [code]
    strengths: Best code completion accuracy
    size_gb: 4-20
```

---

## 8. CLI Commands

```bash
# List available providers and their status
rice-factor providers
# Output:
# Provider     | Status | Priority | Models
# -------------|--------|----------|------------------
# claude       | ✓      | 1        | claude-sonnet-4, claude-opus-4
# openai       | ✓      | 2        | gpt-4o, gpt-4-turbo
# ollama       | ✓      | 3        | codestral, qwen3-coder
# vllm         | ✗      | 4        | (not running)

# List available models
rice-factor models
# Output:
# Model              | Provider | Context | Capabilities
# -------------------|----------|---------|------------------
# claude-sonnet-4    | claude   | 200K    | code, chat, reasoning
# codestral          | ollama   | 32K     | code

# Show usage statistics
rice-factor usage
# Output:
# Provider  | Requests | Tokens  | Cost
# ----------|----------|---------|-------
# claude    | 45       | 125,000 | $1.87
# ollama    | 120      | 450,000 | $0.00
# Total     | 165      | 575,000 | $1.87
```

---

## 9. Testing Strategy

1. **Unit Tests**: Mock HTTP responses, test adapter logic
2. **Integration Tests**: Real Ollama/vLLM servers (optional, skipped in CI)
3. **Fallback Tests**: Simulate provider failures
4. **Usage Tests**: Verify cost and token calculations
