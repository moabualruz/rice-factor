# Feature: F02-07 Artifact Registry

## Status: Complete

## Description

Implement the artifact registry (index) that tracks all artifacts in the system and enables lookup by ID, type, or status.

## Requirements Reference

- M02-E-004: As soon as an artifact is saved, the system shall update `index.json`
- M02-S-004: While an artifact references `depends_on` artifacts, the system shall verify all dependencies are approved or locked
- M02-I-002: If an artifact references a non-existent dependency, then the system shall fail with a clear error
- M02-I-003: If an artifact references a draft dependency, then the system shall reject it

## Tasks

### Registry Data Model
- [x] Create `rice_factor/domain/artifacts/registry.py`
- [x] Implement `RegistryEntry` dataclass:
  - [x] `id: UUID`
  - [x] `artifact_type: ArtifactType`
  - [x] `path: str`
  - [x] `status: ArtifactStatus`
  - [x] `created_at: datetime`

### Registry Implementation
- [x] Create `rice_factor/adapters/storage/registry.py`
- [x] Implement `ArtifactRegistry` class:
  - [x] `register(artifact: ArtifactEnvelope, path: str) -> RegistryEntry`
  - [x] `unregister(artifact_id: UUID) -> bool`
  - [x] `update_status(artifact_id: UUID, status: ArtifactStatus) -> bool`
  - [x] `lookup(artifact_id: UUID) -> RegistryEntry | None`
  - [x] `list_by_type(artifact_type: ArtifactType) -> list[RegistryEntry]`
  - [x] `list_by_status(status: ArtifactStatus) -> list[RegistryEntry]`
  - [x] `list_all() -> list[RegistryEntry]`
- [x] Persist to `artifacts/_meta/index.json`
- [x] Load existing index on startup

### Dependency Validation
- [x] Implement `validate_dependencies(artifact: ArtifactEnvelope) -> None`
- [x] Check all `depends_on` UUIDs exist in registry
- [x] Check all dependencies are approved or locked
- [x] Raise `ArtifactDependencyError` for violations

### Integration with Storage
- [x] Registry can be used alongside storage adapters
- [x] Status updates reflected in registry
- [x] Removal reflected in registry

### Testing
- [x] Test registration and lookup (4 tests)
- [x] Test listing by type/status (4 tests)
- [x] Test dependency validation (5 tests)
- [x] Test index.json persistence (3 tests)
- [x] Test unregister and update_status (4 tests)
- [x] Test initialization (2 tests)
- [x] Test register edge cases (3 tests)

## Acceptance Criteria

- [x] Artifacts are registered when saved (via register() method)
- [x] Artifacts can be looked up by UUID
- [x] Artifacts can be listed by type or status
- [x] Dependencies are validated before artifact acceptance
- [x] Draft dependencies are rejected
- [x] Non-existent dependencies are rejected

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/artifacts/registry.py` | RegistryEntry data model |
| `rice_factor/domain/artifacts/__init__.py` | Updated with RegistryEntry export |
| `rice_factor/adapters/storage/registry.py` | ArtifactRegistry implementation |
| `rice_factor/adapters/storage/__init__.py` | Updated with ArtifactRegistry export |
| `tests/unit/adapters/storage/test_registry.py` | 25 unit tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation complete, all tests passing (25 new tests) |
