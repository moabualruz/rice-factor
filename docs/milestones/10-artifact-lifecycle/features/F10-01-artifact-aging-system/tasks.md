# Feature F10-01: Artifact Aging System - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T10-01-01 | Extend ArtifactEnvelope with timestamps | Pending | P0 |
| T10-01-02 | Add age calculation methods | Pending | P0 |
| T10-01-03 | Update storage adapter | Pending | P0 |
| T10-01-04 | Migrate existing artifacts | Pending | P1 |
| T10-01-05 | Add artifact age CLI command | Pending | P0 |
| T10-01-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T10-01-01: Extend ArtifactEnvelope with Timestamps

**Objective**: Add lifecycle tracking fields to artifacts.

**Files to Modify**:
- [ ] `rice_factor/domain/artifacts/base.py`

**New Fields**:
```python
@dataclass
class ArtifactEnvelope:
    # Existing fields...

    # Lifecycle fields (new)
    created_at: datetime
    updated_at: datetime
    last_reviewed_at: datetime | None = None
    review_notes: str | None = None
```

**Acceptance Criteria**:
- [ ] All new fields have proper types
- [ ] Datetime fields are timezone-aware
- [ ] Fields serialize to JSON correctly

---

### T10-01-02: Add Age Calculation Methods

**Objective**: Implement age calculation properties.

**Files to Modify**:
- [ ] `rice_factor/domain/artifacts/base.py`

**Implementation**:
```python
@property
def age_days(self) -> int:
    """Calculate artifact age in days."""
    return (datetime.now(timezone.utc) - self.created_at).days

@property
def age_months(self) -> float:
    """Calculate artifact age in months."""
    return self.age_days / 30.44

@property
def days_since_review(self) -> int | None:
    """Days since last review."""
    if self.last_reviewed_at is None:
        return None
    return (datetime.now(timezone.utc) - self.last_reviewed_at).days
```

**Acceptance Criteria**:
- [ ] age_days returns integer
- [ ] age_months returns float
- [ ] days_since_review handles None

---

### T10-01-03: Update Storage Adapter

**Objective**: Persist and load timestamp fields.

**Files to Modify**:
- [ ] `rice_factor/adapters/storage/filesystem_adapter.py`

**Implementation**:
- [ ] Serialize datetime to ISO-8601
- [ ] Parse datetime from JSON
- [ ] Handle missing fields (migration)

**Acceptance Criteria**:
- [ ] Timestamps persisted correctly
- [ ] Old artifacts load without error
- [ ] UTC timezone preserved

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

**Files to Create**:
- [ ] `tests/unit/domain/artifacts/test_aging.py`

**Test Cases**:
- [ ] age_days calculation
- [ ] age_months calculation
- [ ] days_since_review with review
- [ ] days_since_review without review
- [ ] Timestamp serialization
- [ ] Timestamp deserialization
- [ ] Migration of old artifacts

**Acceptance Criteria**:
- [ ] All calculations verified
- [ ] Edge cases covered

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
