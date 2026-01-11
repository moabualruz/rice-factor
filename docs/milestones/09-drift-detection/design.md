# Milestone 09: Drift Detection & Reconciliation - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

### 1.1 Architecture Approach

Drift detection follows the hexagonal architecture pattern with a domain service that compares the current codebase state against artifact coverage.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│   rice-factor audit drift    │    rice-factor reconcile     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Services                         │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ DriftDetector   │───▶│ ReconciliationPlanGenerator     │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
│           │                            │                     │
│           ▼                            ▼                     │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │ DriftSignal     │    │ ReconciliationPlan              │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Adapters                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ FileScanner  │  │ArtifactStore │  │  AuditReader     │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 File Organization

```
rice_factor/
├── domain/
│   ├── artifacts/
│   │   └── reconciliation_plan.py    # ReconciliationPlan model
│   ├── services/
│   │   ├── drift_detector.py         # Drift detection logic
│   │   └── reconciliation_service.py # Plan generation
│   └── models/
│       └── drift.py                  # DriftSignal, DriftReport
├── adapters/
│   └── drift/
│       └── file_scanner_adapter.py   # File system scanning
├── entrypoints/
│   └── cli/
│       └── commands/
│           └── audit.py              # audit drift command
└── config/
    └── drift_config.py               # Threshold configuration

schemas/
└── reconciliation_plan.schema.json   # JSON Schema
```

---

## 2. Domain Models

### 2.1 Drift Signal Types

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class DriftSignalType(str, Enum):
    """Types of drift signals detected."""

    ORPHAN_CODE = "orphan_code"           # Code with no plan
    ORPHAN_PLAN = "orphan_plan"           # Plan with no code
    UNDOCUMENTED_BEHAVIOR = "undocumented_behavior"  # Tests for unlisted behavior
    REFACTOR_HOTSPOT = "refactor_hotspot" # Frequently refactored area


class DriftSeverity(str, Enum):
    """Severity levels for drift signals."""

    LOW = "low"         # Informational
    MEDIUM = "medium"   # Should address
    HIGH = "high"       # Blocks new work
    CRITICAL = "critical"  # Requires immediate action


@dataclass
class DriftSignal:
    """A detected instance of drift."""

    signal_type: DriftSignalType
    severity: DriftSeverity
    path: str                    # File or artifact path
    description: str             # Human-readable explanation
    detected_at: datetime
    related_artifact_id: str | None = None
    suggested_action: str | None = None

    def to_dict(self) -> dict:
        return {
            "signal_type": self.signal_type.value,
            "severity": self.severity.value,
            "path": self.path,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "related_artifact_id": self.related_artifact_id,
            "suggested_action": self.suggested_action,
        }
```

### 2.2 Drift Report

```python
@dataclass
class DriftReport:
    """Complete drift analysis report."""

    signals: list[DriftSignal]
    analyzed_at: datetime
    threshold: int
    code_files_scanned: int
    artifacts_checked: int

    @property
    def signal_count(self) -> int:
        return len(self.signals)

    @property
    def exceeds_threshold(self) -> bool:
        return self.signal_count >= self.threshold

    @property
    def requires_reconciliation(self) -> bool:
        # Requires reconciliation if threshold exceeded
        # OR if any critical signals exist
        has_critical = any(
            s.severity == DriftSeverity.CRITICAL
            for s in self.signals
        )
        return self.exceeds_threshold or has_critical

    def by_type(self, signal_type: DriftSignalType) -> list[DriftSignal]:
        return [s for s in self.signals if s.signal_type == signal_type]

    def to_dict(self) -> dict:
        return {
            "analyzed_at": self.analyzed_at.isoformat(),
            "threshold": self.threshold,
            "code_files_scanned": self.code_files_scanned,
            "artifacts_checked": self.artifacts_checked,
            "signal_count": self.signal_count,
            "exceeds_threshold": self.exceeds_threshold,
            "requires_reconciliation": self.requires_reconciliation,
            "signals": [s.to_dict() for s in self.signals],
        }
```

### 2.3 ReconciliationPlan Artifact

```python
from rice_factor.domain.artifacts.base import ArtifactEnvelope


class ReconciliationAction(str, Enum):
    """Actions in a reconciliation plan."""

    UPDATE_ARTIFACT = "update_artifact"
    ARCHIVE_ARTIFACT = "archive_artifact"
    CREATE_ARTIFACT = "create_artifact"
    UPDATE_REQUIREMENTS = "update_requirements"
    REVIEW_CODE = "review_code"
    DELETE_CODE = "delete_code"


@dataclass
class ReconciliationStep:
    """A single step in the reconciliation plan."""

    action: ReconciliationAction
    target: str                  # File path or artifact ID
    reason: str                  # Why this step is needed
    drift_signal_id: str         # Reference to originating signal
    priority: int                # Execution order (1 = first)

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "target": self.target,
            "reason": self.reason,
            "drift_signal_id": self.drift_signal_id,
            "priority": self.priority,
        }


@dataclass
class ReconciliationPlanPayload:
    """Payload for ReconciliationPlan artifact."""

    drift_report_id: str
    steps: list[ReconciliationStep]
    freeze_new_work: bool = True

    def to_dict(self) -> dict:
        return {
            "drift_report_id": self.drift_report_id,
            "steps": [s.to_dict() for s in self.steps],
            "freeze_new_work": self.freeze_new_work,
        }
```

---

## 3. Drift Detection Service

### 3.1 Service Interface

```python
from abc import ABC, abstractmethod
from pathlib import Path


class DriftDetectorPort(ABC):
    """Port for drift detection operations."""

    @abstractmethod
    def detect_orphan_code(self, code_dir: Path) -> list[DriftSignal]:
        """Find code files not covered by any plan."""
        ...

    @abstractmethod
    def detect_orphan_plans(self) -> list[DriftSignal]:
        """Find plans targeting non-existent code."""
        ...

    @abstractmethod
    def detect_undocumented_behavior(self) -> list[DriftSignal]:
        """Find tests covering behavior not in requirements."""
        ...

    @abstractmethod
    def detect_refactor_hotspots(self, threshold: int = 3) -> list[DriftSignal]:
        """Find frequently refactored areas."""
        ...

    @abstractmethod
    def full_analysis(self, code_dir: Path) -> DriftReport:
        """Run complete drift analysis."""
        ...
```

### 3.2 Implementation

```python
class DriftDetector:
    """Detects drift between code and artifacts."""

    def __init__(
        self,
        artifact_store: StoragePort,
        audit_reader: AuditReaderPort,
        config: DriftConfig,
    ) -> None:
        self.artifact_store = artifact_store
        self.audit_reader = audit_reader
        self.config = config

    def detect_orphan_code(self, code_dir: Path) -> list[DriftSignal]:
        """Find code files not covered by any ImplementationPlan."""
        signals = []

        # Get all code files
        code_files = self._scan_code_files(code_dir)

        # Get all file paths covered by ImplementationPlans
        covered_paths = self._get_covered_paths()

        # Find orphans
        for code_file in code_files:
            rel_path = code_file.relative_to(code_dir)
            if str(rel_path) not in covered_paths:
                signals.append(DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.MEDIUM,
                    path=str(rel_path),
                    description=f"No ImplementationPlan covers {rel_path}",
                    detected_at=datetime.now(),
                    suggested_action="Create ImplementationPlan or document as legacy",
                ))

        return signals

    def detect_orphan_plans(self) -> list[DriftSignal]:
        """Find ImplementationPlans targeting non-existent files."""
        signals = []

        impl_plans = self.artifact_store.list_by_type("ImplementationPlan")

        for plan in impl_plans:
            target_file = plan.payload.get("target_file")
            if target_file and not Path(target_file).exists():
                signals.append(DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_PLAN,
                    severity=DriftSeverity.HIGH,
                    path=target_file,
                    description=f"Plan {plan.id} targets non-existent {target_file}",
                    detected_at=datetime.now(),
                    related_artifact_id=plan.id,
                    suggested_action="Archive plan or restore target file",
                ))

        return signals

    def detect_refactor_hotspots(
        self,
        threshold: int = 3,
        days: int = 30,
    ) -> list[DriftSignal]:
        """Find files refactored frequently in recent period."""
        signals = []

        # Get refactor history from audit log
        refactor_counts = self.audit_reader.count_refactors_by_path(days=days)

        for path, count in refactor_counts.items():
            if count >= threshold:
                signals.append(DriftSignal(
                    signal_type=DriftSignalType.REFACTOR_HOTSPOT,
                    severity=DriftSeverity.MEDIUM,
                    path=path,
                    description=f"{path} refactored {count} times in {days} days",
                    detected_at=datetime.now(),
                    suggested_action="Review for architectural issues",
                ))

        return signals

    def full_analysis(self, code_dir: Path) -> DriftReport:
        """Run complete drift analysis."""
        signals = []

        signals.extend(self.detect_orphan_code(code_dir))
        signals.extend(self.detect_orphan_plans())
        signals.extend(self.detect_undocumented_behavior())
        signals.extend(self.detect_refactor_hotspots())

        return DriftReport(
            signals=signals,
            analyzed_at=datetime.now(),
            threshold=self.config.drift_threshold,
            code_files_scanned=len(self._scan_code_files(code_dir)),
            artifacts_checked=len(self.artifact_store.list_all()),
        )

    def _scan_code_files(self, code_dir: Path) -> list[Path]:
        """Scan directory for code files."""
        patterns = self.config.code_patterns  # e.g., ["*.py", "*.ts"]
        ignore = self.config.ignore_patterns  # e.g., ["*_test.py", "__pycache__"]

        files = []
        for pattern in patterns:
            for path in code_dir.rglob(pattern):
                if not any(path.match(ig) for ig in ignore):
                    files.append(path)
        return files

    def _get_covered_paths(self) -> set[str]:
        """Get all file paths covered by ImplementationPlans."""
        covered = set()
        impl_plans = self.artifact_store.list_by_type("ImplementationPlan")
        for plan in impl_plans:
            if target := plan.payload.get("target_file"):
                covered.add(target)
        return covered
```

---

## 4. Reconciliation Service

### 4.1 Plan Generator

```python
class ReconciliationService:
    """Generates reconciliation plans from drift reports."""

    def __init__(
        self,
        artifact_service: ArtifactService,
        llm_port: LLMPort | None = None,
    ) -> None:
        self.artifact_service = artifact_service
        self.llm_port = llm_port

    def generate_plan(self, drift_report: DriftReport) -> ArtifactEnvelope:
        """Generate ReconciliationPlan from drift report."""
        steps = []
        priority = 1

        for signal in drift_report.signals:
            step = self._signal_to_step(signal, priority)
            if step:
                steps.append(step)
                priority += 1

        payload = ReconciliationPlanPayload(
            drift_report_id=str(uuid.uuid4()),  # Reference to report
            steps=steps,
            freeze_new_work=drift_report.requires_reconciliation,
        )

        return self.artifact_service.create(
            artifact_type="ReconciliationPlan",
            payload=payload.to_dict(),
        )

    def _signal_to_step(
        self,
        signal: DriftSignal,
        priority: int,
    ) -> ReconciliationStep | None:
        """Convert drift signal to reconciliation step."""
        action_map = {
            DriftSignalType.ORPHAN_CODE: ReconciliationAction.CREATE_ARTIFACT,
            DriftSignalType.ORPHAN_PLAN: ReconciliationAction.ARCHIVE_ARTIFACT,
            DriftSignalType.UNDOCUMENTED_BEHAVIOR: ReconciliationAction.UPDATE_REQUIREMENTS,
            DriftSignalType.REFACTOR_HOTSPOT: ReconciliationAction.REVIEW_CODE,
        }

        action = action_map.get(signal.signal_type)
        if not action:
            return None

        return ReconciliationStep(
            action=action,
            target=signal.path,
            reason=signal.description,
            drift_signal_id=str(uuid.uuid4()),
            priority=priority,
        )
```

---

## 5. CLI Commands

### 5.1 Audit Drift Command

```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()


@app.command("drift")
def audit_drift(
    code_dir: Path = typer.Option(Path("src"), help="Code directory to scan"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Detect drift between code and artifacts."""
    detector = container.get(DriftDetector)
    report = detector.full_analysis(code_dir)

    if json_output:
        console.print_json(data=report.to_dict())
        return

    # Pretty print
    console.print("\n[bold]Drift Analysis Report[/bold]")
    console.print("=" * 40)

    for signal_type in DriftSignalType:
        signals = report.by_type(signal_type)
        if signals:
            console.print(f"\n[yellow]{signal_type.value}:[/yellow]")
            for signal in signals:
                console.print(f"  - {signal.path}")
                console.print(f"    {signal.description}")

    console.print(f"\n[bold]Summary:[/bold] {report.signal_count} signals detected")
    console.print(f"Threshold: {report.threshold}")

    if report.requires_reconciliation:
        console.print("\n[red bold]Status: RECONCILIATION REQUIRED[/red bold]")
        console.print("Run 'rice-factor reconcile' to generate plan.")
        raise typer.Exit(1)
    else:
        console.print("\n[green]Status: OK[/green]")
```

### 5.2 Reconcile Command

```python
@app.command("reconcile")
def reconcile(
    auto_approve: bool = typer.Option(False, help="Skip approval step"),
) -> None:
    """Generate reconciliation plan for detected drift."""
    detector = container.get(DriftDetector)
    reconciliation_service = container.get(ReconciliationService)

    # Run drift analysis
    report = detector.full_analysis(Path("src"))

    if not report.signals:
        console.print("[green]No drift detected. Nothing to reconcile.[/green]")
        return

    # Generate plan
    console.print("\nGenerating ReconciliationPlan...")
    plan = reconciliation_service.generate_plan(report)

    # Display plan
    console.print("\n[bold]Recommended Actions:[/bold]")
    for i, step in enumerate(plan.payload["steps"], 1):
        console.print(f"\n{i}. [cyan]{step['action']}[/cyan] {step['target']}")
        console.print(f"   Reason: {step['reason']}")

    console.print(f"\nPlan saved to: artifacts/{plan.id}.json")

    if not auto_approve:
        console.print("\nHuman review required.")
        console.print("Run 'rice-factor approve reconciliation' after review.")
```

---

## 6. Configuration

### 6.1 Drift Configuration

```python
from dataclasses import dataclass, field


@dataclass
class DriftConfig:
    """Configuration for drift detection."""

    # Threshold for requiring reconciliation
    drift_threshold: int = 3

    # Code file patterns to scan
    code_patterns: list[str] = field(default_factory=lambda: [
        "*.py", "*.ts", "*.js", "*.go", "*.rs", "*.java",
    ])

    # Patterns to ignore
    ignore_patterns: list[str] = field(default_factory=lambda: [
        "*_test.py", "test_*.py", "__pycache__/*", "node_modules/*",
        "*.pyc", ".git/*",
    ])

    # Refactor hotspot threshold
    refactor_threshold: int = 3
    refactor_window_days: int = 30

    @classmethod
    def from_file(cls, path: Path) -> "DriftConfig":
        """Load config from YAML file."""
        if not path.exists():
            return cls()

        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(**data.get("drift", {}))
```

### 6.2 Configuration File Format

```yaml
# .project/config.yaml
drift:
  drift_threshold: 5
  refactor_threshold: 4
  refactor_window_days: 60
  code_patterns:
    - "*.py"
    - "*.ts"
  ignore_patterns:
    - "*_test.py"
    - "migrations/*"
```

---

## 7. JSON Schema

### 7.1 ReconciliationPlan Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "reconciliation_plan.schema.json",
  "title": "ReconciliationPlan",
  "type": "object",
  "required": ["drift_report_id", "steps", "freeze_new_work"],
  "properties": {
    "drift_report_id": {
      "type": "string",
      "format": "uuid"
    },
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["action", "target", "reason", "priority"],
        "properties": {
          "action": {
            "type": "string",
            "enum": [
              "update_artifact",
              "archive_artifact",
              "create_artifact",
              "update_requirements",
              "review_code",
              "delete_code"
            ]
          },
          "target": { "type": "string" },
          "reason": { "type": "string" },
          "drift_signal_id": { "type": "string" },
          "priority": { "type": "integer", "minimum": 1 }
        }
      }
    },
    "freeze_new_work": {
      "type": "boolean",
      "default": true
    }
  }
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial design |
