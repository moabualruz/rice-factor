# F14.5-01: AST Port Protocol - Tasks

> **Status**: Complete

---

## Tasks

### T14.5-01-01: Create ASTPort protocol
- [x] Files: `rice_factor/domain/ports/ast.py`
- Created protocol for language-agnostic code structure extraction
- No external dependencies (domain layer)

### T14.5-01-02: Define SymbolKind enum
- [x] 13 symbol kinds: CLASS, INTERFACE, STRUCT, ENUM, TRAIT, FUNCTION, METHOD, PROPERTY, FIELD, CONSTANT, TYPE_ALIAS, MODULE, NAMESPACE

### T14.5-01-03: Define Visibility enum
- [x] 5 visibility levels: PUBLIC, PRIVATE, PROTECTED, INTERNAL, PACKAGE

### T14.5-01-04: Define ParameterInfo dataclass
- [x] Fields: name, type_annotation, default_value, is_variadic, is_optional

### T14.5-01-05: Define SymbolInfo dataclass
- [x] Fields: name, kind, visibility, line_start, line_end, column_start, column_end, signature, return_type, parameters, modifiers, parent_name, docstring, generic_params

### T14.5-01-06: Define ImportInfo dataclass
- [x] Fields: module, symbols, line, is_relative, alias, is_wildcard

### T14.5-01-07: Define ParseResult dataclass
- [x] Fields: success, symbols, imports, errors, language, file_path

---

## Files Created

| File | Description |
|------|-------------|
| `rice_factor/domain/ports/ast.py` | ASTPort protocol with all dataclasses |

---

## Estimated Test Count: ~10
## Actual Test Count: Type-checked via mypy
