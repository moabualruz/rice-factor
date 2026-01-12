"""Python Language Server configuration."""

from rice_factor.domain.ports.lsp import LSPServerConfig, MemoryExceedAction

PYLSP_CONFIG = LSPServerConfig(
    name="pylsp",
    command=["pylsp"],
    languages=["python"],
    memory_limit_mb=1024,  # Python projects typically smaller
    on_memory_exceed=MemoryExceedAction.WARN,  # Rope already handles most Python
    timeout_seconds=60,
    initialization_timeout=30,
    install_hint="pip install python-lsp-server",
    initialization_options={
        "pylsp": {
            "plugins": {
                "jedi_completion": {"enabled": False},
                "jedi_hover": {"enabled": False},
                "rope_rename": {"enabled": True},
            },
        },
    },
)
