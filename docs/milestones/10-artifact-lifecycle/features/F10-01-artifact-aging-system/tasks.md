# Feature F10-01: Artifact Aging System - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.1
> **Status**: In Progress
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-01-01 | Extend ArtifactEnvelope with timestamps | **Complete** | P0 |
| T10-01-02 | Add age calculation methods | **Complete** | P0 |
| T10-01-03 | Update storage adapter | **Complete** | P0 |
| T10-01-04 | Migrate existing artifacts | Deferred | P1 |
| T10-01-05 | Add artifact age CLI command | Pending | P0 |
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

**Files to Create**:
- [ ] `rice_factor/migrations/add_timestamps.py`

**Migration Logic**:
```python
def migrate_artifact(artifact_path: Path) -> None:
    data = json.loads(artifact_path.read_text())

    if "created_at" not in data:
        # Use file modification time as fallback
        stat = artifact_path.stat()
        data["created_at"] = datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat()
        data["updated_at"] = data["created_at"]

    artifact_path.write_text(json.dumps(data, indent=2))
```

**Acceptance Criteria**:
- [ ] Migration is idempotent
- [ ] Existing data preserved
- [ ] Uses file mtime as fallback

---

### T10-01-05: Add Artifact Age CLI Command

**Objective**: Show artifact ages via CLI.

**Files to Create/Modify**:
- [ ] `rice_factor/entrypoints/cli/commands/artifact.py`

**Command**:
```bash
rice-factor artifact age [--json] [--type TYPE]
```

**Output**:
```
Artifact Age Report
===================

ProjectPlan (id-001):
  Created: 2025-10-15
  Age: 3 months
  Last Reviewed: 2025-11-01 (2 months ago)

TestPlan (id-002):
  Created: 2025-11-01
  Age: 2 months
  Last Reviewed: Never
```

**Acceptance Criteria**:
- [ ] Lists all artifacts with ages
- [ ] Supports JSON output
- [ ] Can filter by type

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
