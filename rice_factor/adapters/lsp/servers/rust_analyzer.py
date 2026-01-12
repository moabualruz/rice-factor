"""rust-analyzer configuration."""

from rice_factor.domain.ports.lsp import LSPServerConfig, MemoryExceedAction

RUST_ANALYZER_CONFIG = LSPServerConfig(
    name="rust-analyzer",
    command=["rust-analyzer"],
    languages=["rust"],
    memory_limit_mb=3072,  # rust-analyzer commonly uses 4-5GB
    on_memory_exceed=MemoryExceedAction.KILL,
    timeout_seconds=120,  # Rust analysis can be slow
    initialization_timeout=60,  # Initial indexing takes time
    install_hint="rustup component add rust-analyzer",
    initialization_options={
        "cargo": {
            "loadOutDirsFromCheck": True,
        },
        "procMacro": {
            "enable": True,
        },
        "checkOnSave": {
            "enable": False,  # Disable for one-shot mode
        },
    },
)
