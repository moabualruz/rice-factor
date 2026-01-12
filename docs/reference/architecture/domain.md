# Domain Layer

The domain layer contains core business logic with zero external dependencies.

## Overview

```
rice_factor/domain/
├── artifacts/           # Artifact models
│   ├── envelope.py      # ArtifactEnvelope
│   ├── payloads.py      # Payload types
│   └── enums.py         # Enums
├── ports/               # Interface definitions
│   ├── llm.py           # LLMPort
│   ├── storage.py       # StoragePort
│   ├── executor.py      # ExecutorPort
│   └── validator.py     # ValidatorPort
├── services/            # Business logic
│   ├── artifact_service.py
│   ├── plan_service.py
│   └── executor_service.py
└── failures/            # Error models
    └── models.py
```

---

## Ports (Interfaces)

Ports define interfaces that adapters must implement. They use Python's `Protocol` for structural typing.

### LLMPort

Interface for LLM providers.

```python
# rice_factor/domain/ports/llm.py
from typing import Protocol

class LLMPort(Protocol):
    """Port for LLM interactions."""

    def generate(
        self,
        prompt: str,
        schema: dict | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Generate text from prompt.

        Args:
            prompt: The input prompt
            schema: Optional JSON schema for structured output
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        ...

    def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        """Generate structured output.

        Args:
            prompt: The input prompt
            response_model: Pydantic model for response

        Returns:
            Parsed response as model instance
        """
        ...
```

### StoragePort

Interface for artifact storage.

```python
# rice_factor/domain/ports/storage.py
from typing import Protocol
from rice_factor.domain.artifacts import ArtifactEnvelope

class StoragePort(Protocol):
    """Port for artifact storage."""

    def save(self, artifact: ArtifactEnvelope) -> None:
        """Save artifact to storage.

        Args:
            artifact: The artifact to save
        """
        ...

    def load(self, artifact_id: str) -> ArtifactEnvelope:
        """Load artifact from storage.

        Args:
            artifact_id: The artifact ID

        Returns:
            The loaded artifact

        Raises:
            ArtifactNotFoundError: If artifact doesn't exist
        """
        ...

    def delete(self, artifact_id: str) -> None:
        """Delete artifact from storage.

        Args:
            artifact_id: The artifact ID

        Raises:
            ArtifactNotFoundError: If artifact doesn't exist
        """
        ...

    def list_by_type(self, artifact_type: str) -> list[ArtifactEnvelope]:
        """List artifacts by type.

        Args:
            artifact_type: The artifact type to filter by

        Returns:
            List of matching artifacts
        """
        ...

    def list_all(self) -> list[ArtifactEnvelope]:
        """List all artifacts.

        Returns:
            List of all artifacts
        """
        ...
```

### ExecutorPort

Interface for plan execution.

```python
# rice_factor/domain/ports/executor.py
from typing import Protocol
from rice_factor.domain.artifacts import ArtifactEnvelope

class ExecutorPort(Protocol):
    """Port for plan execution."""

    def execute(self, artifact: ArtifactEnvelope) -> ExecutionResult:
        """Execute a plan artifact.

        Args:
            artifact: The plan artifact to execute

        Returns:
            Execution result with success/failure info

        Raises:
            ExecutionError: If execution fails
        """
        ...

    def dry_run(self, artifact: ArtifactEnvelope) -> DryRunResult:
        """Preview execution without changes.

        Args:
            artifact: The plan artifact to preview

        Returns:
            Preview of what would happen
        """
        ...

    def rollback(self, execution_id: str) -> None:
        """Rollback a previous execution.

        Args:
            execution_id: The execution to rollback

        Raises:
            RollbackError: If rollback fails
        """
        ...
```

### ValidatorPort

Interface for validation.

```python
# rice_factor/domain/ports/validator.py
from typing import Protocol
from rice_factor.domain.artifacts import ArtifactEnvelope

class ValidatorPort(Protocol):
    """Port for artifact validation."""

    def validate_schema(self, artifact: ArtifactEnvelope) -> ValidationResult:
        """Validate artifact against JSON schema.

        Args:
            artifact: The artifact to validate

        Returns:
            Validation result
        """
        ...

    def validate_dependencies(
        self,
        artifact: ArtifactEnvelope,
        registry: ArtifactRegistry,
    ) -> ValidationResult:
        """Validate artifact dependencies.

        Args:
            artifact: The artifact to validate
            registry: Registry to check dependencies

        Returns:
            Validation result
        """
        ...
```

---

## Services

Services orchestrate domain logic using ports.

### ArtifactService

Manages artifact lifecycle.

```python
# rice_factor/domain/services/artifact_service.py
from rice_factor.domain.ports import StoragePort, ValidatorPort
from rice_factor.domain.artifacts import (
    ArtifactEnvelope,
    ArtifactStatus,
    ArtifactType,
)

class ArtifactService:
    """Service for artifact lifecycle management."""

    def __init__(
        self,
        storage: StoragePort,
        validator: ValidatorPort,
    ):
        self._storage = storage
        self._validator = validator

    def create(
        self,
        artifact_type: ArtifactType,
        payload: dict,
        depends_on: list[str] | None = None,
    ) -> ArtifactEnvelope:
        """Create a new artifact in DRAFT status.

        Args:
            artifact_type: Type of artifact
            payload: Artifact payload
            depends_on: Optional dependency IDs

        Returns:
            Created artifact
        """
        artifact = ArtifactEnvelope(
            id=self._generate_id(),
            artifact_type=artifact_type,
            status=ArtifactStatus.DRAFT,
            payload=payload,
            depends_on=depends_on or [],
        )

        # Validate schema
        result = self._validator.validate_schema(artifact)
        if not result.valid:
            raise ArtifactValidationError(result.errors)

        self._storage.save(artifact)
        return artifact

    def approve(self, artifact_id: str) -> ArtifactEnvelope:
        """Approve a DRAFT artifact.

        Args:
            artifact_id: ID of artifact to approve

        Returns:
            Approved artifact

        Raises:
            ArtifactStatusError: If not in DRAFT status
            ArtifactDependencyError: If dependencies not satisfied
        """
        artifact = self._storage.load(artifact_id)

        if artifact.status != ArtifactStatus.DRAFT:
            raise ArtifactStatusError(
                f"Cannot approve artifact in {artifact.status} status"
            )

        # Validate dependencies
        for dep_id in artifact.depends_on:
            dep = self._storage.load(dep_id)
            if dep.status not in (ArtifactStatus.APPROVED, ArtifactStatus.LOCKED):
                raise ArtifactDependencyError(
                    f"Dependency {dep_id} is not approved"
                )

        artifact.status = ArtifactStatus.APPROVED
        artifact.updated_at = datetime.now(UTC)
        self._storage.save(artifact)

        return artifact

    def lock(self, artifact_id: str) -> ArtifactEnvelope:
        """Lock an APPROVED TestPlan.

        Args:
            artifact_id: ID of TestPlan to lock

        Returns:
            Locked artifact

        Raises:
            ArtifactStatusError: If not TestPlan or not APPROVED
        """
        artifact = self._storage.load(artifact_id)

        if artifact.artifact_type != ArtifactType.TEST_PLAN:
            raise ArtifactStatusError("Only TestPlan can be locked")

        if artifact.status != ArtifactStatus.APPROVED:
            raise ArtifactStatusError("Can only lock APPROVED artifacts")

        artifact.status = ArtifactStatus.LOCKED
        artifact.updated_at = datetime.now(UTC)
        self._storage.save(artifact)

        return artifact

    def load(self, artifact_id: str) -> ArtifactEnvelope:
        """Load an artifact by ID."""
        return self._storage.load(artifact_id)

    def list_by_type(self, artifact_type: ArtifactType) -> list[ArtifactEnvelope]:
        """List artifacts by type."""
        return self._storage.list_by_type(artifact_type.value)
```

### PlanService

Orchestrates plan generation.

```python
# rice_factor/domain/services/plan_service.py
from rice_factor.domain.ports import LLMPort, StoragePort
from rice_factor.domain.artifacts import ArtifactType

class PlanService:
    """Service for plan generation."""

    def __init__(
        self,
        llm: LLMPort,
        storage: StoragePort,
        artifact_service: ArtifactService,
    ):
        self._llm = llm
        self._storage = storage
        self._artifact_service = artifact_service

    def generate_project_plan(
        self,
        requirements: str,
        constraints: str,
    ) -> ArtifactEnvelope:
        """Generate a ProjectPlan from requirements.

        Args:
            requirements: Project requirements text
            constraints: Technical constraints text

        Returns:
            Generated ProjectPlan artifact (DRAFT)
        """
        prompt = self._build_project_plan_prompt(requirements, constraints)
        payload = self._llm.generate_structured(
            prompt=prompt,
            response_model=ProjectPlanPayload,
        )

        return self._artifact_service.create(
            artifact_type=ArtifactType.PROJECT_PLAN,
            payload=payload.model_dump(),
        )

    def generate_test_plan(
        self,
        project_plan_id: str,
        requirements: str,
    ) -> ArtifactEnvelope:
        """Generate a TestPlan from requirements.

        Args:
            project_plan_id: ID of approved ProjectPlan
            requirements: Detailed requirements

        Returns:
            Generated TestPlan artifact (DRAFT)
        """
        project_plan = self._storage.load(project_plan_id)

        prompt = self._build_test_plan_prompt(project_plan, requirements)
        payload = self._llm.generate_structured(
            prompt=prompt,
            response_model=TestPlanPayload,
        )

        return self._artifact_service.create(
            artifact_type=ArtifactType.TEST_PLAN,
            payload=payload.model_dump(),
            depends_on=[project_plan_id],
        )

    def generate_implementation_plan(
        self,
        test_plan_id: str,
        target_file: str,
    ) -> ArtifactEnvelope:
        """Generate an ImplementationPlan.

        Args:
            test_plan_id: ID of locked TestPlan
            target_file: File to implement

        Returns:
            Generated ImplementationPlan artifact (DRAFT)
        """
        test_plan = self._storage.load(test_plan_id)

        if test_plan.status != ArtifactStatus.LOCKED:
            raise ArtifactStatusError("TestPlan must be LOCKED")

        prompt = self._build_impl_plan_prompt(test_plan, target_file)
        payload = self._llm.generate_structured(
            prompt=prompt,
            response_model=ImplementationPlanPayload,
        )

        return self._artifact_service.create(
            artifact_type=ArtifactType.IMPLEMENTATION_PLAN,
            payload=payload.model_dump(),
            depends_on=[test_plan_id],
        )
```

### ExecutorService

Orchestrates plan execution.

```python
# rice_factor/domain/services/executor_service.py
from rice_factor.domain.ports import ExecutorPort, StoragePort

class ExecutorService:
    """Service for plan execution."""

    def __init__(
        self,
        executors: dict[ArtifactType, ExecutorPort],
        storage: StoragePort,
        artifact_service: ArtifactService,
    ):
        self._executors = executors
        self._storage = storage
        self._artifact_service = artifact_service

    def execute(self, artifact_id: str) -> ExecutionResult:
        """Execute an approved plan.

        Args:
            artifact_id: ID of artifact to execute

        Returns:
            Execution result

        Raises:
            ArtifactStatusError: If artifact not approved
        """
        artifact = self._storage.load(artifact_id)

        if artifact.status not in (ArtifactStatus.APPROVED, ArtifactStatus.LOCKED):
            raise ArtifactStatusError("Artifact must be APPROVED or LOCKED")

        executor = self._executors.get(artifact.artifact_type)
        if not executor:
            raise ValueError(f"No executor for {artifact.artifact_type}")

        result = executor.execute(artifact)

        # Create ValidationResult artifact
        self._artifact_service.create(
            artifact_type=ArtifactType.VALIDATION_RESULT,
            payload={
                "target": artifact_id,
                "status": "passed" if result.success else "failed",
                "errors": result.errors,
            },
        )

        return result

    def dry_run(self, artifact_id: str) -> DryRunResult:
        """Preview execution without changes."""
        artifact = self._storage.load(artifact_id)
        executor = self._executors.get(artifact.artifact_type)

        if not executor:
            raise ValueError(f"No executor for {artifact.artifact_type}")

        return executor.dry_run(artifact)
```

---

## Artifact Models

### ArtifactEnvelope

The wrapper for all artifact types.

```python
# rice_factor/domain/artifacts/envelope.py
from datetime import datetime, UTC
from pydantic import BaseModel, Field
from rice_factor.domain.artifacts.enums import (
    ArtifactStatus,
    ArtifactType,
    CreatedBy,
)

class ArtifactEnvelope(BaseModel):
    """Envelope wrapping all artifact types."""

    id: str = Field(..., description="Unique artifact ID")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    artifact_version: str = Field(default="1.0", description="Schema version")
    status: ArtifactStatus = Field(
        default=ArtifactStatus.DRAFT,
        description="Current status"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp"
    )
    created_by: CreatedBy = Field(
        default=CreatedBy.LLM,
        description="Who created this artifact"
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="IDs of dependency artifacts"
    )
    payload: dict = Field(..., description="Artifact-specific payload")

    def approve(self) -> "ArtifactEnvelope":
        """Transition to APPROVED status."""
        if self.status != ArtifactStatus.DRAFT:
            raise ArtifactStatusError("Can only approve DRAFT artifacts")
        self.status = ArtifactStatus.APPROVED
        self.updated_at = datetime.now(UTC)
        return self

    def lock(self) -> "ArtifactEnvelope":
        """Transition to LOCKED status (TestPlan only)."""
        if self.artifact_type != ArtifactType.TEST_PLAN:
            raise ArtifactStatusError("Only TestPlan can be locked")
        if self.status != ArtifactStatus.APPROVED:
            raise ArtifactStatusError("Can only lock APPROVED artifacts")
        self.status = ArtifactStatus.LOCKED
        self.updated_at = datetime.now(UTC)
        return self
```

### Payload Types

```python
# rice_factor/domain/artifacts/payloads.py
from pydantic import BaseModel, Field

class Domain(BaseModel):
    """Domain definition."""
    name: str
    responsibility: str

class Module(BaseModel):
    """Module definition."""
    name: str
    domain: str

class Constraints(BaseModel):
    """Architecture constraints."""
    architecture: str  # CLEAN, HEXAGONAL, DDD, CUSTOM
    languages: list[str]

class ProjectPlanPayload(BaseModel):
    """ProjectPlan payload."""
    domains: list[Domain] = Field(min_length=1)
    modules: list[Module] = Field(min_length=1)
    constraints: Constraints
    polyglot: dict | None = None

class TestDefinition(BaseModel):
    """Single test definition."""
    id: str
    target: str
    assertions: list[str] = Field(min_length=1)

class TestPlanPayload(BaseModel):
    """TestPlan payload."""
    tests: list[TestDefinition] = Field(min_length=1)

class ImplementationPlanPayload(BaseModel):
    """ImplementationPlan payload."""
    target: str
    steps: list[str] = Field(min_length=1)
    related_tests: list[str]

# ... other payload types
```

### Enums

```python
# rice_factor/domain/artifacts/enums.py
from enum import Enum

class ArtifactStatus(str, Enum):
    """Artifact lifecycle status."""
    DRAFT = "draft"
    APPROVED = "approved"
    LOCKED = "locked"

class ArtifactType(str, Enum):
    """Types of artifacts."""
    PROJECT_PLAN = "ProjectPlan"
    ARCHITECTURE_PLAN = "ArchitecturePlan"
    SCAFFOLD_PLAN = "ScaffoldPlan"
    TEST_PLAN = "TestPlan"
    IMPLEMENTATION_PLAN = "ImplementationPlan"
    REFACTOR_PLAN = "RefactorPlan"
    VALIDATION_RESULT = "ValidationResult"
    FAILURE_REPORT = "FailureReport"
    RECONCILIATION_PLAN = "ReconciliationPlan"

class CreatedBy(str, Enum):
    """Who created the artifact."""
    HUMAN = "human"
    LLM = "llm"
    SYSTEM = "system"
```

---

## Failure Models

```python
# rice_factor/domain/failures/models.py
from pydantic import BaseModel
from enum import Enum

class FailureCategory(str, Enum):
    """Categories of failures."""
    MISSING_INFORMATION = "MISSING_INFORMATION"
    INVALID_REQUEST = "INVALID_REQUEST"
    API_ERROR = "API_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

class RecoveryAction(str, Enum):
    """Suggested recovery actions."""
    HUMAN_INPUT_REQUIRED = "HUMAN_INPUT_REQUIRED"
    RETRY = "RETRY"
    RETRY_AFTER_DELAY = "RETRY_AFTER_DELAY"
    ABORT = "ABORT"
    FIX_AND_RETRY = "FIX_AND_RETRY"

class FailureReport(BaseModel):
    """Structured failure information."""
    phase: str
    artifact_id: str | None
    category: FailureCategory
    summary: str
    details: dict
    blocking: bool
    recovery_action: RecoveryAction
    timestamp: datetime
    raw_response: str | None = None
```

---

## Exceptions

```python
# rice_factor/domain/exceptions.py

class RiceFactorError(Exception):
    """Base exception for Rice-Factor."""
    pass

class ArtifactError(RiceFactorError):
    """Base artifact exception."""
    pass

class ArtifactNotFoundError(ArtifactError):
    """Artifact not found."""
    pass

class ArtifactStatusError(ArtifactError):
    """Invalid status transition."""
    pass

class ArtifactValidationError(ArtifactError):
    """Artifact validation failed."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {errors}")

class ArtifactDependencyError(ArtifactError):
    """Dependency not satisfied."""
    pass

class ExecutionError(RiceFactorError):
    """Execution failed."""
    pass

class RollbackError(RiceFactorError):
    """Rollback failed."""
    pass
```

---

## See Also

- [Architecture Overview](overview.md) - Hexagonal architecture
- [Adapters](adapters.md) - Port implementations
- [Artifact Schemas](../artifacts/schemas.md) - JSON schemas
