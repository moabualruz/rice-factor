# Feature: F03-06 Approval Commands

## Status: Pending

## Description

Implement the `rice-factor approve` and `rice-factor lock` commands for artifact approval workflow. These commands integrate with the M02 ArtifactService to manage artifact status transitions.

## Requirements Reference

- M03-U-004: All destructive commands shall require confirmation
- Commands Table:
  - `rice-factor approve <artifact>` - Approve artifact (P0)
  - `rice-factor lock tests` - Lock TestPlan (P0)

## Tasks

### Approve Command
- [ ] Create `rice_factor/entrypoints/cli/commands/approve.py`
  - [ ] Accept `artifact` argument (path or ID)
  - [ ] Resolve artifact by path or UUID
  - [ ] Display artifact summary before approval
  - [ ] Require confirmation
  - [ ] Call `ArtifactService.approve(artifact_id)`
  - [ ] Record approval in audit trail
  - [ ] Display success message with new status

### Lock Command
- [ ] Create `rice_factor/entrypoints/cli/commands/lock.py`
  - [ ] Accept `artifact` argument (path or ID)
  - [ ] Verify artifact is TestPlan (error if not)
  - [ ] Verify artifact is approved (error if draft)
  - [ ] Display immutability warning
  - [ ] Require explicit confirmation ("type LOCK to confirm")
  - [ ] Call `ArtifactService.lock(artifact_id)`
  - [ ] Record lock in audit trail
  - [ ] Display warning about permanence

### Artifact Resolution
- [ ] Create `rice_factor/domain/services/artifact_resolver.py`
  - [ ] Define `ArtifactResolver` class
  - [ ] Implement `resolve(identifier)` - resolve path or UUID to artifact
  - [ ] Implement `resolve_by_path(path)` - load by file path
  - [ ] Implement `resolve_by_id(uuid)` - lookup by UUID in registry
  - [ ] Handle ambiguous references (multiple matches)

### Integration with M02
- [ ] Verify `ArtifactService.approve()` works correctly
  - [ ] Status transitions from DRAFT to APPROVED
  - [ ] Approval recorded in ApprovalsTracker
  - [ ] Registry updated with new status
- [ ] Verify `ArtifactService.lock()` works correctly
  - [ ] Status transitions from APPROVED to LOCKED
  - [ ] Only TestPlan can be locked
  - [ ] Lock is permanent (no unlock)

### Rich Output
- [ ] Display artifact details in Rich Panel before action
  - [ ] Artifact type and ID
  - [ ] Current status
  - [ ] Created date and creator
  - [ ] Dependencies
- [ ] Color-coded status display
  - [ ] DRAFT: yellow
  - [ ] APPROVED: green
  - [ ] LOCKED: red (immutable)

### Unit Tests
- [ ] Create `tests/unit/domain/services/test_artifact_resolver.py`
  - [ ] Test resolve by valid path
  - [ ] Test resolve by valid UUID
  - [ ] Test resolve with invalid path fails
  - [ ] Test resolve with invalid UUID fails
  - [ ] Test ambiguous reference handling
- [ ] Create `tests/unit/entrypoints/cli/commands/test_approve.py`
  - [ ] Test approve with valid artifact path
  - [ ] Test approve with valid artifact UUID
  - [ ] Test approve requires confirmation
  - [ ] Test approve updates artifact status
  - [ ] Test approve fails for already approved
  - [ ] Test `--help` shows documentation
- [ ] Create `tests/unit/entrypoints/cli/commands/test_lock.py`
  - [ ] Test lock with TestPlan artifact
  - [ ] Test lock fails for non-TestPlan
  - [ ] Test lock fails for unapproved artifact
  - [ ] Test lock requires explicit confirmation
  - [ ] Test lock updates artifact status
  - [ ] Test `--help` shows documentation

### Integration Tests
- [ ] Create `tests/integration/cli/test_approval_flow.py`
  - [ ] Test full plan -> approve -> lock flow
  - [ ] Test approval recorded in ApprovalsTracker
  - [ ] Test registry updated correctly
  - [ ] Test audit trail records approvals

## Acceptance Criteria

- [ ] `rice-factor approve <artifact>` transitions status to APPROVED
- [ ] `rice-factor lock <artifact>` transitions TestPlan to LOCKED
- [ ] Lock command only works for TestPlan artifacts
- [ ] Lock command only works for approved artifacts
- [ ] Both commands require confirmation
- [ ] Lock command requires explicit "LOCK" confirmation
- [ ] Approvals recorded in ApprovalsTracker and audit trail
- [ ] Clear error messages for invalid operations
- [ ] All tests pass (25+ tests)
- [ ] mypy passes
- [ ] ruff passes

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/entrypoints/cli/commands/approve.py` | Approve command |
| `rice_factor/entrypoints/cli/commands/lock.py` | Lock command |
| `rice_factor/domain/services/artifact_resolver.py` | Artifact resolution service |
| `rice_factor/entrypoints/cli/main.py` | Register commands |
| `tests/unit/domain/services/test_artifact_resolver.py` | Resolver tests |
| `tests/unit/entrypoints/cli/commands/test_approve.py` | Approve tests |
| `tests/unit/entrypoints/cli/commands/test_lock.py` | Lock tests |
| `tests/integration/cli/test_approval_flow.py` | Integration tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
