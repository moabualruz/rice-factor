# F14.5-02: Tree-sitter Adapter - Tasks

> **Status**: Complete

---

## Tasks

### T14.5-02-01: Create TreeSitterAdapter
- [x] Files: `rice_factor/adapters/parsing/treesitter_adapter.py`
- Universal parser implementing ASTPort
- Language detection from file extension
- Lazy loading of language parsers

### T14.5-02-02: Create LanguageExtractor base class
- [x] Files: `rice_factor/adapters/parsing/languages/base.py`
- Common functionality for all extractors
- Tree-sitter query execution helpers
- Node text extraction utilities

### T14.5-02-03: Create GoExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/go.py`
- Extracts: structs, interfaces, functions, methods
- Handles: type parameters, embedded types

### T14.5-02-04: Create RustExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/rust.py`
- Extracts: structs, enums, traits, impl blocks, functions
- Handles: pub/pub(crate)/pub(super), lifetimes, generics

### T14.5-02-05: Create JavaExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/java.py`
- Extracts: classes, interfaces, enums, methods
- Handles: annotations, generics, static imports

### T14.5-02-06: Create KotlinExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/kotlin.py`
- Extracts: classes, interfaces, objects, functions
- Handles: suspend, companion objects, extensions

### T14.5-02-07: Create TypeScriptExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/typescript.py`
- Extracts: classes, interfaces, types, functions
- Handles: generics, decorators, async

### T14.5-02-08: Create JavaScriptExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/javascript.py`
- Extracts: classes, functions, arrow functions
- Handles: ES6 modules, default exports

### T14.5-02-09: Create RubyExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/ruby.py`
- Extracts: classes, modules, methods
- Handles: attr_accessor, private/protected

### T14.5-02-10: Create CSharpExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/csharp.py`
- Extracts: classes, interfaces, structs, methods
- Handles: async, nullable, generics

### T14.5-02-11: Create PHPExtractor
- [x] Files: `rice_factor/adapters/parsing/languages/php.py`
- Extracts: classes, interfaces, traits, methods
- Handles: namespaces, use statements

---

## Files Created

| File | Description |
|------|-------------|
| `rice_factor/adapters/parsing/__init__.py` | Package init |
| `rice_factor/adapters/parsing/treesitter_adapter.py` | Main adapter |
| `rice_factor/adapters/parsing/languages/__init__.py` | Languages package |
| `rice_factor/adapters/parsing/languages/base.py` | Base extractor |
| `rice_factor/adapters/parsing/languages/go.py` | Go extractor |
| `rice_factor/adapters/parsing/languages/rust.py` | Rust extractor |
| `rice_factor/adapters/parsing/languages/java.py` | Java extractor |
| `rice_factor/adapters/parsing/languages/kotlin.py` | Kotlin extractor |
| `rice_factor/adapters/parsing/languages/typescript.py` | TypeScript extractor |
| `rice_factor/adapters/parsing/languages/javascript.py` | JavaScript extractor |
| `rice_factor/adapters/parsing/languages/ruby.py` | Ruby extractor |
| `rice_factor/adapters/parsing/languages/csharp.py` | C# extractor |
| `rice_factor/adapters/parsing/languages/php.py` | PHP extractor |

---

## Estimated Test Count: ~50
## Actual Test Count: Type-checked via mypy
