# Milestone 02: Artifact System - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

The artifact system is the **backbone** of Rice-Factor. It implements the Intermediate Representation (IR) pattern, treating artifacts as first-class data structures that drive all automation.

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Artifact System                           │
│                                                              │
│  ┌────────────────┐    ┌────────────────┐                   │
│  │  Pydantic      │    │   JSON Schema  │                   │
│  │  Models        │───▶│   Definitions  │                   │
│  │  (Python)      │    │   (JSON)       │                   │
│  └───────┬────────┘    └───────┬────────┘                   │
│          │                     │                             │
│          ▼                     ▼                             │
│  ┌─────────────────────────────────────────┐                │
│  │         Validation Engine               │                │
│  │  (Pydantic + jsonschema)                │                │
│  └───────────────────┬─────────────────────┘                │
│                      │                                       │
│          ┌───────────┴───────────┐                          │
│          ▼                       ▼                          │
│  ┌──────────────┐       ┌──────────────┐                    │
│  │   Storage    │       │   Registry   │                    │
│  │   (Loader)   │       │   (Index)    │                    │
│  └──────────────┘       └──────────────┘                    │
│          │                       │                          │
│          └───────────┬───────────┘                          │
│                      ▼                                       │
│          ┌──────────────────────┐                           │
│          │   Approvals Tracker  │                           │
│          └──────────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Hexagonal File Organization

```
rice_factor/
├── domain/                          # DOMAIN (innermost - no external deps)
│   ├── artifacts/                   # Artifact models
│   │   ├── __init__.py
│   │   ├── models.py                # ArtifactEnvelope, all payload types
│   │   └── enums.py                 # ArtifactStatus, ArtifactType
│   └── ports/                       # Port definitions
│       └── storage.py               # StoragePort protocol
│
├── adapters/                        # ADAPTERS (implement ports)
│   ├── storage/                     # Storage adapters
│   │   ├── __init__.py
│   │   └── filesystem.py            # FilesystemStorageAdapter
│   └── validators/                  # Validator adapters
│       ├── __init__.py
│       └── schema.py                # JSON Schema validator
│
└── config/
    └── container.py                 # Wires adapters to ports

schemas/                             # JSON Schema definitions
├── artifact.schema.json
├── project_plan.schema.json
├── scaffold_plan.schema.json
├── test_plan.schema.json
├── implementation_plan.schema.json
├── refactor_plan.schema.json
└── validation_result.schema.json
```

---

## 3. Artifact Envelope Model

### 3.1 Base Types

```python
# rice_factor/domain/artifacts/models.py
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Generic, TypeVar

class ArtifactStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    LOCKED = "locked"

class ArtifactType(str, Enum):
    PROJECT_PLAN = "ProjectPlan"
    ARCHITECTURE_PLAN = "ArchitecturePlan"
    SCAFFOLD_PLAN = "ScaffoldPlan"
    TEST_PLAN = "TestPlan"
    IMPLEMENTATION_PLAN = "ImplementationPlan"
    REFACTOR_PLAN = "RefactorPlan"
    VALIDATION_RESULT = "ValidationResult"

class CreatedBy(str, Enum):
    HUMAN = "human"
    LLM = "llm"

PayloadT = TypeVar("PayloadT", bound=BaseModel)

class ArtifactEnvelope(BaseModel, Generic[PayloadT]):
    """Universal wrapper for all artifacts."""

    artifact_type: ArtifactType
    artifact_version: str = "1.0"
    id: UUID = Field(default_factory=uuid4)
    status: ArtifactStatus = ArtifactStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: CreatedBy = CreatedBy.LLM
    depends_on: list[UUID] = Field(default_factory=list)
    payload: PayloadT

    class Config:
        use_enum_values = True
```

### 3.2 Status Transitions

```
┌───────┐     approve()     ┌──────────┐     lock()      ┌────────┐
│ DRAFT │ ─────────────────▶│ APPROVED │ ───────────────▶│ LOCKED │
└───────┘                   └──────────┘                 └────────┘
    │                                                         │
    │                    (no reverse)                         │
    └─────────────────────────────────────────────────────────┘
```

---

## 4. Artifact Type Models

### 4.1 ProjectPlan

```python
# rice_factor/domain/artifacts/models.py (continued)
from pydantic import BaseModel, Field

class Domain(BaseModel):
    """A bounded context within the system."""
    name: str
    responsibility: str

class Module(BaseModel):
    """A code module belonging to a domain."""
    name: str
    domain: str

class Constraints(BaseModel):
    """Technical constraints for the project."""
    architecture: str  # clean, hexagonal, ddd, custom
    languages: list[str]

class ProjectPlanPayload(BaseModel):
    """Payload for ProjectPlan artifact."""
    domains: list[Domain] = Field(min_length=1)
    modules: list[Module] = Field(min_length=1)
    constraints: Constraints
```

### 4.2 ScaffoldPlan

```python
# rice_factor/domain/artifacts/models.py (continued)
from pydantic import BaseModel, Field
from enum import Enum

class FileKind(str, Enum):
    SOURCE = "source"
    TEST = "test"
    CONFIG = "config"
    DOC = "doc"

class FileEntry(BaseModel):
    """A file to be scaffolded."""
    path: str
    description: str
    kind: FileKind

class ScaffoldPlanPayload(BaseModel):
    """Payload for ScaffoldPlan artifact."""
    files: list[FileEntry] = Field(min_length=1)
```

### 4.3 TestPlan

```python
# core/domain/artifacts/test_plan.py
from pydantic import BaseModel, Field

class TestDefinition(BaseModel):
    """A test to be implemented."""
    id: str
    target: str  # file path
    assertions: list[str] = Field(min_length=1)

class TestPlanPayload(BaseModel):
    """Payload for TestPlan artifact."""
    tests: list[TestDefinition] = Field(min_length=1)
```

### 4.4 ImplementationPlan

```python
# core/domain/artifacts/implementation_plan.py
from pydantic import BaseModel, Field

class ImplementationPlanPayload(BaseModel):
    """Payload for ImplementationPlan artifact."""
    target: str  # single file path
    steps: list[str] = Field(min_length=1)
    related_tests: list[str] = Field(default_factory=list)
```

### 4.5 RefactorPlan

```python
# core/domain/artifacts/refactor_plan.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class RefactorOperationType(str, Enum):
    MOVE_FILE = "move_file"
    RENAME_SYMBOL = "rename_symbol"
    EXTRACT_INTERFACE = "extract_interface"
    ENFORCE_DEPENDENCY = "enforce_dependency"

class RefactorOperation(BaseModel):
    """A single refactoring operation."""
    type: RefactorOperationType
    from_path: Optional[str] = Field(None, alias="from")
    to_path: Optional[str] = Field(None, alias="to")
    symbol: Optional[str] = None

class RefactorConstraints(BaseModel):
    """Constraints for refactoring."""
    preserve_behavior: bool = True

class RefactorPlanPayload(BaseModel):
    """Payload for RefactorPlan artifact."""
    goal: str
    operations: list[RefactorOperation] = Field(min_length=1)
    constraints: RefactorConstraints = Field(default_factory=RefactorConstraints)
```

### 4.6 ValidationResult

```python
# core/domain/artifacts/validation_result.py
from pydantic import BaseModel
from enum import Enum

class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"

class ValidationResultPayload(BaseModel):
    """Payload for ValidationResult artifact."""
    target: str
    status: ValidationStatus
    errors: list[str] = []
```

---

## 5. JSON Schema Definitions

### 5.1 Artifact Envelope Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "artifact.schema.json",
  "type": "object",
  "required": ["artifact_type", "artifact_version", "id", "status", "created_at", "created_by", "payload"],
  "properties": {
    "artifact_type": {
      "type": "string",
      "enum": ["ProjectPlan", "ArchitecturePlan", "ScaffoldPlan", "TestPlan", "ImplementationPlan", "RefactorPlan", "ValidationResult"]
    },
    "artifact_version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$"
    },
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "status": {
      "type": "string",
      "enum": ["draft", "approved", "locked"]
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "created_by": {
      "type": "string",
      "enum": ["human", "llm"]
    },
    "depends_on": {
      "type": "array",
      "items": {"type": "string", "format": "uuid"}
    },
    "payload": {
      "type": "object"
    }
  },
  "additionalProperties": false
}
```

### 5.2 Schema Generation Strategy

```python
# Generate JSON Schema from Pydantic models
from pydantic import BaseModel

def export_json_schema(model: type[BaseModel], path: str) -> None:
    """Export Pydantic model to JSON Schema file."""
    schema = model.model_json_schema()
    with open(path, 'w') as f:
        json.dump(schema, f, indent=2)
```

---

## 6. Validation Engine

### 6.1 Dual Validation Strategy

```python
# rice_factor/adapters/validators/schema.py
from pydantic import ValidationError as PydanticError
from jsonschema import validate, ValidationError as JsonSchemaError

class ArtifactValidator:
    """Validates artifacts using both Pydantic and JSON Schema."""

    def validate_pydantic(self, data: dict, model: type[BaseModel]) -> BaseModel:
        """Validate using Pydantic (Python type safety)."""
        try:
            return model.model_validate(data)
        except PydanticError as e:
            raise ArtifactValidationError(str(e))

    def validate_json_schema(self, data: dict, schema: dict) -> None:
        """Validate using JSON Schema (language-agnostic)."""
        try:
            validate(instance=data, schema=schema)
        except JsonSchemaError as e:
            raise ArtifactValidationError(e.message)

    def validate_full(self, data: dict, model: type[BaseModel], schema: dict) -> BaseModel:
        """Full validation: JSON Schema + Pydantic."""
        self.validate_json_schema(data, schema)
        return self.validate_pydantic(data, model)
```

---

## 7. Storage System

### 7.1 Artifact Loader

```python
# rice_factor/adapters/storage/filesystem.py
from pathlib import Path
import json

class ArtifactLoader:
    """Loads and saves artifacts to the filesystem."""

    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir

    def load(self, path: Path) -> ArtifactEnvelope:
        """Load artifact from JSON file."""
        with open(path) as f:
            data = json.load(f)
        # Validate and return
        return self._validate_and_parse(data)

    def save(self, artifact: ArtifactEnvelope, path: Path) -> None:
        """Save artifact to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(artifact.model_dump(mode='json'), f, indent=2)
```

### 7.2 Registry (Index)

```python
# rice_factor/adapters/storage/filesystem.py (continued)
from dataclasses import dataclass
from uuid import UUID

@dataclass
class RegistryEntry:
    id: UUID
    type: str
    path: str
    status: str

class ArtifactRegistry:
    """Manages the artifact index."""

    INDEX_PATH = "artifacts/_meta/index.json"

    def register(self, artifact: ArtifactEnvelope, path: str) -> None:
        """Add artifact to registry."""
        ...

    def lookup(self, artifact_id: UUID) -> RegistryEntry | None:
        """Find artifact by ID."""
        ...

    def list_by_type(self, artifact_type: str) -> list[RegistryEntry]:
        """List all artifacts of a type."""
        ...
```

### 7.3 Approvals Tracker

```python
# rice_factor/adapters/storage/filesystem.py (continued)
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class Approval:
    artifact_id: UUID
    approved_by: str
    approved_at: datetime

class ApprovalsTracker:
    """Tracks artifact approvals."""

    APPROVALS_PATH = "artifacts/_meta/approvals.json"

    def approve(self, artifact_id: UUID, approved_by: str = "human") -> None:
        """Record approval for artifact."""
        ...

    def is_approved(self, artifact_id: UUID) -> bool:
        """Check if artifact is approved."""
        ...

    def get_approval(self, artifact_id: UUID) -> Approval | None:
        """Get approval details."""
        ...
```

---

## 8. Immutability Enforcement

### 8.1 Lock Mechanism

```python
class ArtifactService:
    """Application service for artifact operations."""

    def lock(self, artifact_id: UUID) -> None:
        """Lock an artifact (only TestPlan supports this)."""
        artifact = self.loader.load_by_id(artifact_id)

        if artifact.artifact_type != ArtifactType.TEST_PLAN:
            raise ArtifactError("Only TestPlan can be locked")

        if artifact.status != ArtifactStatus.APPROVED:
            raise ArtifactError("Only approved artifacts can be locked")

        artifact.status = ArtifactStatus.LOCKED
        self.loader.save(artifact)

    def modify(self, artifact_id: UUID, updates: dict) -> None:
        """Modify an artifact (blocked if approved/locked)."""
        artifact = self.loader.load_by_id(artifact_id)

        if artifact.status in (ArtifactStatus.APPROVED, ArtifactStatus.LOCKED):
            raise ArtifactError(f"Cannot modify {artifact.status} artifact")

        # Apply updates...
```

---

## 9. Error Handling

### 9.1 Exception Types

```python
class ArtifactError(RiceFactorError):
    """Base class for artifact errors."""

class ArtifactValidationError(ArtifactError):
    """Schema validation failed."""

class ArtifactNotFoundError(ArtifactError):
    """Artifact not found."""

class ArtifactStatusError(ArtifactError):
    """Invalid status transition."""

class ArtifactDependencyError(ArtifactError):
    """Dependency not satisfied."""
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

```python
# tests/unit/domain/artifacts/test_project_plan.py
def test_project_plan_requires_domain():
    """ProjectPlan must have at least one domain."""
    with pytest.raises(ValidationError):
        ProjectPlanPayload(domains=[], modules=[...], constraints=...)

def test_artifact_status_transitions():
    """Test valid status transitions."""
    artifact = create_test_artifact(status=ArtifactStatus.DRAFT)
    artifact.approve()
    assert artifact.status == ArtifactStatus.APPROVED
```

### 10.2 Integration Tests

```python
# tests/integration/test_artifact_storage.py
def test_save_and_load_artifact(tmp_path):
    """Artifact can be saved and loaded correctly."""
    artifact = create_project_plan()
    loader = ArtifactLoader(tmp_path)

    loader.save(artifact, tmp_path / "test.json")
    loaded = loader.load(tmp_path / "test.json")

    assert loaded == artifact
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone design |
| 1.1.0 | 2026-01-10 | User Decision | Updated file paths for Hexagonal Architecture |
