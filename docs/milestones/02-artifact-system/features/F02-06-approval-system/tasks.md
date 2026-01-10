# Feature: F02-06 Approval System

## Status: Complete

## Description

Implement the approval tracking system that manages artifact status transitions and records approvals in `approvals.json`.

## Requirements Reference

- M02-S-001: While an artifact has status "draft", the system shall allow modifications
- M02-S-002: While an artifact has status "approved", the system shall reject modifications
- M02-S-003: While an artifact has status "locked", the system shall reject all changes permanently
- M02-E-003: As soon as an artifact is approved, the system shall update `approvals.json`
- M02-I-004: If a TestPlan artifact is locked and modification is attempted, then the system shall hard fail

## Tasks

### Approval Data Model
- [x] Create `rice_factor/domain/artifacts/approval.py`
- [x] Implement `Approval` dataclass:
  - [x] `artifact_id: UUID`
  - [x] `approved_by: str`
  - [x] `approved_at: datetime`

### Approvals Tracker
- [x] Create `rice_factor/adapters/storage/approvals.py`
- [x] Implement `ApprovalsTracker` class:
  - [x] `approve(artifact_id: UUID, approved_by: str) -> Approval`
  - [x] `is_approved(artifact_id: UUID) -> bool`
  - [x] `get_approval(artifact_id: UUID) -> Approval | None`
  - [x] `list_approvals() -> list[Approval]`
  - [x] `revoke(artifact_id: UUID) -> bool`
- [x] Persist to `artifacts/_meta/approvals.json`
- [x] Load existing approvals on startup

### Status Transition Service
- [x] Create `rice_factor/domain/services/artifact_service.py`
- [x] Implement `ArtifactService` class:
  - [x] `approve(artifact_id: UUID, approved_by: str) -> Approval`
  - [x] `lock(artifact_id: UUID) -> ArtifactEnvelope` (TestPlan only)
  - [x] `modify(artifact_id: UUID, updates: dict) -> ArtifactEnvelope`
  - [x] `get(artifact_id: UUID) -> ArtifactEnvelope`
  - [x] `is_approved(artifact_id: UUID) -> bool`
  - [x] `get_approval(artifact_id: UUID) -> Approval | None`
  - [x] `revoke_approval(artifact_id: UUID) -> bool`
- [x] Validate status transitions
- [x] Update artifact file on status change
- [x] Record approval in tracker

### Immutability Enforcement
- [x] Check status before any modification
- [x] Raise `ArtifactStatusError` for invalid transitions
- [x] Implement hard fail for locked TestPlan modification

### Testing
- [x] Test approval workflow (17 tests in test_approvals.py)
- [x] Test status transitions (25 tests in test_artifact_service.py)
- [x] Test modification rejection for approved/locked
- [x] Test approvals.json persistence

## Acceptance Criteria

- [x] Artifacts can be approved (draft -> approved)
- [x] TestPlan can be locked (approved -> locked)
- [x] Approved/locked artifacts reject modifications
- [x] Approvals are persisted to approvals.json
- [x] Invalid transitions raise clear errors

## Files Created/Modified

| File | Description |
|------|-------------|
| `rice_factor/domain/artifacts/approval.py` | Approval data model |
| `rice_factor/domain/artifacts/__init__.py` | Updated with Approval export |
| `rice_factor/adapters/storage/approvals.py` | ApprovalsTracker implementation |
| `rice_factor/adapters/storage/__init__.py` | Updated with ApprovalsTracker export |
| `rice_factor/domain/services/artifact_service.py` | ArtifactService implementation |
| `rice_factor/domain/services/__init__.py` | Updated with ArtifactService export |
| `tests/unit/adapters/storage/test_approvals.py` | 17 unit tests |
| `tests/unit/domain/services/__init__.py` | Package init |
| `tests/unit/domain/services/test_artifact_service.py` | 25 unit tests |

## Progress Log

| Date | Update |
|------|--------|
| 2026-01-10 | Task file created |
| 2026-01-10 | Implementation complete, all tests passing (42 new tests) |
