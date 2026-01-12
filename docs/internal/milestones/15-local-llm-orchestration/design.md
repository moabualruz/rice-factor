# Milestone 15: LLM Orchestration - Design

> **Status**: Complete
> **Priority**: P0

---

## 1. Architecture

The orchestration layer supports two modes of AI integration:

1. **API Mode** - Direct HTTP/REST calls to LLM providers
2. **CLI Mode** - Subprocess execution of agentic coding tools

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        LLM Orchestration Layer                           │
├─────────────────────────────────────────────────────────────────────────┤
│  UnifiedOrchestrator                                                     │
│    ├── Mode Selection: API vs CLI (based on task type)                  │
│    ├── Fallback Chain: API providers → CLI agents                       │
│    └── Task Router: code_gen → API, complex_refactor → CLI              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────┐  ┌────────────────────────────────────┐ │
│  │     LLMPort (API Mode)     │  │     CLIAgentPort (CLI Mode)        │ │
│  ├────────────────────────────┤  ├────────────────────────────────────┤ │
│  │  CloudProviders            │  │  Agentic CLI Tools                 │ │
│  │    ├── ClaudeAdapter       │  │    ├── ClaudeCodeAdapter           │ │
│  │    └── OpenAIAdapter       │  │    ├── CodexAdapter                │ │
│  │  LocalProviders            │  │    ├── GeminiCLIAdapter            │ │
│  │    ├── OllamaAdapter       │  │    ├── QwenCodeAdapter             │ │
│  │    ├── VLLMAdapter         │  │    └── AiderAdapter                │ │
│  │    ├── LMStudioAdapter     │  │                                    │ │
│  │    └── LocalAIAdapter      │  │                                    │ │
│  └────────────────────────────┘  └────────────────────────────────────┘ │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ProviderSelector                                                        │
│    ├── Priority-based selection (API priority 1-9, CLI priority 10-19)  │
│    ├── Cost-based routing (free CLI tiers first)                        │
│    ├── Capability-based routing (task → best provider/agent)            │
│    └── Fallback Chain: Claude API → OpenAI → Ollama → Claude Code CLI   │
├─────────────────────────────────────────────────────────────────────────┤
│  UsageTracker                                                            │
│    ├── Token counting (API mode)                                         │
│    ├── Task duration (CLI mode)                                          │
│    ├── Cost calculation (API) / Free tier tracking (CLI)                │
│    └── Latency metrics                                                   │
└─────────────────────────────────────────────────────────────────────────┘
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
│
│  # API Adapters (NEW)
├── ollama_adapter.py            # NEW: Ollama integration
├── vllm_adapter.py              # NEW: vLLM integration
├── openai_compat_adapter.py     # NEW: Generic OpenAI-compat
├── local_ai_adapter.py          # NEW: LocalAI integration
│
│  # CLI Agent Adapters (NEW)
├── cli/
│   ├── __init__.py
│   ├── base.py                  # NEW: CLIAgentPort protocol
│   ├── claude_code_adapter.py   # NEW: Claude Code CLI
│   ├── codex_adapter.py         # NEW: OpenAI Codex CLI
│   ├── gemini_cli_adapter.py    # NEW: Google Gemini CLI
│   ├── qwen_code_adapter.py     # NEW: Qwen Code CLI
│   ├── aider_adapter.py         # NEW: Aider CLI
│   ├── opencode_adapter.py      # NEW: OpenCode CLI
│   └── detector.py              # NEW: CLI tool auto-detection
│
│  # Orchestration (NEW)
├── orchestrator.py              # NEW: Unified orchestrator
├── provider_selector.py         # NEW: Fallback/routing logic
└── usage_tracker.py             # NEW: Cost/latency tracking

rice_factor/config/
├── llm_providers.yaml           # NEW: Provider + CLI agent config
└── model_registry.yaml          # NEW: Model capabilities

rice_factor/domain/ports/
├── llm.py                       # UPDATE: Add provider metadata
└── cli_agent.py                 # NEW: CLIAgentPort protocol
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

## 9. CLI Agent Protocol

```python
# rice_factor/domain/ports/cli_agent.py
from typing import Protocol
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CLITaskResult:
    """Result from CLI agent execution."""
    success: bool
    output: str
    error: str | None
    files_modified: list[str]
    duration_seconds: float
    agent_name: str

class CLIAgentPort(Protocol):
    """Protocol for CLI-based coding agents."""

    @property
    def name(self) -> str:
        """Agent identifier (e.g., 'claude_code', 'codex')."""
        ...

    async def is_available(self) -> bool:
        """Check if CLI tool is installed and accessible."""
        ...

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float = 300.0,
    ) -> CLITaskResult:
        """Execute a coding task and return results."""
        ...

    def get_capabilities(self) -> list[str]:
        """Return list of capabilities (e.g., ['code_generation', 'refactoring'])."""
        ...
```

---

## 10. Claude Code CLI Adapter

```python
# rice_factor/adapters/llm/cli/claude_code_adapter.py
import asyncio
import shutil
from pathlib import Path

class ClaudeCodeAdapter:
    """Adapter for Claude Code CLI (anthropics/claude-code)."""

    def __init__(
        self,
        command: str = "claude",
        args: list[str] | None = None,
        timeout_seconds: float = 300.0,
    ):
        self.command = command
        self.args = args or ["--print", "--output-format", "json"]
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "claude_code"

    async def is_available(self) -> bool:
        """Check if Claude Code CLI is installed."""
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float | None = None,
    ) -> CLITaskResult:
        """Execute task via Claude Code CLI."""
        timeout = timeout_seconds or self.timeout_seconds
        start_time = asyncio.get_event_loop().time()

        try:
            # Build command: claude --print -p "prompt"
            cmd = [self.command] + self.args + ["-p", prompt]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=working_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )

            duration = asyncio.get_event_loop().time() - start_time

            return CLITaskResult(
                success=process.returncode == 0,
                output=stdout.decode("utf-8"),
                error=stderr.decode("utf-8") if stderr else None,
                files_modified=self._parse_modified_files(stdout.decode()),
                duration_seconds=duration,
                agent_name=self.name,
            )

        except asyncio.TimeoutError:
            return CLITaskResult(
                success=False,
                output="",
                error=f"Timeout after {timeout}s",
                files_modified=[],
                duration_seconds=timeout,
                agent_name=self.name,
            )

    def _parse_modified_files(self, output: str) -> list[str]:
        """Parse modified files from JSON output."""
        try:
            import json
            data = json.loads(output)
            return data.get("files_modified", [])
        except json.JSONDecodeError:
            return []

    def get_capabilities(self) -> list[str]:
        return ["code_generation", "refactoring", "testing", "git_integration"]
```

---

## 11. Codex CLI Adapter

```python
# rice_factor/adapters/llm/cli/codex_adapter.py

class CodexAdapter:
    """Adapter for OpenAI Codex CLI (openai/codex)."""

    def __init__(
        self,
        command: str = "codex",
        approval_mode: str = "suggest",  # suggest | auto-edit | full-auto
        timeout_seconds: float = 300.0,
    ):
        self.command = command
        self.approval_mode = approval_mode
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "codex"

    async def is_available(self) -> bool:
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float | None = None,
    ) -> CLITaskResult:
        """Execute task via Codex CLI in non-interactive mode."""
        timeout = timeout_seconds or self.timeout_seconds
        start_time = asyncio.get_event_loop().time()

        # Build command: codex exec --approval-mode suggest "prompt"
        cmd = [
            self.command, "exec",
            "--approval-mode", self.approval_mode,
            "--output-format", "json",
            prompt,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )

        duration = asyncio.get_event_loop().time() - start_time

        return CLITaskResult(
            success=process.returncode == 0,
            output=stdout.decode("utf-8"),
            error=stderr.decode("utf-8") if stderr else None,
            files_modified=self._parse_modified_files(stdout.decode()),
            duration_seconds=duration,
            agent_name=self.name,
        )

    def get_capabilities(self) -> list[str]:
        return ["code_generation", "refactoring", "code_review"]
```

---

## 12. Aider CLI Adapter

```python
# rice_factor/adapters/llm/cli/aider_adapter.py

class AiderAdapter:
    """Adapter for Aider CLI (Aider-AI/aider)."""

    def __init__(
        self,
        command: str = "aider",
        model: str = "claude-3-5-sonnet",  # or "ollama/codestral"
        auto_commits: bool = False,
        timeout_seconds: float = 600.0,
    ):
        self.command = command
        self.model = model
        self.auto_commits = auto_commits
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "aider"

    async def is_available(self) -> bool:
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float | None = None,
    ) -> CLITaskResult:
        """Execute task via Aider in non-interactive mode."""
        timeout = timeout_seconds or self.timeout_seconds
        start_time = asyncio.get_event_loop().time()

        # Build command: aider --yes --message "prompt" --model model
        cmd = [
            self.command,
            "--yes",  # Auto-accept changes
            "--message", prompt,
            "--model", self.model,
        ]

        if not self.auto_commits:
            cmd.append("--no-auto-commits")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )

        duration = asyncio.get_event_loop().time() - start_time

        return CLITaskResult(
            success=process.returncode == 0,
            output=stdout.decode("utf-8"),
            error=stderr.decode("utf-8") if stderr else None,
            files_modified=self._parse_modified_files(stdout.decode()),
            duration_seconds=duration,
            agent_name=self.name,
        )

    def _parse_modified_files(self, output: str) -> list[str]:
        """Parse modified files from Aider output."""
        # Aider outputs lines like "Added file.py to the chat"
        # and "Wrote file.py"
        files = []
        for line in output.split("\n"):
            if line.startswith("Wrote "):
                files.append(line.replace("Wrote ", "").strip())
        return files

    def get_capabilities(self) -> list[str]:
        return ["code_generation", "refactoring", "git_integration", "multi_file"]
```

---

## 12.5 OpenCode CLI Adapter

```python
# rice_factor/adapters/llm/cli/opencode_adapter.py

class OpenCodeAdapter:
    """Adapter for OpenCode CLI (opencode.ai).

    OpenCode is an open-source AI coding agent with 50k+ GitHub stars.
    Supports multiple AI providers (Claude, OpenAI, Gemini, Groq, etc.).
    """

    def __init__(
        self,
        command: str = "opencode",
        model: str | None = None,  # e.g., "anthropic/claude-4-sonnet"
        attach_url: str | None = None,  # e.g., "http://localhost:4096"
        timeout_seconds: float = 300.0,
    ):
        self.command = command
        self.model = model
        self.attach_url = attach_url
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "opencode"

    async def is_available(self) -> bool:
        return shutil.which(self.command) is not None

    async def execute_task(
        self,
        prompt: str,
        working_dir: Path,
        timeout_seconds: float | None = None,
    ) -> CLITaskResult:
        """Execute task via OpenCode CLI in non-interactive mode."""
        timeout = timeout_seconds or self.timeout_seconds
        start_time = asyncio.get_event_loop().time()

        # Build command: opencode run --format json "prompt"
        cmd = [self.command, "run", "--format", "json"]

        # Add model if specified
        if self.model:
            cmd.extend(["--model", self.model])

        # Add server attach for faster execution (avoids cold boot)
        if self.attach_url:
            cmd.extend(["--attach", self.attach_url])

        # Add the prompt
        cmd.append(prompt)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )

        duration = asyncio.get_event_loop().time() - start_time

        return CLITaskResult(
            success=process.returncode == 0,
            output=stdout.decode("utf-8"),
            error=stderr.decode("utf-8") if stderr else None,
            files_modified=self._parse_modified_files(stdout.decode()),
            duration_seconds=duration,
            agent_name=self.name,
        )

    def _parse_modified_files(self, output: str) -> list[str]:
        """Parse modified files from JSON output."""
        try:
            import json
            data = json.loads(output)
            return data.get("files_modified", [])
        except json.JSONDecodeError:
            return []

    def get_capabilities(self) -> list[str]:
        return ["code_generation", "refactoring", "file_manipulation", "command_execution"]
```

### OpenCode CLI Key Features

1. **Non-Interactive Mode**: `opencode run "prompt"` for scripted execution
2. **JSON Output**: `--format json` for structured response parsing
3. **Multi-Provider Support**: Anthropic, OpenAI, Google, Groq, AWS Bedrock, etc.
4. **Server Attach Mode**: `--attach http://localhost:4096` avoids cold boot overhead
5. **Session Management**: `--session <id>` or `--continue` to resume conversations
6. **Built-in Agents**: `build` (full access) and `plan` (read-only analysis)

### Server Mode Optimization

For repeated task execution, use server mode to avoid startup latency:

```bash
# Terminal 1: Start persistent server
opencode serve --port 4096

# Terminal 2+: Fast task execution via attach
opencode run --attach http://localhost:4096 --format json "prompt"
```

---

## 13. CLI Agent Detector

```python
# rice_factor/adapters/llm/cli/detector.py
import shutil
from dataclasses import dataclass

@dataclass
class DetectedAgent:
    name: str
    command: str
    version: str | None
    available: bool

class CLIAgentDetector:
    """Auto-detect available CLI coding agents."""

    AGENTS = {
        "claude_code": {"command": "claude", "version_flag": "--version"},
        "codex": {"command": "codex", "version_flag": "--version"},
        "gemini": {"command": "gemini", "version_flag": "--version"},
        "qwen_code": {"command": "qwen-code", "version_flag": "--version"},
        "aider": {"command": "aider", "version_flag": "--version"},
        "opencode": {"command": "opencode", "version_flag": "--version"},
    }

    def detect_all(self) -> list[DetectedAgent]:
        """Detect all available CLI agents."""
        results = []
        for name, config in self.AGENTS.items():
            available = shutil.which(config["command"]) is not None
            version = self._get_version(config) if available else None
            results.append(DetectedAgent(
                name=name,
                command=config["command"],
                version=version,
                available=available,
            ))
        return results

    def _get_version(self, config: dict) -> str | None:
        """Get version string from CLI tool."""
        import subprocess
        try:
            result = subprocess.run(
                [config["command"], config["version_flag"]],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip().split("\n")[0]
        except Exception:
            return None
```

---

## 14. Unified Orchestrator

```python
# rice_factor/adapters/llm/orchestrator.py
from enum import Enum

class OrchestrationMode(Enum):
    API = "api"          # Use LLM API providers
    CLI = "cli"          # Use CLI agents
    AUTO = "auto"        # Select based on task type

class UnifiedOrchestrator:
    """Orchestrates between API providers and CLI agents."""

    def __init__(
        self,
        api_selector: ProviderSelector,
        cli_agents: list[CLIAgentPort],
        default_mode: OrchestrationMode = OrchestrationMode.AUTO,
    ):
        self.api_selector = api_selector
        self.cli_agents = {a.name: a for a in cli_agents}
        self.default_mode = default_mode

    async def execute(
        self,
        prompt: str,
        task_type: str = "code_generation",
        mode: OrchestrationMode | None = None,
        working_dir: Path | None = None,
    ) -> str | CLITaskResult:
        """Execute task using appropriate mode."""
        mode = mode or self.default_mode

        if mode == OrchestrationMode.AUTO:
            mode = self._select_mode(task_type)

        if mode == OrchestrationMode.API:
            response, provider = await self.api_selector.generate(prompt)
            return response
        else:
            return await self._execute_cli(prompt, working_dir, task_type)

    def _select_mode(self, task_type: str) -> OrchestrationMode:
        """Select mode based on task type."""
        # Complex tasks benefit from agentic CLI tools
        cli_tasks = {"complex_refactor", "multi_file_change", "testing", "debugging"}
        if task_type in cli_tasks:
            return OrchestrationMode.CLI
        return OrchestrationMode.API

    async def _execute_cli(
        self,
        prompt: str,
        working_dir: Path | None,
        task_type: str,
    ) -> CLITaskResult:
        """Execute via CLI agent with fallback."""
        working_dir = working_dir or Path.cwd()

        # Try agents in priority order
        for agent in sorted(self.cli_agents.values(), key=lambda a: a.priority):
            if await agent.is_available():
                if task_type in agent.get_capabilities():
                    return await agent.execute_task(prompt, working_dir)

        raise NoAgentAvailableError(f"No CLI agent available for {task_type}")
```

---

## 15. Updated CLI Commands

```bash
# List available providers and agents
rice-factor providers
# Output:
# === API Providers ===
# Provider     | Status | Priority | Models
# -------------|--------|----------|------------------
# claude       | ✓      | 1        | claude-sonnet-4, claude-opus-4
# openai       | ✓      | 2        | gpt-4o, gpt-4-turbo
# ollama       | ✓      | 3        | codestral, qwen3-coder
# vllm         | ✗      | 4        | (not running)
#
# === CLI Agents ===
# Agent        | Status | Priority | Capabilities
# -------------|--------|----------|---------------------------
# claude_code  | ✓      | 10       | code_generation, refactoring
# codex        | ✓      | 11       | code_generation, refactoring
# gemini       | ✓      | 12       | code_generation, file_ops
# qwen_code    | ✗      | 13       | (not installed)
# aider        | ✓      | 14       | code_generation, git
# opencode     | ✓      | 15       | code_generation, refactoring

# Detect installed CLI agents
rice-factor agents detect
# Output:
# Detecting CLI coding agents...
# ✓ claude v1.2.3 (claude_code)
# ✓ codex v0.9.0 (codex)
# ✓ gemini v2.1.0 (gemini_cli)
# ✗ qwen-code (not found)
# ✓ aider v0.82.0 (aider)
# ✓ opencode v0.5.0 (opencode)

# Execute task with specific mode
rice-factor exec --mode cli "Add unit tests for auth module"
rice-factor exec --mode api "Generate docstring for function"
rice-factor exec --mode auto "Refactor database layer"  # Auto-selects
```

---

## 16. Testing Strategy

### API Adapters
1. **Unit Tests**: Mock HTTP responses, test adapter logic
2. **Integration Tests**: Real Ollama/vLLM servers (optional, skipped in CI)
3. **Fallback Tests**: Simulate provider failures
4. **Usage Tests**: Verify cost and token calculations

### CLI Adapters
1. **Unit Tests**: Mock subprocess execution, test output parsing
2. **Detection Tests**: Verify agent detection with mocked `shutil.which`
3. **Timeout Tests**: Ensure proper timeout handling
4. **Integration Tests**: Real CLI tools (optional, marked as slow)

### Orchestrator
1. **Mode Selection Tests**: Verify auto-mode task routing
2. **Fallback Tests**: API → CLI fallback on failure
3. **E2E Tests**: Full orchestration with mocked adapters
