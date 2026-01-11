# Feature F10-01: Artifact Aging System - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.2
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-01-01 | Extend ArtifactEnvelope with timestamps | **Complete** | P0 |
| T10-01-02 | Add age calculation methods | **Complete** | P0 |
| T10-01-03 | Update storage adapter | **Complete** | P0 |
| T10-01-04 | Migrate existing artifacts | **Complete** | P1 |
| T10-01-05 | Add artifact age CLI command | **Complete** | P0 |
| T10-01-06 | Write unit tests | **Complete** | P0 |

---

## 2. Task Details

### T10-01-01: Extend ArtifactEnvelope with Timestamps

**Objective**: Add lifecycle tracking fields to artifacts.

**Files Modified**:
- [x] `rice_factor/domain/artifacts/envelope.py`
- [x] `schemas/artifact.schema.json`

**New Fields**:
- [x] `updated_at: datetime` - timestamp of last modification
- [x] `last_reviewed_at: datetime | None` - timestamp of last review
- [x] `review_notes: str | None` - notes from last review

**Acceptance Criteria**:
- [x] All new fields have proper types
- [x] Datetime fields are timezone-aware (UTC)
- [x] Fields serialize to JSON correctly
- [x] JSON Schema updated to allow new fields

---

### T10-01-02: Add Age Calculation Methods

**Objective**: Implement age calculation properties.

**Files Modified**:
- [x] `rice_factor/domain/artifacts/envelope.py`

**Implementation**:
- [x] `age_days` property - returns integer days since creation
- [x] `age_months` property - returns float months since creation
- [x] `days_since_review` property - returns days since review or None
- [x] `days_since_update` property - returns days since last update

**Acceptance Criteria**:
- [x] age_days returns integer
- [x] age_months returns float
- [x] days_since_review handles None
- [x] Timezone-aware datetime comparisons

---

### T10-01-03: Update Storage Adapter

**Objective**: Persist and load timestamp fields.

**Note**: Pydantic BaseModel automatically handles datetime serialization to ISO-8601 format and deserialization. No additional adapter changes needed.

**Acceptance Criteria**:
- [x] Timestamps persisted correctly (via Pydantic)
- [x] Old artifacts load without error (new fields optional)
- [x] UTC timezone preserved

---

### T10-01-04: Migrate Existing Artifacts

**Objective**: Add timestamps to existing artifacts.

**Files Created**:
- [x] `rice_factor/migrations/__init__.py`
- [x] `rice_factor/migrations/add_timestamps.py`
- [x] `tests/unit/migrations/__init__.py`
- [x] `tests/unit/migrations/test_add_timestamps.py` (16 tests)

**CLI Command Added**:
- [x] `rice-factor artifact migrate` - Run the timestamp migration

**Features**:
- [x] Adds `created_at` and `updated_at` to artifacts missing them
- [x] Uses file modification time as fallback
- [x] Idempotent - safe to run multiple times
- [x] Preserves all existing artifact data
- [x] Skips `_meta` directories
- [x] Dry-run mode for previewing changes
- [x] JSON output format

**Acceptance Criteria**:
- [x] Migration is idempotent
- [x] Existing data preserved
- [x] Uses file mtime as fallback
- [x] 16 tests passing

---

### T10-01-05: Add Artifact Age CLI Command

**Objective**: Show artifact ages via CLI.

**Files Created**:
- [x] `rice_factor/entrypoints/cli/commands/artifact.py`

**Files Modified**:
- [x] `rice_factor/entrypoints/cli/main.py`
- [x] `rice_factor/entrypoints/cli/commands/__init__.py`

**Commands**:
- [x] `rice-factor artifact age` - List all artifacts with ages
- [x] `rice-factor artifact extend` - Extend artifact validity period

**Options (age)**:
- [x] `--path` - Project root path
- [x] `--type` - Filter by artifact type
- [x] `--json` - JSON output format

**Options (extend)**:
- [x] `--reason` - Required reason for extension
- [x] `--months` - Extension period (optional)
- [x] `--path` - Project root path

**Exit Codes**:
- 0: All artifacts healthy
- 1: Some artifacts need review (3+ months old)
- 2: Artifacts overdue (6+ months old)

**Acceptance Criteria**:
- [x] Lists all artifacts with ages
- [x] Supports JSON output
- [x] Can filter by type
- [x] extend command updates last_reviewed_at
- [x] Cannot extend LOCKED artifacts

---

### T10-01-06: Write Unit Tests

**Objective**: Test aging system functionality.

**Files Modified**:
- [x] `tests/unit/domain/artifacts/test_envelope.py` (12 new tests)

**Test Cases**:
- [x] test_updated_at_defaults_to_created_at
- [x] test_last_reviewed_at_defaults_to_none
- [x] test_review_notes_defaults_to_none
- [x] test_can_set_lifecycle_fields
- [x] test_age_days_calculation
- [x] test_age_days_for_new_artifact
- [x] test_age_months_calculation
- [x] test_age_months_for_new_artifact
- [x] test_days_since_review_when_never_reviewed
- [x] test_days_since_review_calculation
- [x] test_days_since_update_calculation
- [x] test_days_since_update_for_new_artifact

**Acceptance Criteria**:
- [x] All calculations verified
- [x] Edge cases covered (32 total tests in envelope file)

---

## 3. Task Dependencies

```
T10-01-01 (Fields) ──→ T10-01-02 (Methods) ──→ T10-01-03 (Storage)
                                                      │
                                           ┌──────────┴──────────┐
                                           ↓                     ↓
                                   T10-01-04 (Migrate)   T10-01-05 (CLI)
                                           │                     │
                                           └──────────┬──────────┘
                                                      ↓
                                              T10-01-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T10-01-01 | Low | Field additions |
| T10-01-02 | Low | Simple math |
| T10-01-03 | Medium | Serialization |
| T10-01-04 | Medium | Migration script |
| T10-01-05 | Medium | CLI output |
| T10-01-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.0.1 | 2026-01-11 | Implementation | Core aging system complete - 32 tests, T10-01-04 deferred, T10-01-05 pending |
| 1.0.2 | 2026-01-11 | Implementation | CLI commands complete - 50 tests (32 envelope + 18 artifact CLI), T10-01-04 deferred |
