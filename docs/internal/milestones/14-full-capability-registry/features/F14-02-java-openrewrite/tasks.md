# F14-02: Enhanced Java/Kotlin Adapter (OpenRewrite) - Tasks

---

## Tasks

### T14-02-01: Add extract_interface Recipe Support
- [x] Files: `rice_factor/adapters/refactoring/openrewrite_adapter.py`

### T14-02-02: Add enforce_dependency Recipe Support
- [x] Files: `rice_factor/adapters/refactoring/openrewrite_adapter.py`

### T14-02-03: Support Kotlin Interface Extraction
- [x] Files: `rice_factor/adapters/refactoring/openrewrite_adapter.py`

### T14-02-04: Create Custom OpenRewrite Recipes
- [x] Files: `rice_factor/adapters/refactoring/openrewrite_adapter.py`
- Note: Implemented local extract_interface and enforce_dependency methods
  with regex-based parsing. Added extract_interface_via_recipe() for
  recipe-based extraction when OpenRewrite plugin is available.

### T14-02-05: Unit Tests for Enhanced OpenRewrite
- [x] Files: `tests/unit/adapters/refactoring/test_openrewrite.py`

---

## Estimated Test Count: ~6
## Actual Test Count: 20 new tests (37 total for OpenRewrite adapter)
