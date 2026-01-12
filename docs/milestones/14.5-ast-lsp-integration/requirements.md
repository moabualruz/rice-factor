# Milestone 14.5: AST Parsing & LSP Integration - Requirements

> **Status**: Complete
> **Priority**: P0 (Foundation for IDE-like refactoring)
> **Dependencies**: M14 (Full Capability Registry)

---

## 1. Overview

Replace regex-based code parsing with proper AST parsing (like IDEs do) using tree-sitter, and integrate LSP servers only where AST isn't sufficient (rename, references). This milestone addresses the fundamental issue that "regex is totally wrong and defies the purpose of this tool!"

### Problem Statement

The refactoring adapters were using regex patterns to extract method signatures and analyze imports. This approach:
- Fails on complex syntax (nested generics, multiline signatures)
- Cannot understand code structure semantically
- Breaks easily with edge cases
- Doesn't match how professional IDEs work

### Solution

1. **Tree-sitter for AST**: Universal parser supporting 165+ languages
2. **LSP for semantic operations**: Only when AST isn't sufficient (rename, find references)
3. **Memory-safe LSP**: One-shot mode with memory limits to prevent resource exhaustion
4. **Graceful fallback**: AST → Regex when tree-sitter unavailable

### Target State

- All 9 languages use tree-sitter AST for code analysis
- LSP servers are killed after each task (one-shot mode)
- Memory limits enforced per server (configurable)
- Clear indication to users what requires LSP vs AST alone

---

## 2. Requirements

### REQ-14.5-01: AST Port Protocol

**Description**: Define domain port for language-agnostic code structure extraction.

**Acceptance Criteria**:
- [x] `ASTPort` protocol in `rice_factor/domain/ports/ast.py`
- [x] `SymbolKind` enum (CLASS, FUNCTION, METHOD, STRUCT, ENUM, etc.)
- [x] `Visibility` enum (PUBLIC, PRIVATE, PROTECTED, INTERNAL)
- [x] `ParameterInfo` dataclass (name, type_annotation, default_value, is_variadic)
- [x] `SymbolInfo` dataclass (name, kind, visibility, position, signature, etc.)
- [x] `ImportInfo` dataclass (module, symbols, line, is_relative, alias)
- [x] `ParseResult` dataclass (success, symbols, imports, errors, language)

---

### REQ-14.5-02: Tree-sitter Adapter

**Description**: Implement universal tree-sitter parser supporting all target languages.

**Acceptance Criteria**:
- [x] `TreeSitterAdapter` in `rice_factor/adapters/parsing/treesitter_adapter.py`
- [x] Language detection from file extension
- [x] Support 9 languages: Go, Rust, Java, Kotlin, TypeScript, JavaScript, Ruby, C#, PHP
- [x] Language-specific extractors in `rice_factor/adapters/parsing/languages/`
- [x] Base extractor class with common functionality
- [x] Query-based symbol extraction using tree-sitter queries

**Tool**: [tree-sitter-language-pack](https://github.com/grantjenks/py-tree-sitter-languages)

---

### REQ-14.5-03: LSP Port Protocol

**Description**: Define domain port for Language Server Protocol operations.

**Acceptance Criteria**:
- [x] `LSPPort` protocol in `rice_factor/domain/ports/lsp.py`
- [x] `LSPServerConfig` dataclass with memory limits and timeouts
- [x] `MemoryExceedAction` enum (KILL, WARN, IGNORE)
- [x] Support for rename, find_references, find_definition
- [x] Initialization options and install hints per server

---

### REQ-14.5-04: LSP Client with Memory Management

**Description**: Generic LSP client with one-shot execution and memory monitoring.

**Acceptance Criteria**:
- [x] `LSPClient` in `rice_factor/adapters/lsp/client.py`
- [x] One-shot mode: start → execute → kill
- [x] `MemoryManager` for monitoring server memory
- [x] Configurable memory limits per server
- [x] Auto-kill on memory exceed
- [x] Pre-configured servers for gopls, rust-analyzer, tsserver, pylsp

**Tool**: psutil for memory monitoring

---

### REQ-14.5-05: Configuration Schema

**Description**: Configuration for parsing and LSP integration.

**Acceptance Criteria**:
- [x] `parsing` section in `defaults.yaml` with provider settings
- [x] `lsp` section with server configurations
- [x] Memory limits per server (default: 2048MB)
- [x] Timeout settings (default: 60s)
- [x] Install hints for unavailable servers

---

### REQ-14.5-06: Adapter Updates (AST Integration)

**Description**: Update refactoring adapters to use tree-sitter AST instead of regex.

**Acceptance Criteria**:
- [x] `gopls_adapter.py` uses tree-sitter for extract_interface, enforce_dependency
- [x] `rust_analyzer_adapter.py` uses tree-sitter for extract_interface, enforce_dependency
- [x] `openrewrite_adapter.py` uses tree-sitter for Java/Kotlin method extraction
- [x] `roslyn_adapter.py` uses tree-sitter for C# method extraction
- [x] `jscodeshift_adapter.py` uses tree-sitter for JS/TS method extraction
- [x] Graceful regex fallback when tree-sitter unavailable
- [x] `RefactorRequest` extended with `dependency_rules` and `interface_name`

---

## 3. Non-Functional Requirements

### NFR-14.5-01: Performance

- Tree-sitter parsing should complete within 100ms for typical files
- LSP server startup should complete within 30s
- Memory monitoring overhead < 1% CPU

### NFR-14.5-02: Reliability

- Graceful fallback to regex if tree-sitter unavailable
- LSP servers killed cleanly on completion or memory exceed
- No memory leaks from orphaned LSP processes

### NFR-14.5-03: Testing

- All existing tests must continue to pass
- AST parsing covered by language-specific extractors
- Memory management tested with mocks

---

## 4. Exit Criteria

- [x] All 9 language extractors implemented and working
- [x] LSP client with memory management operational
- [x] Configuration schema defined and documented
- [x] All refactoring adapters updated to use tree-sitter
- [x] All 2948 tests pass
- [x] All mypy type checks pass
- [x] All ruff linting checks pass

---

## 5. Estimated Test Count

**Existing tests affected**: 279 refactoring adapter tests
**All tests passing**: 2948 total tests
