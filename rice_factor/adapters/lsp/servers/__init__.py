"""LSP server configurations.

Pre-configured settings for common language servers.
"""

from rice_factor.adapters.lsp.servers.gopls import GOPLS_CONFIG
from rice_factor.adapters.lsp.servers.pylsp import PYLSP_CONFIG
from rice_factor.adapters.lsp.servers.rust_analyzer import RUST_ANALYZER_CONFIG
from rice_factor.adapters.lsp.servers.tsserver import TSSERVER_CONFIG

__all__ = [
    "GOPLS_CONFIG",
    "PYLSP_CONFIG",
    "RUST_ANALYZER_CONFIG",
    "TSSERVER_CONFIG",
]
