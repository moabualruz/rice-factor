# Milestone 14.5: AST Parsing & LSP Integration - Design

> **Status**: Complete
> **Priority**: P0

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Code Analysis Subsystem                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Domain Ports (Protocols)                                                    │
│    ├── ASTPort: Language-agnostic code structure extraction                  │
│    │     ├── SymbolKind, Visibility enums                                    │
│    │     ├── SymbolInfo, ImportInfo, ParameterInfo dataclasses               │
│    │     └── ParseResult with symbols + imports                              │
│    └── LSPPort: Language Server Protocol operations                          │
│          ├── LSPServerConfig with memory limits                              │
│          ├── MemoryExceedAction (KILL/WARN/IGNORE)                           │
│          └── rename, find_references, find_definition                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  Parsing Adapters (tree-sitter)                                              │
│    ├── TreeSitterAdapter: Universal parser                                   │
│    │     ├── Language detection from file extension                          │
│    │     ├── Query-based symbol extraction                                   │
│    │     └── Lazy loading of language parsers                                │
│    └── Language Extractors (9 languages):                                    │
│          ├── GoExtractor        # Go structs, interfaces, funcs              │
│          ├── RustExtractor      # Rust structs, traits, impl blocks          │
│          ├── JavaExtractor      # Java classes, interfaces, methods          │
│          ├── KotlinExtractor    # Kotlin classes, fun, suspend               │
│          ├── TypeScriptExtractor # TS classes, interfaces, types             │
│          ├── JavaScriptExtractor # JS classes, functions                     │
│          ├── RubyExtractor      # Ruby classes, modules, def                 │
│          ├── CSharpExtractor    # C# classes, interfaces, async              │
│          └── PHPExtractor       # PHP classes, traits, use                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  LSP Adapters (one-shot mode)                                                │
│    ├── LSPClient: Generic client with memory management                      │
│    │     ├── start() → execute() → kill()                                    │
│    │     └── Memory monitoring via MemoryManager                             │
│    ├── MemoryManager: Process memory monitoring with psutil                  │
│    └── Server Configs:                                                       │
│          ├── gopls_config.py      # Go LSP (gopls)                           │
│          ├── rust_analyzer.py     # Rust LSP (rust-analyzer)                 │
│          ├── tsserver_config.py   # TypeScript LSP (tsserver)                │
│          └── pylsp_config.py      # Python LSP (python-lsp-server)           │
├─────────────────────────────────────────────────────────────────────────────┤
│  Refactoring Adapters (UPDATED)                                              │
│    ├── gopls_adapter.py        # Now uses tree-sitter for extract_interface  │
│    ├── rust_analyzer_adapter.py # Now uses tree-sitter for extract_interface │
│    ├── openrewrite_adapter.py  # Now uses tree-sitter for method extraction  │
│    ├── roslyn_adapter.py       # Now uses tree-sitter for method extraction  │
│    └── jscodeshift_adapter.py  # Now uses tree-sitter for method extraction  │
└─────────────────────────────────────────────────────────────────────────────┘

Flow: AST-first, LSP-when-needed

  [Source Code]
       │
       ▼
  [TreeSitterAdapter.parse_file()]
       │
       ├── Symbols (classes, methods, functions)
       ├── Imports (modules, aliases)
       └── Structure (parent-child relationships)
       │
       ▼
  [Refactoring Adapter]
       │
       ├── extract_interface → Uses AST symbols ✓
       ├── enforce_dependency → Uses AST imports ✓
       │
       └── rename/references → Falls back to LSP
              │
              ▼
         [LSPClient (one-shot)]
              │
              ├── start_server()
              ├── execute_operation()
              ├── monitor_memory()
              └── kill_server()
```

---

## 2. Package Structure

```
rice_factor/
├── domain/ports/
│   ├── ast.py                      # NEW: ASTPort protocol
│   ├── lsp.py                      # NEW: LSPPort protocol
│   └── refactor.py                 # UPDATED: dependency_rules, interface_name
│
├── adapters/
│   ├── parsing/                    # NEW PACKAGE
│   │   ├── __init__.py
│   │   ├── treesitter_adapter.py   # Universal tree-sitter parser
│   │   └── languages/              # Language-specific extractors
│   │       ├── __init__.py
│   │       ├── base.py             # LanguageExtractor base class
│   │       ├── go.py               # GoExtractor
│   │       ├── rust.py             # RustExtractor
│   │       ├── java.py             # JavaExtractor
│   │       ├── kotlin.py           # KotlinExtractor
│   │       ├── typescript.py       # TypeScriptExtractor
│   │       ├── javascript.py       # JavaScriptExtractor
│   │       ├── ruby.py             # RubyExtractor
│   │       ├── csharp.py           # CSharpExtractor
│   │       └── php.py              # PHPExtractor
│   │
│   ├── lsp/                        # NEW PACKAGE
│   │   ├── __init__.py
│   │   ├── client.py               # LSPClient with one-shot mode
│   │   ├── memory_manager.py       # Memory monitoring with psutil
│   │   └── servers/                # Pre-configured server settings
│   │       ├── __init__.py
│   │       ├── gopls.py            # gopls config
│   │       ├── rust_analyzer.py    # rust-analyzer config
│   │       ├── tsserver.py         # tsserver config
│   │       └── pylsp.py            # python-lsp-server config
│   │
│   └── refactoring/                # UPDATED
│       ├── gopls_adapter.py        # +tree-sitter for extract_interface
│       ├── rust_analyzer_adapter.py # +tree-sitter for extract_interface
│       ├── openrewrite_adapter.py  # +tree-sitter for method extraction
│       ├── roslyn_adapter.py       # +tree-sitter for method extraction
│       └── jscodeshift_adapter.py  # +tree-sitter for method extraction
│
└── config/
    └── defaults.yaml               # UPDATED: parsing + lsp sections
```

---

## 3. Domain Port Interfaces

### ASTPort (rice_factor/domain/ports/ast.py)

```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

class SymbolKind(str, Enum):
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    TRAIT = "trait"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    FIELD = "field"
    CONSTANT = "constant"
    TYPE_ALIAS = "type_alias"
    MODULE = "module"
    NAMESPACE = "namespace"

class Visibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    PACKAGE = "package"

@dataclass
class ParameterInfo:
    name: str
    type_annotation: str | None = None
    default_value: str | None = None
    is_variadic: bool = False
    is_optional: bool = False

@dataclass
class SymbolInfo:
    name: str
    kind: SymbolKind
    visibility: Visibility
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    signature: str | None = None
    return_type: str | None = None
    parameters: list[ParameterInfo] = field(default_factory=list)
    modifiers: list[str] = field(default_factory=list)
    parent_name: str | None = None
    docstring: str | None = None
    generic_params: list[str] = field(default_factory=list)

@dataclass
class ImportInfo:
    module: str
    symbols: list[str] = field(default_factory=list)
    line: int = 0
    is_relative: bool = False
    alias: str | None = None
    is_wildcard: bool = False

@dataclass
class ParseResult:
    success: bool
    symbols: list[SymbolInfo]
    imports: list[ImportInfo]
    errors: list[str]
    language: str
    file_path: str | None = None

class ASTPort(Protocol):
    def parse_file(self, file_path: str, content: str | None = None) -> ParseResult:
        """Parse source file and extract structural information."""
        ...

    def get_supported_languages(self) -> list[str]:
        """Return list of supported language identifiers."""
        ...
```

### LSPPort (rice_factor/domain/ports/lsp.py)

```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Any

class MemoryExceedAction(str, Enum):
    KILL = "kill"
    WARN = "warn"
    IGNORE = "ignore"

@dataclass
class LSPServerConfig:
    name: str
    command: list[str]
    languages: list[str]
    memory_limit_mb: int = 2048
    on_memory_exceed: MemoryExceedAction = MemoryExceedAction.KILL
    timeout_seconds: int = 60
    initialization_timeout: int = 30
    install_hint: str | None = None
    initialization_options: dict[str, Any] | None = None

@dataclass
class Location:
    file_path: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int

class LSPPort(Protocol):
    def rename(
        self, file_path: str, line: int, column: int, new_name: str
    ) -> list[Location]:
        """Rename symbol at position across codebase."""
        ...

    def find_references(
        self, file_path: str, line: int, column: int
    ) -> list[Location]:
        """Find all references to symbol at position."""
        ...

    def find_definition(
        self, file_path: str, line: int, column: int
    ) -> Location | None:
        """Find definition of symbol at position."""
        ...
```

---

## 4. Configuration Schema

### defaults.yaml additions

```yaml
# AST Parsing Configuration
parsing:
  provider: "treesitter"  # treesitter | native | none
  fallback_to_regex: true
  cache_parsed_files: true
  max_file_size_kb: 1024  # Skip files larger than this

# LSP Server Configuration
lsp:
  mode: "one_shot"  # one_shot | persistent
  default_memory_limit_mb: 2048
  default_timeout_seconds: 60

  servers:
    gopls:
      command: ["gopls", "serve"]
      languages: ["go"]
      memory_limit_mb: 2048
      install_hint: "go install golang.org/x/tools/gopls@latest"

    rust_analyzer:
      command: ["rust-analyzer"]
      languages: ["rust"]
      memory_limit_mb: 4096
      install_hint: "rustup component add rust-analyzer"

    tsserver:
      command: ["typescript-language-server", "--stdio"]
      languages: ["typescript", "javascript"]
      memory_limit_mb: 2048
      install_hint: "npm install -g typescript-language-server"

    pylsp:
      command: ["pylsp"]
      languages: ["python"]
      memory_limit_mb: 1024
      install_hint: "pip install python-lsp-server"
```

---

## 5. Capability Matrix

| Operation          | AST (tree-sitter) | LSP Required | Notes                      |
|--------------------|-------------------|--------------|----------------------------|
| extract_interface  | Yes               | No           | Parse class, emit interface |
| enforce_dependency | Yes               | No           | Analyze imports            |
| move_file          | Partial           | Yes          | LSP for reference updates  |
| rename_symbol      | No                | Yes          | Semantic rename            |
| find_references    | No                | Yes          | Cross-file search          |

---

## 6. Dependencies

**Python packages** (added to pyproject.toml):
- `tree-sitter>=0.20.0` - Tree-sitter Python bindings
- `tree-sitter-language-pack>=0.20.0` - Pre-built language grammars
- `psutil>=5.9.0` - Process memory monitoring

**External tools** (optional, for LSP):
- `gopls` - Go LSP server
- `rust-analyzer` - Rust LSP server
- `typescript-language-server` - TypeScript/JavaScript LSP
- `python-lsp-server` - Python LSP server

---

## 7. Testing Strategy

| Component                | Test Type   | Coverage                          |
|--------------------------|-------------|-----------------------------------|
| LanguageExtractors (9)   | Unit        | Query patterns, symbol extraction |
| TreeSitterAdapter        | Unit        | Language detection, parsing       |
| LSPClient                | Unit/Mock   | Start/stop, memory monitoring     |
| MemoryManager            | Unit/Mock   | Process monitoring, kill logic    |
| Refactoring adapters     | Integration | AST + fallback paths              |

**Test counts**:
- All 2948 existing tests continue to pass
- 279 refactoring adapter tests cover AST integration
