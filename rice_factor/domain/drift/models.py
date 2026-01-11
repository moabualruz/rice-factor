"""Drift detection domain models.

This module provides data models for drift detection between code and artifacts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class DriftSignalType(str, Enum):
    """Types of drift signals detected."""

    ORPHAN_CODE = "orphan_code"  # Code with no plan
    ORPHAN_PLAN = "orphan_plan"  # Plan with no code
    UNDOCUMENTED_BEHAVIOR = "undocumented_behavior"  # Tests for unlisted behavior
    REFACTOR_HOTSPOT = "refactor_hotspot"  # Frequently refactored area


class DriftSeverity(str, Enum):
    """Severity levels for drift signals."""

    LOW = "low"  # Informational
    MEDIUM = "medium"  # Should address
    HIGH = "high"  # Blocks new work
    CRITICAL = "critical"  # Requires immediate action


@dataclass(frozen=True)
class DriftSignal:
    """A detected instance of drift.

    Attributes:
        signal_type: The type of drift detected.
        severity: The severity level of this signal.
        path: File or artifact path related to the signal.
        description: Human-readable explanation.
        detected_at: When the signal was detected.
        related_artifact_id: ID of related artifact (if applicable).
        suggested_action: Guidance on how to address the drift.
    """

    signal_type: DriftSignalType
    severity: DriftSeverity
    path: str
    description: str
    detected_at: datetime
    related_artifact_id: str | None = None
    suggested_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "signal_type": self.signal_type.value,
            "severity": self.severity.value,
            "path": self.path,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "related_artifact_id": self.related_artifact_id,
            "suggested_action": self.suggested_action,
        }


@dataclass
class DriftReport:
    """Complete drift analysis report.

    Attributes:
        signals: List of detected drift signals.
        analyzed_at: When the analysis was performed.
        threshold: Number of signals that trigger reconciliation.
        code_files_scanned: Number of code files analyzed.
        artifacts_checked: Number of artifacts analyzed.
    """

    signals: list[DriftSignal] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)
    threshold: int = 3
    code_files_scanned: int = 0
    artifacts_checked: int = 0

    @property
    def signal_count(self) -> int:
        """Total number of drift signals."""
        return len(self.signals)

    @property
    def exceeds_threshold(self) -> bool:
        """Whether signal count exceeds threshold."""
        return self.signal_count >= self.threshold

    @property
    def requires_reconciliation(self) -> bool:
        """Whether reconciliation is required.

        Returns True if threshold is exceeded OR any critical signals exist.
        """
        has_critical = any(
            s.severity == DriftSeverity.CRITICAL for s in self.signals
        )
        return self.exceeds_threshold or has_critical

    @property
    def has_high_severity(self) -> bool:
        """Whether any high or critical severity signals exist."""
        return any(
            s.severity in (DriftSeverity.HIGH, DriftSeverity.CRITICAL)
            for s in self.signals
        )

    def by_type(self, signal_type: DriftSignalType) -> list[DriftSignal]:
        """Get signals of a specific type."""
        return [s for s in self.signals if s.signal_type == signal_type]

    def by_severity(self, severity: DriftSeverity) -> list[DriftSignal]:
        """Get signals of a specific severity."""
        return [s for s in self.signals if s.severity == severity]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "analyzed_at": self.analyzed_at.isoformat(),
            "threshold": self.threshold,
            "code_files_scanned": self.code_files_scanned,
            "artifacts_checked": self.artifacts_checked,
            "signal_count": self.signal_count,
            "exceeds_threshold": self.exceeds_threshold,
            "requires_reconciliation": self.requires_reconciliation,
            "signals": [s.to_dict() for s in self.signals],
            "summary": {
                "orphan_code": len(self.by_type(DriftSignalType.ORPHAN_CODE)),
                "orphan_plan": len(self.by_type(DriftSignalType.ORPHAN_PLAN)),
                "undocumented_behavior": len(
                    self.by_type(DriftSignalType.UNDOCUMENTED_BEHAVIOR)
                ),
                "refactor_hotspot": len(
                    self.by_type(DriftSignalType.REFACTOR_HOTSPOT)
                ),
            },
        }


@dataclass
class DriftConfig:
    """Configuration for drift detection.

    Attributes:
        drift_threshold: Number of signals that require reconciliation.
        code_patterns: Glob patterns for code files to scan.
        ignore_patterns: Glob patterns for files to ignore.
        refactor_threshold: Number of refactors to trigger hotspot signal.
        refactor_window_days: Lookback period for refactor analysis.
        source_dirs: Directories to scan for code files.
    """

    drift_threshold: int = 3
    code_patterns: list[str] = field(
        default_factory=lambda: [
            "*.py",
            "*.ts",
            "*.js",
            "*.go",
            "*.rs",
            "*.java",
        ]
    )
    ignore_patterns: list[str] = field(
        default_factory=lambda: [
            "*_test.py",
            "test_*.py",
            "tests/*",
            "__pycache__/*",
            "node_modules/*",
            "*.pyc",
            ".git/*",
            ".venv/*",
            "venv/*",
        ]
    )
    refactor_threshold: int = 3
    refactor_window_days: int = 30
    source_dirs: list[str] = field(default_factory=lambda: ["src"])

    def should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored based on patterns."""
        from fnmatch import fnmatch

        return any(fnmatch(path, pattern) for pattern in self.ignore_patterns)

    def matches_code_pattern(self, path: str) -> bool:
        """Check if a path matches code patterns."""
        from fnmatch import fnmatch

        return any(fnmatch(path, pattern) for pattern in self.code_patterns)

    @classmethod
    def from_file(cls, path: Path | str) -> "DriftConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to the configuration file.

        Returns:
            DriftConfig with values from file merged with defaults.
        """
        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            return cls()

        try:
            import yaml

            with path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                return cls()

            # Get drift section if it exists
            drift_data = data.get("drift", data)

            # Build config from known fields
            config_kwargs: dict[str, Any] = {}
            if "drift_threshold" in drift_data:
                config_kwargs["drift_threshold"] = drift_data["drift_threshold"]
            if "code_patterns" in drift_data:
                config_kwargs["code_patterns"] = drift_data["code_patterns"]
            if "ignore_patterns" in drift_data:
                config_kwargs["ignore_patterns"] = drift_data["ignore_patterns"]
            if "refactor_threshold" in drift_data:
                config_kwargs["refactor_threshold"] = drift_data["refactor_threshold"]
            if "refactor_window_days" in drift_data:
                config_kwargs["refactor_window_days"] = drift_data["refactor_window_days"]
            if "source_dirs" in drift_data:
                config_kwargs["source_dirs"] = drift_data["source_dirs"]

            return cls(**config_kwargs)

        except Exception:
            # On any error, return defaults
            return cls()
