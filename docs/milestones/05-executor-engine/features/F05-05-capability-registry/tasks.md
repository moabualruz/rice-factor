# Feature: F05-05 Capability Registry

## Status: Pending

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
- [ ] Create `rice_factor/config/capability_registry.yaml`
  - [ ] Define python language capabilities
    - [ ] move_file: true
    - [ ] rename_symbol: true
    - [ ] extract_interface: false
    - [ ] enforce_dependency: false
  - [ ] Define rust language capabilities
    - [ ] move_file: true
    - [ ] rename_symbol: true
    - [ ] extract_interface: false
    - [ ] enforce_dependency: partial
  - [ ] Define go language capabilities
    - [ ] move_file: true
    - [ ] rename_symbol: true
    - [ ] extract_interface: false
    - [ ] enforce_dependency: false
  - [ ] Define javascript language capabilities
    - [ ] move_file: true
    - [ ] rename_symbol: true
    - [ ] extract_interface: false
    - [ ] enforce_dependency: false
  - [ ] Define typescript language capabilities
    - [ ] move_file: true
    - [ ] rename_symbol: true
    - [ ] extract_interface: false
    - [ ] enforce_dependency: false

### Capability Registry Class
- [ ] Create `rice_factor/adapters/executors/capability_registry.py`
  - [ ] Define `CapabilityRegistry` class
  - [ ] Implement `__init__(project_root: Path | None = None)`
    - [ ] Load bundled default registry
    - [ ] Check for project override
    - [ ] Merge configurations
  - [ ] Implement `check_capability(operation: str, language: str) -> bool`
    - [ ] Look up operation in language config
    - [ ] Return True only if explicitly true
    - [ ] Handle "partial" as False for strict checking
  - [ ] Implement `get_supported_operations(language: str) -> list[str]`
    - [ ] Return list of operations with true value
  - [ ] Implement `get_supported_languages() -> list[str]`
    - [ ] Return list of all configured languages
  - [ ] Implement `is_language_supported(language: str) -> bool`
    - [ ] Check if language exists in registry

### Registry Loading
- [ ] Implement `_load_bundled_registry() -> dict`
  - [ ] Use `importlib.resources` to load from package
  - [ ] Parse YAML safely
- [ ] Implement `_load_project_registry(project_root: Path) -> dict | None`
  - [ ] Check for `tools/registry/capability_registry.yaml`
  - [ ] Return None if not found
  - [ ] Parse YAML safely
- [ ] Implement `_merge_registries(base: dict, override: dict) -> dict`
  - [ ] Deep merge language configurations
  - [ ] Override takes precedence

### Capability Check Convenience Functions
- [ ] Implement `check_all_capabilities(operations: list[RefactorOperation], language: str) -> list[str]`
  - [ ] Check each operation
  - [ ] Return list of unsupported operations
- [ ] Implement `get_capability_status(operation: str, language: str) -> str`
  - [ ] Return "supported", "unsupported", or "partial"

### Registry Schema Validation
- [ ] Implement `_validate_registry_schema(data: dict) -> bool`
  - [ ] Check for "languages" key
  - [ ] Check each language has "operations" key
  - [ ] Check operations are valid types (bool or "partial")

### Adapter Exports
- [ ] Update `rice_factor/adapters/executors/__init__.py`
  - [ ] Export `CapabilityRegistry`

### Unit Tests
- [ ] Create `tests/unit/adapters/executors/test_capability_registry.py`
  - [ ] Test loads bundled default configuration
  - [ ] Test check_capability returns True for supported
  - [ ] Test check_capability returns False for unsupported
  - [ ] Test check_capability returns False for partial (strict mode)
  - [ ] Test project override merges correctly
  - [ ] Test project override takes precedence
  - [ ] Test unknown language returns False
  - [ ] Test unknown operation returns False
  - [ ] Test get_supported_operations returns correct list
  - [ ] Test get_supported_languages returns all languages
  - [ ] Test is_language_supported works correctly
  - [ ] Test check_all_capabilities returns unsupported list
  - [ ] Test invalid registry schema is rejected

### Integration Tests
- [ ] Create `tests/integration/adapters/executors/test_capability_registry_loading.py`
  - [ ] Test loads from bundled file
  - [ ] Test loads from project override file (using tmp_path)
  - [ ] Test merge behavior with real files

## Acceptance Criteria

- [ ] Default capability registry bundled with package
- [ ] Registry loads automatically on initialization
- [ ] Project override from `tools/registry/capability_registry.yaml` works
- [ ] `check_capability()` returns correct boolean
- [ ] Unknown languages/operations return False
- [ ] Partial support treated as False in strict mode
- [ ] Registry merge works correctly (override wins)
- [ ] All configured languages have correct capabilities
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

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
