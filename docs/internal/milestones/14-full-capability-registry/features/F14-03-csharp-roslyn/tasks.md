# F14-03: C# Roslyn Adapter - Tasks

---

## Tasks

### T14-03-01: Create Roslyn Adapter Base
- [x] Files: `rice_factor/adapters/refactoring/roslyn_adapter.py`

### T14-03-02: Implement move_file Operation
- [x] Files: `rice_factor/adapters/refactoring/roslyn_adapter.py`

### T14-03-03: Implement rename_symbol Operation
- [x] Files: `rice_factor/adapters/refactoring/roslyn_adapter.py`

### T14-03-04: Implement extract_interface Operation
- [x] Files: `rice_factor/adapters/refactoring/roslyn_adapter.py`

### T14-03-05: Implement enforce_dependency Operation
- [x] Files: `rice_factor/adapters/refactoring/roslyn_adapter.py`

### T14-03-06: Add dotnet/Roslyn Dependency Detection
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- Note: Already present in capability_detector.py

### T14-03-07: Unit Tests for Roslyn Adapter
- [x] Files: `tests/unit/adapters/refactoring/test_roslyn_adapter.py`

---

## Estimated Test Count: ~8
## Actual Test Count: 23 tests

## Features Implemented
- CSharpDependencyRule and CSharpDependencyViolation dataclasses
- Manual rename with text-based fallback (Roslynator integration planned)
- Namespace move with using statement updates
- extract_interface for C# classes
- enforce_dependency with using statement analysis
- Full test coverage for all operations
