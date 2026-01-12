# Feature: F06-03 Architecture Validator

## Status: Pending

## Description

Implement the ArchitectureValidator that checks hexagonal architecture layer import rules. This validator analyzes Python import statements to detect violations of the hexagonal architecture constraints (e.g., domain importing from adapters). This feature is optional and can be disabled.

## Requirements Reference

- M06-U-003: Never auto-fix issues
- M06-U-004: Provide actionable error messages
- M06-AV-001: Architecture validator shall be optional (can be disabled)
- M06-AV-002: Check hexagonal layer imports
- M06-AV-003: Detect domain → adapter imports
- M06-AV-004: Never auto-fix violations
- M06-AV-005: Report exact import location
- raw/item-02-executor-design-and-pseudocode.md: Section 2.9 Architecture Validator

## Tasks

### ArchitectureValidator Implementation
- [ ] Create `rice_factor/adapters/validators/architecture_validator.py`
  - [ ] Define `ArchitectureValidator` class implementing `ValidatorPort`
  - [ ] Implement `name` property returning "architecture_validator"
  - [ ] Implement `validate(target, context) -> ValidationResult`
    - [ ] Scan domain/ directory for Python files
    - [ ] Extract imports from each file
    - [ ] Check imports against layer rules
    - [ ] Collect violations with file/line info
    - [ ] Return ValidationResult

### Import Extraction
- [ ] Implement `extract_imports(file_path: Path) -> list[ImportInfo]`
  - [ ] Parse Python file with `ast` module
  - [ ] Extract `import X` statements
  - [ ] Extract `from X import Y` statements
  - [ ] Track line numbers for each import
  - [ ] Handle syntax errors gracefully

### Import Info Type
- [ ] Define `ImportInfo` dataclass
  - [ ] `module: str` (imported module path)
  - [ ] `line: int` (line number)
  - [ ] `file: Path` (source file)

### Layer Rule Checking
- [ ] Implement `check_layer_rules(imports: list[ImportInfo], file_path: Path) -> list[str]`
  - [ ] Define forbidden imports for domain layer:
    - [ ] `rice_factor.adapters.*`
    - [ ] `rice_factor.entrypoints.*`
  - [ ] Check each import against rules
  - [ ] Generate violation message with exact location
  - [ ] Format: `{file}:{line}: domain imports from {layer}: {module}`

### Hexagonal Layer Detection
- [ ] Implement `get_layer(file_path: Path) -> str`
  - [ ] Return "domain" if path contains `/domain/`
  - [ ] Return "adapters" if path contains `/adapters/`
  - [ ] Return "entrypoints" if path contains `/entrypoints/`
  - [ ] Return "other" for other paths

### Optional Behavior
- [ ] Check `context.config.get("skip_architecture", False)` to skip
- [ ] If skipped, return status="passed" immediately
- [ ] Log that architecture check was skipped

### Exports
- [ ] Update `rice_factor/adapters/validators/__init__.py`
  - [ ] Export `ArchitectureValidator`

### Unit Tests
- [ ] Create `tests/unit/adapters/validators/test_architecture_validator.py`
  - [ ] Test `name` property returns "architecture_validator"
  - [ ] Test `validate` returns ValidationResult
  - [ ] Test clean architecture returns status="passed"
  - [ ] Test domain→adapter import returns status="failed"
  - [ ] Test domain→entrypoint import returns status="failed"
  - [ ] Test adapter→domain import returns status="passed" (allowed)
  - [ ] Test skip_architecture config option
  - [ ] Test import extraction from Python files
  - [ ] Test syntax error handling

### Test Fixtures
- [ ] Create test fixtures for architecture tests
  - [ ] Clean architecture example
  - [ ] Domain with forbidden adapter import
  - [ ] Domain with forbidden entrypoint import
  - [ ] Domain with allowed stdlib import

## Acceptance Criteria

- [ ] `ArchitectureValidator` implements `ValidatorPort`
- [ ] Detects domain → adapters imports
- [ ] Detects domain → entrypoints imports
- [ ] Reports exact file:line for each violation
- [ ] Can be disabled via config
- [ ] Does not modify any files (no auto-fix)
- [ ] Handles Python syntax errors gracefully
- [ ] All tests pass
- [ ] mypy passes
- [ ] ruff passes

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `rice_factor/adapters/validators/architecture_validator.py` | CREATE | Architecture validator implementation |
| `rice_factor/adapters/validators/__init__.py` | UPDATE | Export ArchitectureValidator |
| `tests/unit/adapters/validators/test_architecture_validator.py` | CREATE | Unit tests |
| `tests/fixtures/architecture/` | CREATE | Test fixture files |

## Dependencies

- F06-05: ValidationResult Generator (ValidatorPort, ValidationResult, ValidationContext)

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
