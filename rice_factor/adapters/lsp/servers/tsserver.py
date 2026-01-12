"""TypeScript Language Server configuration."""

from rice_factor.domain.ports.lsp import LSPServerConfig, MemoryExceedAction

TSSERVER_CONFIG = LSPServerConfig(
    name="typescript-language-server",
    command=["typescript-language-server", "--stdio"],
    languages=["typescript", "javascript"],
    memory_limit_mb=2048,  # Node.js single-threaded
    on_memory_exceed=MemoryExceedAction.KILL,
    timeout_seconds=60,
    initialization_timeout=30,
    install_hint="npm install -g typescript-language-server typescript",
    initialization_options={
        "preferences": {
            "includeInlayParameterNameHints": "none",
            "includeInlayVariableTypeHints": False,
        },
    },
)
