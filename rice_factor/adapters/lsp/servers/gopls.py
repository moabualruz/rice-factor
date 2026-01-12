"""gopls (Go Language Server) configuration."""

from rice_factor.domain.ports.lsp import LSPServerConfig, MemoryExceedAction

GOPLS_CONFIG = LSPServerConfig(
    name="gopls",
    command=["gopls", "serve"],
    languages=["go"],
    memory_limit_mb=4096,  # gopls can use 9-14GB on large projects
    on_memory_exceed=MemoryExceedAction.KILL,
    timeout_seconds=60,
    initialization_timeout=30,
    install_hint="go install golang.org/x/tools/gopls@latest",
    initialization_options={
        "staticcheck": True,
        "analyses": {
            "unusedparams": True,
            "shadow": True,
        },
    },
)
