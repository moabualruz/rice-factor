"""LSP (Language Server Protocol) adapters.

Provides memory-safe LSP integration for language server operations
like rename, find references, and other semantic operations.
"""

from rice_factor.adapters.lsp.client import LSPClient
from rice_factor.adapters.lsp.memory_manager import MemoryManager

__all__ = ["LSPClient", "MemoryManager"]
