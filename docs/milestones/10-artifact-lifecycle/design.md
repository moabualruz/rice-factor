# Milestone 10: Artifact Lifecycle Management - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

### 1.1 Architecture Approach

Artifact lifecycle management extends the existing artifact system with age tracking, policy evaluation, and review triggers.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  artifact age  │  validate arch  │  audit coverage          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Services                         │
│                                                              │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ LifecycleService│  │ ArchValidator   │  │ CoverageMon  │  │
│  └────────────────┘  └─────────────────┘  └──────────────┘  │
│           │                   │                   │          │
│           ▼                   ▼                   ▼          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              ArtifactEnvelope (extended)                │ │
│  │  + created_at, updated_at, last_reviewed_at            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Configuration                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              LifecyclePolicy (per artifact type)     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 File Organization

```
rice_factor/
├── domain/
│   ├── artifacts/
│   │   └── base.py                    # Extended with timestamps
│   ├── services/
│   │   ├── lifecycle_service.py       # Age tracking & policies
│   │   ├── architecture_validator.py  # Arch violation detection
│   │   └── coverage_monitor.py        # Test coverage tracking
│   └── models/
│       └── lifecycle.py               # AgeStatus, PolicyResult
├── adapters/
│   └── lifecycle/
│       └── coverage_adapter.py        # Coverage tool integration
├── entrypoints/
│   └── cli/
│       └── commands/
│           └── artifact.py            # artifact age command
└── config/
    └── lifecycle_config.py            # Policy configuration
```

---

## 2. Domain Models

### 2.1 Artifact Timestamps

Extend `ArtifactEnvelope` with lifecycle metadata:

```python
from datetime import datetime


@dataclass
class ArtifactEnvelope:
    """Extended artifact envelope with lifecycle tracking."""

    # Existing fields
    id: str
    artifact_type: str
    status: ArtifactStatus
    payload: dict

    # Lifecycle fields (new)
    created_at: datetime
    updated_at: datetime
    last_reviewed_at: datetime | None = None
    review_notes: str | None = None

    @property
    def age_days(self) -> int:
        """Calculate artifact age in days."""
        return (datetime.now() - self.created_at).days

    @property
    def age_months(self) -> float:
        """Calculate artifact age in months (approximate)."""
        return self.age_days / 30.44  # Average days per month

    @property
    def days_since_review(self) -> int | None:
        """Days since last review, or None if never reviewed."""
        if self.last_reviewed_at is None:
            return None
        return (datetime.now() - self.last_reviewed_at).days
```

### 2.2 Lifecycle Policy

```python
from dataclasses import dataclass
from enum import Enum


class ReviewTrigger(str, Enum):
    """What triggers a review requirement."""

    AGE = "age"                    # Time-based
    VIOLATION = "violation"        # Rule violation
    DRIFT = "drift"               # Coverage/content drift
    MANUAL = "manual"             # User-initiated


class ReviewUrgency(str, Enum):
    """How urgent is the review."""

    INFORMATIONAL = "informational"  # FYI, no action required
    RECOMMENDED = "recommended"       # Should review soon
    REQUIRED = "required"            # Must review before proceeding
    MANDATORY = "mandatory"          # Blocks all work until reviewed


@dataclass
class LifecyclePolicy:
    """Policy for artifact lifecycle management."""

    artifact_type: str

    # Age-based review
    review_after_months: int = 3
    warning_at_months: int | None = None  # None = 1 month before review

    # Violation handling
    mandatory_on_violation: bool = False

    # Coverage drift (for TestPlan)
    coverage_drift_threshold: float | None = None  # Percent

    def evaluate(
        self,
        artifact: ArtifactEnvelope,
        violations: list | None = None,
        coverage_drift: float | None = None,
    ) -> "PolicyResult":
        """Evaluate artifact against this policy."""
        triggers = []
        urgency = ReviewUrgency.INFORMATIONAL

        # Check age
        if artifact.age_months >= self.review_after_months:
            triggers.append(ReviewTrigger.AGE)
            urgency = ReviewUrgency.REQUIRED

        elif self._in_warning_period(artifact):
            triggers.append(ReviewTrigger.AGE)
            urgency = ReviewUrgency.RECOMMENDED

        # Check violations
        if violations and self.mandatory_on_violation:
            triggers.append(ReviewTrigger.VIOLATION)
            urgency = ReviewUrgency.MANDATORY

        # Check coverage drift
        if (
            coverage_drift is not None
            and self.coverage_drift_threshold is not None
            and coverage_drift >= self.coverage_drift_threshold
        ):
            triggers.append(ReviewTrigger.DRIFT)
            if urgency != ReviewUrgency.MANDATORY:
                urgency = ReviewUrgency.REQUIRED

        return PolicyResult(
            artifact_id=artifact.id,
            artifact_type=artifact.artifact_type,
            triggers=triggers,
            urgency=urgency,
            age_months=artifact.age_months,
            violations=violations or [],
            coverage_drift=coverage_drift,
        )

    def _in_warning_period(self, artifact: ArtifactEnvelope) -> bool:
        warning = self.warning_at_months or (self.review_after_months - 1)
        return warning <= artifact.age_months < self.review_after_months


@dataclass
class PolicyResult:
    """Result of policy evaluation."""

    artifact_id: str
    artifact_type: str
    triggers: list[ReviewTrigger]
    urgency: ReviewUrgency
    age_months: float
    violations: list
    coverage_drift: float | None

    @property
    def requires_action(self) -> bool:
        return self.urgency in (ReviewUrgency.REQUIRED, ReviewUrgency.MANDATORY)

    @property
    def blocks_work(self) -> bool:
        return self.urgency == ReviewUrgency.MANDATORY
```

---

## 3. Lifecycle Service

### 3.1 Service Implementation

```python
class LifecycleService:
    """Manages artifact lifecycle and policy evaluation."""

    def __init__(
        self,
        artifact_store: StoragePort,
        policies: dict[str, LifecyclePolicy],
        arch_validator: ArchitectureValidatorPort | None = None,
        coverage_monitor: CoverageMonitorPort | None = None,
    ) -> None:
        self.artifact_store = artifact_store
        self.policies = policies
        self.arch_validator = arch_validator
        self.coverage_monitor = coverage_monitor

    def evaluate_all(self) -> list[PolicyResult]:
        """Evaluate all artifacts against their policies."""
        results = []

        for artifact in self.artifact_store.list_all():
            policy = self.policies.get(artifact.artifact_type)
            if policy is None:
                continue

            # Get violations for ArchitecturePlan
            violations = None
            if artifact.artifact_type == "ArchitecturePlan" and self.arch_validator:
                violations = self.arch_validator.check_violations(artifact)

            # Get coverage drift for TestPlan
            coverage_drift = None
            if artifact.artifact_type == "TestPlan" and self.coverage_monitor:
                coverage_drift = self.coverage_monitor.calculate_drift(artifact)

            result = policy.evaluate(artifact, violations, coverage_drift)
            results.append(result)

        return results

    def get_blocking_issues(self) -> list[PolicyResult]:
        """Get issues that block further work."""
        return [r for r in self.evaluate_all() if r.blocks_work]

    def record_review(
        self,
        artifact_id: str,
        notes: str | None = None,
    ) -> None:
        """Record that an artifact was reviewed."""
        artifact = self.artifact_store.load(artifact_id)
        artifact.last_reviewed_at = datetime.now()
        artifact.review_notes = notes
        self.artifact_store.save(artifact)

    def generate_age_report(self) -> "AgeReport":
        """Generate comprehensive age report."""
        results = self.evaluate_all()

        return AgeReport(
            generated_at=datetime.now(),
            total_artifacts=len(results),
            requiring_action=[r for r in results if r.requires_action],
            blocking=[r for r in results if r.blocks_work],
            healthy=[r for r in results if not r.requires_action],
        )


@dataclass
class AgeReport:
    """Report on artifact ages and policy status."""

    generated_at: datetime
    total_artifacts: int
    requiring_action: list[PolicyResult]
    blocking: list[PolicyResult]
    healthy: list[PolicyResult]

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "total_artifacts": self.total_artifacts,
            "requiring_action_count": len(self.requiring_action),
            "blocking_count": len(self.blocking),
            "healthy_count": len(self.healthy),
        }
```

---

## 4. Architecture Validator

### 4.1 Port Definition

```python
from abc import ABC, abstractmethod


@dataclass
class ArchitectureViolation:
    """A detected architecture violation."""

    rule_name: str
    description: str
    source_file: str
    target_file: str | None
    severity: str  # error, warning


class ArchitectureValidatorPort(ABC):
    """Port for architecture validation."""

    @abstractmethod
    def check_violations(
        self,
        arch_plan: ArtifactEnvelope,
    ) -> list[ArchitectureViolation]:
        """Check code against architecture rules."""
        ...

    @abstractmethod
    def get_rules(
        self,
        arch_plan: ArtifactEnvelope,
    ) -> list[str]:
        """Get list of architecture rules from plan."""
        ...
```

### 4.2 Adapter Implementation

```python
class ArchitectureValidatorAdapter:
    """Validates code against ArchitecturePlan rules."""

    def check_violations(
        self,
        arch_plan: ArtifactEnvelope,
    ) -> list[ArchitectureViolation]:
        violations = []

        rules = self._parse_rules(arch_plan.payload)

        for rule in rules:
            rule_violations = self._check_rule(rule)
            violations.extend(rule_violations)

        return violations

    def _parse_rules(self, payload: dict) -> list[dict]:
        """Extract architecture rules from plan payload."""
        return payload.get("layer_rules", []) + payload.get("dependency_rules", [])

    def _check_rule(self, rule: dict) -> list[ArchitectureViolation]:
        """Check a single architecture rule."""
        violations = []

        if rule["type"] == "layer_boundary":
            violations.extend(self._check_layer_boundary(rule))
        elif rule["type"] == "no_external_deps":
            violations.extend(self._check_no_external_deps(rule))

        return violations

    def _check_layer_boundary(self, rule: dict) -> list[ArchitectureViolation]:
        """Check layer boundary violations."""
        source_layer = rule["source"]
        forbidden_targets = rule["cannot_import"]

        violations = []

        # Scan source files for forbidden imports
        for source_file in self._get_files_in_layer(source_layer):
            imports = self._get_imports(source_file)
            for imp in imports:
                for forbidden in forbidden_targets:
                    if imp.startswith(forbidden):
                        violations.append(ArchitectureViolation(
                            rule_name=f"{source_layer}_boundary",
                            description=f"{source_layer} cannot import from {forbidden}",
                            source_file=str(source_file),
                            target_file=imp,
                            severity="error",
                        ))

        return violations
```

---

## 5. Coverage Monitor

### 5.1 Port Definition

```python
class CoverageMonitorPort(ABC):
    """Port for test coverage monitoring."""

    @abstractmethod
    def get_current_coverage(self) -> float:
        """Get current test coverage percentage."""
        ...

    @abstractmethod
    def get_baseline_coverage(
        self,
        test_plan: ArtifactEnvelope,
    ) -> float:
        """Get baseline coverage from TestPlan."""
        ...

    @abstractmethod
    def calculate_drift(
        self,
        test_plan: ArtifactEnvelope,
    ) -> float:
        """Calculate coverage drift (baseline - current)."""
        ...
```

### 5.2 Adapter Implementation

```python
import subprocess
import json


class CoverageMonitorAdapter:
    """Monitors test coverage drift."""

    def get_current_coverage(self) -> float:
        """Get current coverage by running tests."""
        result = subprocess.run(
            ["pytest", "--cov", "--cov-report=json", "-q"],
            capture_output=True,
            text=True,
        )

        with open("coverage.json") as f:
            data = json.load(f)

        return data["totals"]["percent_covered"]

    def get_baseline_coverage(
        self,
        test_plan: ArtifactEnvelope,
    ) -> float:
        """Get baseline from TestPlan metadata."""
        return test_plan.payload.get("baseline_coverage", 0.0)

    def calculate_drift(
        self,
        test_plan: ArtifactEnvelope,
    ) -> float:
        """Calculate how much coverage has drifted."""
        baseline = self.get_baseline_coverage(test_plan)
        current = self.get_current_coverage()

        # Positive drift means coverage decreased
        return baseline - current
```

---

## 6. CLI Commands

### 6.1 Artifact Age Command

```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()


@app.command("age")
def artifact_age(
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show artifact age and lifecycle status."""
    lifecycle_service = container.get(LifecycleService)
    report = lifecycle_service.generate_age_report()

    if json_output:
        console.print_json(data=report.to_dict())
        return

    console.print("\n[bold]Artifact Age Report[/bold]")
    console.print("=" * 40)

    # Show blocking issues first
    if report.blocking:
        console.print("\n[red bold]BLOCKING ISSUES[/red bold]")
        for result in report.blocking:
            _print_result(result)

    # Show requiring action
    if report.requiring_action:
        console.print("\n[yellow]Requiring Action[/yellow]")
        for result in report.requiring_action:
            if result not in report.blocking:
                _print_result(result)

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total: {report.total_artifacts}")
    console.print(f"  Healthy: {len(report.healthy)}")
    console.print(f"  Requiring Action: {len(report.requiring_action)}")
    console.print(f"  Blocking: {len(report.blocking)}")

    if report.blocking:
        raise typer.Exit(2)
    elif report.requiring_action:
        raise typer.Exit(1)


def _print_result(result: PolicyResult) -> None:
    console.print(f"\n  {result.artifact_type} ({result.artifact_id}):")
    console.print(f"    Age: {result.age_months:.1f} months")
    console.print(f"    Urgency: {result.urgency.value}")

    for trigger in result.triggers:
        console.print(f"    Trigger: {trigger.value}")

    if result.violations:
        console.print(f"    Violations: {len(result.violations)}")

    if result.coverage_drift is not None:
        console.print(f"    Coverage Drift: {result.coverage_drift:.1f}%")
```

---

## 7. Configuration

### 7.1 Policy Configuration

```python
@dataclass
class LifecycleConfig:
    """Configuration for artifact lifecycle management."""

    policies: dict[str, LifecyclePolicy] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> "LifecycleConfig":
        """Load from YAML config file."""
        if not path.exists():
            return cls.default()

        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)

        lifecycle_data = data.get("lifecycle", {})
        policies_data = lifecycle_data.get("policies", {})

        policies = {}
        for artifact_type, policy_data in policies_data.items():
            policies[artifact_type] = LifecyclePolicy(
                artifact_type=artifact_type,
                **policy_data,
            )

        return cls(policies=policies)

    @classmethod
    def default(cls) -> "LifecycleConfig":
        """Default lifecycle policies."""
        return cls(policies={
            "ProjectPlan": LifecyclePolicy(
                artifact_type="ProjectPlan",
                review_after_months=3,
            ),
            "ArchitecturePlan": LifecyclePolicy(
                artifact_type="ArchitecturePlan",
                review_after_months=6,
                mandatory_on_violation=True,
            ),
            "TestPlan": LifecyclePolicy(
                artifact_type="TestPlan",
                review_after_months=3,
                coverage_drift_threshold=10.0,
            ),
        })
```

### 7.2 YAML Format

```yaml
# .project/config.yaml
lifecycle:
  policies:
    ProjectPlan:
      review_after_months: 3
      warning_at_months: 2

    ArchitecturePlan:
      review_after_months: 6
      mandatory_on_violation: true

    TestPlan:
      review_after_months: 3
      coverage_drift_threshold: 10

    ImplementationPlan:
      review_after_months: 6
      warning_at_months: 5
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial design |
