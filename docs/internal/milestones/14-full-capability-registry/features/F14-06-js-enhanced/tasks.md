# F14-06: Enhanced JavaScript/TypeScript Adapter - Tasks

---

## Tasks

### T14-06-01: Add extract_interface for TypeScript
- [x] Files: `rice_factor/adapters/refactoring/jscodeshift_adapter.py`
- [x] Added `EXTRACT_INTERFACE` to supported operations
- [x] Implemented `extract_interface()` method generating TypeScript interfaces
- [x] Private/protected method filtering

### T14-06-02: Add extract_interface for JavaScript (JSDoc)
- [x] Files: `rice_factor/adapters/refactoring/jscodeshift_adapter.py`
- [x] Implemented `_generate_jsdoc_typedef()` for JavaScript files
- [x] Generates JSDoc `@typedef` with `@property` annotations

### T14-06-03: Implement enforce_dependency Operation
- [x] Files: `rice_factor/adapters/refactoring/jscodeshift_adapter.py`
- [x] Added `JsDependencyRule` and `JsDependencyViolation` dataclasses
- [x] Implemented `enforce_dependency()` method
- [x] Added `_find_js_dependency_violations()` and `_check_js_file_violations()`
- [x] Added `_remove_js_import()` for fix mode

### T14-06-04: Support ESM and CommonJS Modules
- [x] Files: `rice_factor/adapters/refactoring/jscodeshift_adapter.py`
- [x] ES module import detection (`import { X } from '...'`)
- [x] CommonJS require detection (`const x = require('...')`)
- [x] Dynamic import detection (`await import('...')`)
- [x] Cross-platform path normalization (Windows backslash handling)

### T14-06-05: Unit Tests for Enhanced jscodeshift
- [x] Files: `tests/unit/adapters/refactoring/test_jscodeshift.py`
- [x] Added `TestJscodeshiftExtractInterface` class (7 tests)
- [x] Added `TestJscodeshiftEnforceDependency` class (9 tests)

---

## Actual Test Count: 16 new tests (40 total for jscodeshift adapter)

## Test Baseline: 2627 → 2643 tests

---

## Summary

Enhanced the jscodeshift adapter with M14 features:
- **extract_interface**: Generates TypeScript interfaces or JSDoc typedefs from classes
- **enforce_dependency**: Detects and optionally fixes import violations (ES modules, CommonJS, dynamic imports)
- Updated `__init__.py` to export `JsDependencyRule` and `JsDependencyViolation`
- Cross-platform compatible (Windows path handling)
