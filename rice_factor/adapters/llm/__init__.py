"""LLM provider adapters (Claude, OpenAI, local models) and CLI agents."""

from rice_factor.adapters.llm.claude import ClaudeAdapter, create_claude_adapter_from_config
from rice_factor.adapters.llm.claude_client import ClaudeClient, ClaudeClientError
from rice_factor.adapters.llm.cli import (
    AgentConfig,
    AiderAdapter,
    ClaudeCodeAdapter,
    CLIAgent,
    CLIAgentDetector,
    CLIAgentPort,
    CLITaskResult,
    CodexAdapter,
    DetectedAgent,
    GeminiCLIAdapter,
    QwenCodeAdapter,
    create_aider_adapter_from_config,
    create_claude_code_adapter_from_config,
    create_codex_adapter_from_config,
    create_gemini_cli_adapter_from_config,
    create_qwen_code_adapter_from_config,
)
from rice_factor.adapters.llm.ollama_adapter import (
    OllamaAdapter,
    OllamaClient,
    OllamaClientError,
    create_ollama_adapter_from_config,
)
from rice_factor.adapters.llm.openai_adapter import (
    OpenAIAdapter,
    create_openai_adapter_from_config,
)
from rice_factor.adapters.llm.openai_client import OpenAIClient, OpenAIClientError
from rice_factor.adapters.llm.openai_compat_adapter import (
    OpenAICompatAdapter,
    OpenAICompatClient,
    OpenAICompatClientError,
    create_openai_compat_adapter_from_config,
)
from rice_factor.adapters.llm.orchestrator import (
    NoAgentAvailableError,
    OrchestrationMode,
    OrchestrationResult,
    UnifiedOrchestrator,
    create_orchestrator_from_config,
)
from rice_factor.adapters.llm.provider_selector import (
    AllProvidersFailedError,
    ProviderConfig,
    ProviderSelector,
    SelectionResult,
    SelectionStrategy,
    create_provider_selector_from_config,
)
from rice_factor.adapters.llm.stub import StubLLMAdapter
from rice_factor.adapters.llm.usage_tracker import (
    ProviderStats,
    UsageRecord,
    UsageTracker,
    get_usage_tracker,
    reset_usage_tracker,
)
from rice_factor.adapters.llm.vllm_adapter import (
    VLLMAdapter,
    VLLMClient,
    VLLMClientError,
    create_vllm_adapter_from_config,
)

# Type alias for any LLM adapter
LLMAdapter = (
    ClaudeAdapter
    | OpenAIAdapter
    | OllamaAdapter
    | VLLMAdapter
    | OpenAICompatAdapter
    | StubLLMAdapter
)


def create_llm_adapter_from_config() -> LLMAdapter:
    """Create an LLM adapter based on application configuration.

    Reads the llm.provider setting and instantiates the appropriate adapter:
    - "claude": ClaudeAdapter
    - "openai": OpenAIAdapter
    - "ollama": OllamaAdapter (local LLM via Ollama)
    - "vllm": VLLMAdapter (vLLM server with OpenAI-compatible API)
    - "openai_compat": OpenAICompatAdapter (generic OpenAI-compatible server)
    - "stub": StubLLMAdapter (for testing)

    Returns:
        Configured LLM adapter instance.

    Raises:
        ValueError: If the provider is not recognized.
    """
    from rice_factor.config.settings import settings

    provider = settings.get("llm.provider", "claude").lower()

    if provider == "claude":
        return create_claude_adapter_from_config()
    elif provider == "openai":
        return create_openai_adapter_from_config()
    elif provider == "ollama":
        return create_ollama_adapter_from_config()
    elif provider == "vllm":
        return create_vllm_adapter_from_config()
    elif provider in ("openai_compat", "localai", "lmstudio", "tgi"):
        return create_openai_compat_adapter_from_config()
    elif provider == "stub":
        return StubLLMAdapter()
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            "Valid options: claude, openai, ollama, vllm, openai_compat, localai, lmstudio, tgi, stub"
        )


__all__ = [
    "AgentConfig",
    "AiderAdapter",
    "AllProvidersFailedError",
    "CLIAgent",
    "CLIAgentDetector",
    "CLIAgentPort",
    "CLITaskResult",
    "ClaudeAdapter",
    "ClaudeClient",
    "ClaudeClientError",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "DetectedAgent",
    "GeminiCLIAdapter",
    "LLMAdapter",
    "NoAgentAvailableError",
    "OllamaAdapter",
    "OllamaClient",
    "OllamaClientError",
    "OpenAIAdapter",
    "OpenAIClient",
    "OpenAIClientError",
    "OpenAICompatAdapter",
    "OpenAICompatClient",
    "OpenAICompatClientError",
    "OrchestrationMode",
    "OrchestrationResult",
    "ProviderConfig",
    "ProviderSelector",
    "ProviderStats",
    "QwenCodeAdapter",
    "SelectionResult",
    "SelectionStrategy",
    "StubLLMAdapter",
    "UnifiedOrchestrator",
    "UsageRecord",
    "UsageTracker",
    "VLLMAdapter",
    "VLLMClient",
    "VLLMClientError",
    "create_aider_adapter_from_config",
    "create_claude_adapter_from_config",
    "create_claude_code_adapter_from_config",
    "create_codex_adapter_from_config",
    "create_gemini_cli_adapter_from_config",
    "create_llm_adapter_from_config",
    "create_ollama_adapter_from_config",
    "create_openai_adapter_from_config",
    "create_openai_compat_adapter_from_config",
    "create_orchestrator_from_config",
    "create_provider_selector_from_config",
    "create_qwen_code_adapter_from_config",
    "create_vllm_adapter_from_config",
    "get_usage_tracker",
    "reset_usage_tracker",
]
