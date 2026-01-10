"""LLM provider adapters (Claude, OpenAI, local models)."""

from rice_factor.adapters.llm.claude import ClaudeAdapter, create_claude_adapter_from_config
from rice_factor.adapters.llm.claude_client import ClaudeClient, ClaudeClientError
from rice_factor.adapters.llm.openai_adapter import (
    OpenAIAdapter,
    create_openai_adapter_from_config,
)
from rice_factor.adapters.llm.openai_client import OpenAIClient, OpenAIClientError
from rice_factor.adapters.llm.stub import StubLLMAdapter

__all__ = [
    "ClaudeAdapter",
    "ClaudeClient",
    "ClaudeClientError",
    "OpenAIAdapter",
    "OpenAIClient",
    "OpenAIClientError",
    "StubLLMAdapter",
    "create_claude_adapter_from_config",
    "create_openai_adapter_from_config",
]
