# Feature: F05-05 Capability Registry

## Status: Complete

## Description

Implement the Capability Registry that tracks which refactoring operations are supported for each programming language. The registry loads from a bundled default configuration and can be overridden by a project-specific configuration.

## Requirements Reference

- M05-CR-001: Capability Registry shall load from bundled default configuration
- M05-CR-002: Capability Registry shall allow override from project `tools/registry/capability_registry.yaml`
- M05-CR-003: Capability Registry shall provide `check_capability(operation, language)` function
- M05-CR-004: If capability check fails, then system shall fail before execution
- M05-I-003: If operation is unsupported for language, then executor shall fail explicitly
- raw/04-repository-and-system-layout.md: Section 4.6 Capability Registry

## Tasks

### Default Capability Registry Configuration
- [x] Create `rice_factor/config/capability_registry.yaml`
  - [x] Define python language capabilities
    - [x] move_file: true
    - [x] rename_symbol: true
    - [x] extract_interface: false
    - [x] enforce_dependency: false
  - [x] Define rust language capabilities
    - [x] move_file: true
    - [x] rename_symbol: true
    - [x] extract_interface: false
    - [x] enforce_dependency: partial
  - [x] Define go language capabilities
    - [x] move_file: true
    - [x] rename_symbol: true
    - [x] extract_interface: false
    - [x] enforce_dependency: false
  - [x] Define javascript language capabilities
    - [x] move_file: true
    - [x] rename_symbol: true
    - [x] extract_interface: false
    - [x] enforce_dependency: false
  - [x] Define typescript language capabilities
    - [x] move_file: true
    - [x] rename_symbol: true
    - [x] extract_interface: false
    - [x] enforce_dependency: false

### Capability Registry Class
- [x] Create `rice_factor/adapters/executors/capability_registry.py`
  - [x] Define `CapabilityRegistry` class
  - [x] Implement `__init__(project_root: Path | None = None)`
    - [x] Load bundled default registry
    - [x] Check for project override
    - [x] Merge configurations
  - [x] Implement `check_capability(operation: str, language: str) -> bool`
    - [x] Look up operation in language config
    - [x] Return True only if explicitly true
    - [x] Handle "partial" as False for strict checking
  - [x] Implement `get_supported_operations(language: str) -> list[str]`
    - [x] Return list of operations with true value
  - [x] Implement `get_supported_languages() -> list[str]`
    - [x] Return list of all configured languages
  - [x] Implement `is_language_supported(language: str) -> bool`
    - [x] Check if language exists in registry

### Registry Loading
- [x] Implement `_load_bundled_registry() -> dict`
  - [x] Use `importlib.resources` to load from package
  - [x] Parse YAML safely
- [x] Implement `_load_project_registry(project_root: Path) -> dict | None`
  - [x] Check for `tools/registry/capability_registry.yaml`
  - [x] Return None if not found
  - [x] Parse YAML safely
- [x] Implement `_merge_registries(base: dict, override: dict) -> dict`
  - [x] Deep merge language configurations
  - [x] Override takes precedence

### Capability Check Convenience Functions
- [x] Implement `check_all_capabilities(operations: list[RefactorOperation], language: str) -> list[str]`
  - [x] Check each operation
  - [x] Return list of unsupported operations
- [x] Implement `get_capability_status(operation: str, language: str) -> str`
  - [x] Return "supported", "unsupported", or "partial"

### Registry Schema Validation
- [x] Implement `_validate_registry_schema(data: dict) -> bool`
  - [x] Check for "languages" key
  - [x] Check each language has "operations" key
  - [x] Check operations are valid types (bool or "partial")

### Adapter Exports
- [x] Update `rice_factor/adapters/executors/__init__.py`
  - [x] Export `CapabilityRegistry`

### Unit Tests
- [x] Create `tests/unit/adapters/executors/test_capability_registry.py`
  - [x] Test loads bundled default configuration
  - [x] Test check_capability returns True for supported
  - [x] Test check_capability returns False for unsupported
  - [x] Test check_capability returns False for partial (strict mode)
  - [x] Test project override merges correctly
  - [x] Test project override takes precedence
  - [x] Test unknown language returns False
  - [x] Test unknown operation returns False
  - [x] Test get_supported_operations returns correct list
  - [x] Test get_supported_languages returns all languages
  - [x] Test is_language_supported works correctly
  - [x] Test check_all_capabilities returns unsupported list
  - [x] Test invalid registry schema is rejected

### Integration Tests
- [x] Create `tests/integration/adapters/executors/test_capability_registry_loading.py`
  - [x] Test loads from bundled file
  - [x] Test loads from project override file (using tmp_path)
  - [x] Test merge behavior with real files

## Acceptance Criteria

- [x] Default capability registry bundled with package
- [x] Registry loads automatically on initialization
- [x] Project override from `tools/registry/capability_registry.yaml` works
- [x] `check_capability()` returns correct boolean
- [x] Unknown languages/operations return False
- [x] Partial support treated as False in strict mode
- [x] Registry merge works correctly (override wins)
- [x] All configured languages have correct capabilities
- [x] All tests pass
- [x] mypy passes
- [x] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/config/capability_registry.yaml` | CREATE | Default capability registry |
| `rice_factor/adapters/executors/capability_registry.py` | CREATE | CapabilityRegistry class |
| `rice_factor/adapters/executors/__init__.py` | UPDATE | Export CapabilityRegistry |
| `tests/unit/adapters/executors/test_capability_registry.py` | CREATE | Unit tests |
| `tests/integration/adapters/executors/test_capability_registry_loading.py` | CREATE | Integration tests |

## Dependencies

- F05-01: Executor Base Interface (UnsupportedOperationError)
- PyYAML: External dependency for YAML parsing

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Feature completed - all tasks implemented |
