"""CLI agent adapters for agentic coding tools.

This module provides adapters for CLI-based coding agents like
Claude Code, Codex, Aider, and others. These agents run as
subprocesses and can perform complex multi-file operations.
"""

from rice_factor.adapters.llm.cli.aider_adapter import (
    AiderAdapter,
    create_aider_adapter_from_config,
)
from rice_factor.adapters.llm.cli.base import (
    CLIAgentPort,
    CLITaskResult,
    DetectedAgent,
)
from rice_factor.adapters.llm.cli.claude_code_adapter import (
    ClaudeCodeAdapter,
    create_claude_code_adapter_from_config,
)
from rice_factor.adapters.llm.cli.codex_adapter import (
    CodexAdapter,
    create_codex_adapter_from_config,
)
from rice_factor.adapters.llm.cli.detector import (
    AgentConfig,
    CLIAgentDetector,
)
from rice_factor.adapters.llm.cli.gemini_cli_adapter import (
    GeminiCLIAdapter,
    create_gemini_cli_adapter_from_config,
)
from rice_factor.adapters.llm.cli.opencode_adapter import (
    OpenCodeAdapter,
    create_opencode_adapter_from_config,
)
from rice_factor.adapters.llm.cli.qwen_code_adapter import (
    QwenCodeAdapter,
    create_qwen_code_adapter_from_config,
)

# Type alias for any CLI agent adapter
CLIAgent = (
    ClaudeCodeAdapter
    | CodexAdapter
    | GeminiCLIAdapter
    | QwenCodeAdapter
    | AiderAdapter
    | OpenCodeAdapter
)

__all__ = [
    "AgentConfig",
    "AiderAdapter",
    "CLIAgent",
    "CLIAgentDetector",
    "CLIAgentPort",
    "CLITaskResult",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "DetectedAgent",
    "GeminiCLIAdapter",
    "OpenCodeAdapter",
    "QwenCodeAdapter",
    "create_aider_adapter_from_config",
    "create_claude_code_adapter_from_config",
    "create_codex_adapter_from_config",
    "create_gemini_cli_adapter_from_config",
    "create_opencode_adapter_from_config",
    "create_qwen_code_adapter_from_config",
]
