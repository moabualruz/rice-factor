# F14.5-05: Adapter Updates - Tasks

> **Status**: Complete

---

## Tasks

### T14.5-05-01: Update RefactorRequest model
- [x] Files: `rice_factor/domain/ports/refactor.py`
- Added `interface_name` field for EXTRACT_INTERFACE operation
- Added `dependency_rules` field for ENFORCE_DEPENDENCY operation
  - Format: `{"forbidden": ["pkg1"], "allowed": ["pkg2"]}`

### T14.5-05-02: Update gopls_adapter.py
- [x] Files: `rice_factor/adapters/refactoring/gopls_adapter.py`
- Added `_ast_adapter` attribute
- Added `_get_ast_adapter()` helper method
- Added `_parse_file()` helper method
- Implemented `_extract_interface()` using tree-sitter AST
- Implemented `_enforce_dependency()` using tree-sitter AST
- Added EXTRACT_INTERFACE and ENFORCE_DEPENDENCY to OPERATIONS

### T14.5-05-03: Update rust_analyzer_adapter.py
- [x] Files: `rice_factor/adapters/refactoring/rust_analyzer_adapter.py`
- Added `_ast_adapter` attribute
- Added `_get_ast_adapter()` helper method
- Added `_parse_file()` helper method
- Implemented `_extract_interface()` using tree-sitter AST
  - Generates trait definition from public impl methods
- Implemented `_enforce_dependency()` using tree-sitter AST
  - Checks use statements against forbidden/allowed rules
- Added EXTRACT_INTERFACE and ENFORCE_DEPENDENCY to OPERATIONS

### T14.5-05-04: Update openrewrite_adapter.py
- [x] Files: `rice_factor/adapters/refactoring/openrewrite_adapter.py`
- Added `_ast_adapter` attribute and helpers
- Replaced `_extract_java_methods()` with tree-sitter version
- Replaced `_extract_kotlin_methods()` with tree-sitter version
- Added `_extract_java_methods_regex()` as fallback
- Added `_extract_kotlin_methods_regex()` as fallback

### T14.5-05-05: Update roslyn_adapter.py
- [x] Files: `rice_factor/adapters/refactoring/roslyn_adapter.py`
- Added `_ast_adapter` attribute and helpers
- Replaced `_extract_csharp_methods()` with tree-sitter version
- Added `_extract_csharp_methods_regex()` as fallback

### T14.5-05-06: Update jscodeshift_adapter.py
- [x] Files: `rice_factor/adapters/refactoring/jscodeshift_adapter.py`
- Added `_ast_adapter` attribute and helpers
- Replaced `_extract_js_methods()` with tree-sitter version
- Handles both TypeScript and JavaScript
- Added `_extract_js_methods_regex()` as fallback

---

## Key Changes Per Adapter

### Pattern Applied to All Adapters

```python
# 1. Add attribute in __init__
self._ast_adapter: TreeSitterAdapter | None = None

# 2. Add helper to get/create adapter
def _get_ast_adapter(self) -> TreeSitterAdapter | None:
    if self._ast_adapter is not None:
        return self._ast_adapter
    try:
        self._ast_adapter = TreeSitterAdapter()
        return self._ast_adapter
    except (ImportError, RuntimeError):
        logger.warning("tree-sitter not available")
        return None

# 3. Add parse helper
def _parse_file(self, file_path: Path, content: str | None = None) -> ParseResult | None:
    ast_adapter = self._get_ast_adapter()
    if not ast_adapter:
        return None
    # ... parse and return

# 4. Update method extraction to try AST first, fallback to regex
def _extract_xxx_methods(...) -> list[dict]:
    parse_result = self._parse_file(...)
    if parse_result:
        # Use AST symbols
        return signatures

    # Fallback to regex
    return self._extract_xxx_methods_regex(...)
```

---

## Files Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/ports/refactor.py` | Added dependency_rules, interface_name |
| `rice_factor/adapters/refactoring/gopls_adapter.py` | AST for extract_interface, enforce_dependency |
| `rice_factor/adapters/refactoring/rust_analyzer_adapter.py` | AST for extract_interface, enforce_dependency |
| `rice_factor/adapters/refactoring/openrewrite_adapter.py` | AST for Java/Kotlin method extraction |
| `rice_factor/adapters/refactoring/roslyn_adapter.py` | AST for C# method extraction |
| `rice_factor/adapters/refactoring/jscodeshift_adapter.py` | AST for JS/TS method extraction |

---

## Test Results

- All 2948 tests pass
- All 279 refactoring adapter tests pass
- All mypy type checks pass
- All ruff linting checks pass

---

## Estimated Test Count: ~100 (existing tests)
## Actual Test Count: 279 refactoring tests + existing coverage
