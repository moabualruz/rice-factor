# F14.5-03: LSP Client with Memory Management - Tasks

> **Status**: Complete

---

## Tasks

### T14.5-03-01: Create LSPPort protocol
- [x] Files: `rice_factor/domain/ports/lsp.py`
- Protocol for LSP operations (rename, find_references, find_definition)
- LSPServerConfig dataclass with memory limits
- MemoryExceedAction enum (KILL, WARN, IGNORE)
- Location dataclass for position info

### T14.5-03-02: Create LSPClient
- [x] Files: `rice_factor/adapters/lsp/client.py`
- One-shot execution mode: start → execute → kill
- JSON-RPC protocol implementation
- Request/response handling with timeouts
- Integration with MemoryManager

### T14.5-03-03: Create MemoryManager
- [x] Files: `rice_factor/adapters/lsp/memory_manager.py`
- Process memory monitoring using psutil
- Configurable memory limits per server
- Auto-kill on memory exceed
- Background monitoring thread

### T14.5-03-04: Create gopls server config
- [x] Files: `rice_factor/adapters/lsp/servers/gopls.py`
- Command: `gopls serve`
- Default memory limit: 2048MB
- Install hint: `go install golang.org/x/tools/gopls@latest`

### T14.5-03-05: Create rust-analyzer server config
- [x] Files: `rice_factor/adapters/lsp/servers/rust_analyzer.py`
- Command: `rust-analyzer`
- Default memory limit: 4096MB
- Install hint: `rustup component add rust-analyzer`

### T14.5-03-06: Create tsserver config
- [x] Files: `rice_factor/adapters/lsp/servers/tsserver.py`
- Command: `typescript-language-server --stdio`
- Default memory limit: 2048MB
- Install hint: `npm install -g typescript-language-server`

### T14.5-03-07: Create pylsp config
- [x] Files: `rice_factor/adapters/lsp/servers/pylsp.py`
- Command: `pylsp`
- Default memory limit: 1024MB
- Install hint: `pip install python-lsp-server`

---

## Files Created

| File | Description |
|------|-------------|
| `rice_factor/domain/ports/lsp.py` | LSPPort protocol |
| `rice_factor/adapters/lsp/__init__.py` | Package init |
| `rice_factor/adapters/lsp/client.py` | LSP client |
| `rice_factor/adapters/lsp/memory_manager.py` | Memory monitor |
| `rice_factor/adapters/lsp/servers/__init__.py` | Servers package |
| `rice_factor/adapters/lsp/servers/gopls.py` | gopls config |
| `rice_factor/adapters/lsp/servers/rust_analyzer.py` | rust-analyzer config |
| `rice_factor/adapters/lsp/servers/tsserver.py` | tsserver config |
| `rice_factor/adapters/lsp/servers/pylsp.py` | pylsp config |

---

## Key Design Decisions

1. **One-shot mode**: Servers are killed after each operation to prevent memory accumulation
2. **Memory limits**: Configurable per server (gopls=2GB, rust-analyzer=4GB, etc.)
3. **Graceful degradation**: If server unavailable, adapter falls back to regex

---

## Estimated Test Count: ~20
## Actual Test Count: Type-checked via mypy
