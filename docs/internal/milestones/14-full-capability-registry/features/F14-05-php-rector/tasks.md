# F14-05: PHP Refactoring Adapter (Rector) - Tasks

---

## Tasks

### T14-05-01: Create Rector Adapter Base
- [x] Files: `rice_factor/adapters/refactoring/rector_adapter.py`

### T14-05-02: Implement move_file Operation
- [x] Files: `rice_factor/adapters/refactoring/rector_adapter.py`

### T14-05-03: Implement rename_symbol Operation
- [x] Files: `rice_factor/adapters/refactoring/rector_adapter.py`

### T14-05-04: Implement extract_interface Operation
- [x] Files: `rice_factor/adapters/refactoring/rector_adapter.py`

### T14-05-05: Implement enforce_dependency Operation
- [x] Files: `rice_factor/adapters/refactoring/rector_adapter.py`

### T14-05-06: Add PHP to Capability Registry
- [x] Files: `rice_factor/adapters/refactoring/__init__.py`, `rice_factor/adapters/refactoring/tool_registry.py`
- Note: PHP already in capability_detector.py

### T14-05-07: Add Rector/Composer Detection
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- Note: Already present in capability_detector.py

### T14-05-08: Unit Tests for Rector Adapter
- [x] Files: `tests/unit/adapters/refactoring/test_rector_adapter.py`

---

## Estimated Test Count: ~8
## Actual Test Count: 25 tests

## Features Implemented
- PhpDependencyRule and PhpDependencyViolation dataclasses
- Text-based rename with whole-project search
- Namespace move with use statement updates (escaped backslash handling)
- extract_interface for PHP classes with optional/nullable return types
- enforce_dependency with use statement analysis
- Full test coverage for all operations
