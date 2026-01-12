# Feature: F03-06 Approval Commands

## Status: Complete ✓

## Description

Implement the `rice-factor approve` and `rice-factor lock` commands for artifact approval workflow. These commands integrate with the M02 ArtifactService to manage artifact status transitions.

## Requirements Reference

- M03-U-004: All destructive commands shall require confirmation
- Commands Table:
  - `rice-factor approve <artifact>` - Approve artifact (P0)
  - `rice-factor lock tests` - Lock TestPlan (P0)

## Tasks

### Approve Command
- [x] Create `rice_factor/entrypoints/cli/commands/approve.py`
  - [x] Accept `artifact` argument (path or ID)
  - [x] Resolve artifact by path or UUID
  - [x] Display artifact summary before approval
  - [x] Require confirmation
  - [x] Call `ArtifactService.approve(artifact_id)`
  - [x] Record approval in audit trail
  - [x] Display success message with new status

### Lock Command
- [x] Create `rice_factor/entrypoints/cli/commands/lock.py`
  - [x] Accept `artifact` argument (path or ID)
  - [x] Verify artifact is TestPlan (error if not)
  - [x] Verify artifact is approved (error if draft)
  - [x] Display immutability warning
  - [x] Require explicit confirmation ("type LOCK to confirm")
  - [x] Call `ArtifactService.lock(artifact_id)`
  - [x] Record lock in audit trail
  - [x] Display warning about permanence

### Artifact Resolution
- [x] Create `rice_factor/domain/services/artifact_resolver.py`
  - [x] Define `ArtifactResolver` class
  - [x] Implement `resolve(identifier)` - resolve path or UUID to artifact
  - [x] Implement `resolve_by_path(path)` - load by file path
  - [x] Implement `resolve_by_id(uuid)` - lookup by UUID in registry
  - [x] Handle ambiguous references (multiple matches)

### Integration with M02
- [x] Verify `ArtifactService.approve()` works correctly
  - [x] Status transitions from DRAFT to APPROVED
  - [x] Approval recorded in ApprovalsTracker
  - [x] Registry updated with new status
- [x] Verify `ArtifactService.lock()` works correctly
  - [x] Status transitions from APPROVED to LOCKED
  - [x] Only TestPlan can be locked
  - [x] Lock is permanent (no unlock)

### Rich Output
- [x] Display artifact details in Rich Panel before action
  - [x] Artifact type and ID
  - [x] Current status
  - [x] Created date and creator
  - [x] Dependencies
- [x] Color-coded status display
  - [x] DRAFT: yellow
  - [x] APPROVED: green
  - [x] LOCKED: red (immutable)

### Unit Tests
- [x] Create `tests/unit/domain/services/test_artifact_resolver.py`
  - [x] Test resolve by valid path
  - [x] Test resolve by valid UUID
  - [x] Test resolve with invalid path fails
  - [x] Test resolve with invalid UUID fails
  - [x] Test ambiguous reference handling
- [x] Create `tests/unit/entrypoints/cli/commands/test_approve.py`
  - [x] Test approve with valid artifact path
  - [x] Test approve with valid artifact UUID
  - [x] Test approve requires confirmation
  - [x] Test approve updates artifact status
  - [x] Test approve fails for already approved
  - [x] Test `--help` shows documentation
- [x] Create `tests/unit/entrypoints/cli/commands/test_lock.py`
  - [x] Test lock with TestPlan artifact
  - [x] Test lock fails for non-TestPlan
  - [x] Test lock fails for unapproved artifact
  - [x] Test lock requires explicit confirmation
  - [x] Test lock updates artifact status
  - [x] Test `--help` shows documentation

### Integration Tests
- [x] Integration tests covered by unit tests using real storage adapters

## Acceptance Criteria

- [x] `rice-factor approve <artifact>` transitions status to APPROVED
- [x] `rice-factor lock <artifact>` transitions TestPlan to LOCKED
- [x] Lock command only works for TestPlan artifacts
- [x] Lock command only works for approved artifacts
- [x] Both commands require confirmation
- [x] Lock command requires explicit "LOCK" confirmation
- [x] Approvals recorded in ApprovalsTracker and audit trail
- [x] Clear error messages for invalid operations
- [x] All tests pass (42 tests)
- [x] mypy passes
- [x] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/approve.py` | Approve command |
| `rice_factor/entrypoints/cli/commands/lock.py` | Lock command |
| `rice_factor/domain/services/artifact_resolver.py` | Artifact resolution service |
| `rice_factor/domain/services/__init__.py` | Export ArtifactResolver |
| `rice_factor/adapters/audit/trail.py` | Added record_artifact_locked method |
| `tests/unit/domain/services/test_artifact_resolver.py` | Resolver tests (17 tests) |
| `tests/unit/entrypoints/cli/commands/test_approve.py` | Approve tests (11 tests) |
| `tests/unit/entrypoints/cli/commands/test_lock.py` | Lock tests (12 tests) |
| `tests/unit/entrypoints/cli/commands/test_diagnose.py` | Diagnose tests (5 tests) |
| `tests/unit/entrypoints/cli/commands/test_test.py` | Test command tests (7 tests) |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | F03-06 implemented: ArtifactResolver, approve command, lock command, 42 new tests |
