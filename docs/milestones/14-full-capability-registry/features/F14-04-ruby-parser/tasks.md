# F14-04: Ruby Refactoring Adapter - Tasks

---

## Tasks

### T14-04-01: Create Ruby Parser Adapter Base
- [x] Files: `rice_factor/adapters/refactoring/ruby_parser_adapter.py`

### T14-04-02: Implement move_file Operation
- [x] Files: `rice_factor/adapters/refactoring/ruby_parser_adapter.py`

### T14-04-03: Implement rename_symbol Operation
- [x] Files: `rice_factor/adapters/refactoring/ruby_parser_adapter.py`

### T14-04-04: Implement extract_interface (Module/RBS)
- [x] Files: `rice_factor/adapters/refactoring/ruby_parser_adapter.py`

### T14-04-05: Implement enforce_dependency Operation
- [x] Files: `rice_factor/adapters/refactoring/ruby_parser_adapter.py`

### T14-04-06: Add Ruby to Capability Registry
- [x] Files: `rice_factor/adapters/refactoring/__init__.py`, `rice_factor/adapters/refactoring/tool_registry.py`
- Note: Ruby already in capability_detector.py

### T14-04-07: Add Ruby Gem Detection
- [x] Files: `rice_factor/adapters/refactoring/capability_detector.py`
- Note: Already present in capability_detector.py

### T14-04-08: Unit Tests for Ruby Parser Adapter
- [x] Files: `tests/unit/adapters/refactoring/test_ruby_parser_adapter.py`

---

## Estimated Test Count: ~8
## Actual Test Count: 33 tests

## Features Implemented
- RubyDependencyRule and RubyDependencyViolation dataclasses
- Text-based rename with whole-project search
- Module move with require statement updates
- extract_interface generating both Ruby module and RBS signature file
- enforce_dependency with require statement and module reference analysis
- Full test coverage for all operations
