"""LLM provider adapters (Claude, OpenAI, local models)."""

from rice_factor.adapters.llm.claude import ClaudeAdapter, create_claude_adapter_from_config
from rice_factor.adapters.llm.claude_client import ClaudeClient, ClaudeClientError
from rice_factor.adapters.llm.openai_adapter import (
    OpenAIAdapter,
    create_openai_adapter_from_config,
)
from rice_factor.adapters.llm.openai_client import OpenAIClient, OpenAIClientError
from rice_factor.adapters.llm.stub import StubLLMAdapter

# Type alias for any LLM adapter
LLMAdapter = ClaudeAdapter | OpenAIAdapter | StubLLMAdapter


def create_llm_adapter_from_config() -> LLMAdapter:
    """Create an LLM adapter based on application configuration.

    Reads the llm.provider setting and instantiates the appropriate adapter:
    - "claude": ClaudeAdapter
    - "openai": OpenAIAdapter
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
    elif provider == "stub":
        return StubLLMAdapter()
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            "Valid options: claude, openai, stub"
        )


__all__ = [
    "ClaudeAdapter",
    "ClaudeClient",
    "ClaudeClientError",
    "LLMAdapter",
    "OpenAIAdapter",
    "OpenAIClient",
    "OpenAIClientError",
    "StubLLMAdapter",
    "create_claude_adapter_from_config",
    "create_llm_adapter_from_config",
    "create_openai_adapter_from_config",
]
