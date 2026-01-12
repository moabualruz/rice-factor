# Feature: F02-05 Artifact Storage

## Status: Complete

## Description

Implement the filesystem-based storage adapter for loading and saving artifacts as JSON files.

## Requirements Reference

- M02-U-006: Artifacts shall be serializable to JSON with no data loss
- M02-U-007: Artifacts shall be deserializable from JSON with full validation
- M02-E-004: As soon as an artifact is saved, the system shall update `index.json`

## Tasks

### Storage Port
- [x] Create `rice_factor/domain/ports/storage.py`
- [x] Define `StoragePort` protocol with:
  - [x] `save(artifact: ArtifactEnvelope, path: Path) -> None`
  - [x] `load(path: Path) -> ArtifactEnvelope`
  - [x] `load_by_id(artifact_id: UUID) -> ArtifactEnvelope`
  - [x] `exists(artifact_id: UUID) -> bool`
  - [x] `delete(artifact_id: UUID) -> None`
  - [x] `list_by_type(artifact_type: ArtifactType) -> list[ArtifactEnvelope]`
  - [x] `get_path_for_artifact(artifact_id: UUID, artifact_type: ArtifactType) -> Path`

### Filesystem Adapter
- [x] Update `rice_factor/adapters/storage/__init__.py`
- [x] Create `rice_factor/adapters/storage/filesystem.py`
- [x] Implement `FilesystemStorageAdapter`:
  - [x] Load artifact from JSON file
  - [x] Validate on load
  - [x] Save artifact to JSON file
  - [x] Create parent directories if needed
  - [x] Use consistent JSON formatting (indent=2)

### Path Management
- [x] Define artifact path conventions:
  - [x] `artifacts/<type_dir>/<uuid>.json`
- [x] Implement path resolution logic

### Serialization
- [x] Handle UUID serialization
- [x] Handle datetime serialization (ISO 8601)
- [x] Handle enum serialization
- [x] Ensure round-trip consistency (load -> save -> load)

### Testing
- [x] Write unit tests for save/load
- [x] Test round-trip consistency
- [x] Test path creation
- [x] Test invalid JSON handling

## Acceptance Criteria

- [x] Artifacts can be saved to JSON files
- [x] Artifacts can be loaded from JSON files
- [x] Loaded artifacts are validated automatically
- [x] Serialization is lossless (round-trip)
- [x] Parent directories are created automatically

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/ports/storage.py` | StoragePort protocol |
| `rice_factor/domain/ports/__init__.py` | Updated with StoragePort export |
| `rice_factor/adapters/storage/__init__.py` | Package exports |
| `rice_factor/adapters/storage/filesystem.py` | FilesystemStorageAdapter implementation |
| `tests/unit/adapters/storage/test_filesystem.py` | 24 unit tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation complete, all tests passing (24 tests) |
