"""Override scope manager for limiting and tracking overrides.

This module provides the OverrideScopeManager for enforcing scope limits
on overrides and integrating with CI to flag overridden files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID


class OverrideServicePort(Protocol):
    """Protocol for override service operations."""

    def get_pending_overrides(self) -> list[Any]:
        """Get pending overrides."""
        ...

    def get_all_overrides(self) -> list[Any]:
        """Get all overrides."""
        ...


class OverrideScope(Enum):
    """Scope of an override."""

    FILE = "file"  # Single file override
    DIRECTORY = "directory"  # Directory-level override
    PROJECT = "project"  # Project-wide override
    ARTIFACT = "artifact"  # Specific artifact override


class ScopeLimitViolation(Exception):
    """Raised when an override violates scope limits."""

    def __init__(self, message: str, limit: str, current: int, max_allowed: int) -> None:
        self.limit = limit
        self.current = current
        self.max_allowed = max_allowed
        super().__init__(message)


@dataclass
class ScopeLimit:
    """Configuration for a scope limit."""

    max_file_overrides: int = 10  # Max files that can be overridden simultaneously
    max_directory_overrides: int = 3  # Max directories
    max_project_overrides: int = 1  # Max project-wide overrides
    max_override_age_days: int = 30  # Max age before forced reconciliation
    require_reason_min_length: int = 20  # Minimum characters for reason


@dataclass
class OverrideRecord:
    """Record of an override with scope information."""

    override_id: str
    scope: OverrideScope
    target_path: str
    reason: str
    created_at: datetime
    created_by: str | None = None
    reconciled: bool = False
    reconciled_at: datetime | None = None
    ci_flagged: bool = False
    ci_flag_commit: str | None = None


@dataclass
class CIFlag:
    """CI flag for an overridden file."""

    file_path: str
    override_id: str
    flagged_at: datetime
    flagged_commit: str
    message: str
    severity: str = "warning"  # "warning" or "error"


@dataclass
class ScopeReport:
    """Report on current override scope usage."""

    generated_at: datetime
    file_overrides: int
    directory_overrides: int
    project_overrides: int
    artifact_overrides: int
    violations: list[str]
    expiring_soon: list[OverrideRecord]  # Overrides expiring within 7 days
    ci_flags: list[CIFlag]

    @property
    def total_overrides(self) -> int:
        """Get total number of active overrides."""
        return (
            self.file_overrides
            + self.directory_overrides
            + self.project_overrides
            + self.artifact_overrides
        )

    @property
    def has_violations(self) -> bool:
        """Check if there are any scope violations."""
        return len(self.violations) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "total_overrides": self.total_overrides,
            "file_overrides": self.file_overrides,
            "directory_overrides": self.directory_overrides,
            "project_overrides": self.project_overrides,
            "artifact_overrides": self.artifact_overrides,
            "violations": self.violations,
            "expiring_soon_count": len(self.expiring_soon),
            "ci_flags_count": len(self.ci_flags),
        }


@dataclass
class OverrideScopeManager:
    """Manager for override scope limits and CI flag integration.

    This service enforces configurable limits on overrides by scope
    (file, directory, project) and integrates with CI to permanently
    flag overridden files until reconciliation.

    Attributes:
        repo_root: Root directory of the repository.
        limits: Scope limit configuration.
        override_service: Optional override service for existing data.
    """

    repo_root: Path
    limits: ScopeLimit = field(default_factory=ScopeLimit)
    override_service: OverrideServicePort | None = None
    _records: dict[str, OverrideRecord] = field(default_factory=dict, init=False)
    _ci_flags: list[CIFlag] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Initialize by loading existing records."""
        self._load()

    def _get_records_path(self) -> Path:
        """Get path to scope records file."""
        return self.repo_root / "audit" / "override_scopes.json"

    def _get_flags_path(self) -> Path:
        """Get path to CI flags file."""
        return self.repo_root / "audit" / "ci_override_flags.json"

    def _load(self) -> None:
        """Load existing records and flags."""
        self._load_records()
        self._load_ci_flags()

    def _load_records(self) -> None:
        """Load override records from file."""
        records_path = self._get_records_path()
        if not records_path.exists():
            return

        try:
            data = json.loads(records_path.read_text(encoding="utf-8"))
            for item in data.get("records", []):
                reconciled_at = None
                if item.get("reconciled_at"):
                    reconciled_at = datetime.fromisoformat(item["reconciled_at"])

                record = OverrideRecord(
                    override_id=item["override_id"],
                    scope=OverrideScope(item["scope"]),
                    target_path=item["target_path"],
                    reason=item["reason"],
                    created_at=datetime.fromisoformat(item["created_at"]),
                    created_by=item.get("created_by"),
                    reconciled=item.get("reconciled", False),
                    reconciled_at=reconciled_at,
                    ci_flagged=item.get("ci_flagged", False),
                    ci_flag_commit=item.get("ci_flag_commit"),
                )
                self._records[record.override_id] = record
        except (json.JSONDecodeError, KeyError, ValueError):
            self._records = {}

    def _load_ci_flags(self) -> None:
        """Load CI flags from file."""
        flags_path = self._get_flags_path()
        if not flags_path.exists():
            return

        try:
            data = json.loads(flags_path.read_text(encoding="utf-8"))
            self._ci_flags = []
            for item in data.get("flags", []):
                flag = CIFlag(
                    file_path=item["file_path"],
                    override_id=item["override_id"],
                    flagged_at=datetime.fromisoformat(item["flagged_at"]),
                    flagged_commit=item["flagged_commit"],
                    message=item["message"],
                    severity=item.get("severity", "warning"),
                )
                self._ci_flags.append(flag)
        except (json.JSONDecodeError, KeyError, ValueError):
            self._ci_flags = []

    def _save_records(self) -> None:
        """Save override records to file."""
        records_path = self._get_records_path()
        records_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "records": [
                {
                    "override_id": r.override_id,
                    "scope": r.scope.value,
                    "target_path": r.target_path,
                    "reason": r.reason,
                    "created_at": r.created_at.isoformat(),
                    "created_by": r.created_by,
                    "reconciled": r.reconciled,
                    "reconciled_at": (
                        r.reconciled_at.isoformat() if r.reconciled_at else None
                    ),
                    "ci_flagged": r.ci_flagged,
                    "ci_flag_commit": r.ci_flag_commit,
                }
                for r in self._records.values()
            ]
        }

        records_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _save_ci_flags(self) -> None:
        """Save CI flags to file."""
        flags_path = self._get_flags_path()
        flags_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "flags": [
                {
                    "file_path": f.file_path,
                    "override_id": f.override_id,
                    "flagged_at": f.flagged_at.isoformat(),
                    "flagged_commit": f.flagged_commit,
                    "message": f.message,
                    "severity": f.severity,
                }
                for f in self._ci_flags
            ]
        }

        flags_path.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def register_override(
        self,
        override_id: str,
        scope: OverrideScope,
        target_path: str,
        reason: str,
        created_by: str | None = None,
    ) -> OverrideRecord:
        """Register a new override with scope tracking.

        Args:
            override_id: Unique identifier for the override.
            scope: Scope of the override.
            target_path: Target file/directory/artifact path.
            reason: Reason for the override.
            created_by: Optional user who created the override.

        Returns:
            The created OverrideRecord.

        Raises:
            ScopeLimitViolation: If registering would exceed scope limits.
            ValueError: If reason is too short.
        """
        # Validate reason length
        if len(reason) < self.limits.require_reason_min_length:
            raise ValueError(
                f"Override reason must be at least {self.limits.require_reason_min_length} characters"
            )

        # Check scope limits
        self._check_scope_limits(scope)

        # Create record
        record = OverrideRecord(
            override_id=override_id,
            scope=scope,
            target_path=target_path,
            reason=reason,
            created_at=datetime.now(UTC),
            created_by=created_by,
        )

        self._records[override_id] = record
        self._save_records()
        return record

    def _check_scope_limits(self, new_scope: OverrideScope) -> None:
        """Check if adding a new override would exceed limits.

        Args:
            new_scope: Scope of the new override.

        Raises:
            ScopeLimitViolation: If limit would be exceeded.
        """
        active = self.get_active_overrides()

        counts = {
            OverrideScope.FILE: 0,
            OverrideScope.DIRECTORY: 0,
            OverrideScope.PROJECT: 0,
            OverrideScope.ARTIFACT: 0,
        }

        for record in active:
            counts[record.scope] += 1

        if new_scope == OverrideScope.FILE:
            if counts[OverrideScope.FILE] >= self.limits.max_file_overrides:
                raise ScopeLimitViolation(
                    f"Cannot exceed {self.limits.max_file_overrides} file overrides",
                    limit="max_file_overrides",
                    current=counts[OverrideScope.FILE],
                    max_allowed=self.limits.max_file_overrides,
                )

        elif new_scope == OverrideScope.DIRECTORY:
            if counts[OverrideScope.DIRECTORY] >= self.limits.max_directory_overrides:
                raise ScopeLimitViolation(
                    f"Cannot exceed {self.limits.max_directory_overrides} directory overrides",
                    limit="max_directory_overrides",
                    current=counts[OverrideScope.DIRECTORY],
                    max_allowed=self.limits.max_directory_overrides,
                )

        elif new_scope == OverrideScope.PROJECT:
            if counts[OverrideScope.PROJECT] >= self.limits.max_project_overrides:
                raise ScopeLimitViolation(
                    f"Cannot exceed {self.limits.max_project_overrides} project overrides",
                    limit="max_project_overrides",
                    current=counts[OverrideScope.PROJECT],
                    max_allowed=self.limits.max_project_overrides,
                )

    def get_active_overrides(self) -> list[OverrideRecord]:
        """Get all active (non-reconciled) overrides.

        Returns:
            List of active override records.
        """
        return [r for r in self._records.values() if not r.reconciled]

    def get_overrides_by_scope(self, scope: OverrideScope) -> list[OverrideRecord]:
        """Get active overrides by scope.

        Args:
            scope: The scope to filter by.

        Returns:
            List of matching override records.
        """
        return [r for r in self.get_active_overrides() if r.scope == scope]

    def reconcile_override(
        self, override_id: str
    ) -> bool:
        """Mark an override as reconciled.

        Args:
            override_id: ID of the override to reconcile.

        Returns:
            True if reconciled, False if not found.
        """
        record = self._records.get(override_id)
        if record is None:
            return False

        record.reconciled = True
        record.reconciled_at = datetime.now(UTC)
        self._save_records()

        # Remove associated CI flags
        self._ci_flags = [
            f for f in self._ci_flags if f.override_id != override_id
        ]
        self._save_ci_flags()

        return True

    def flag_for_ci(
        self,
        override_id: str,
        commit_hash: str,
        severity: str = "warning",
    ) -> CIFlag | None:
        """Create a CI flag for an override.

        Args:
            override_id: ID of the override to flag.
            commit_hash: Current commit hash.
            severity: Flag severity ("warning" or "error").

        Returns:
            The created CIFlag, or None if override not found.
        """
        record = self._records.get(override_id)
        if record is None:
            return None

        # Check if already flagged
        existing = [f for f in self._ci_flags if f.override_id == override_id]
        if existing:
            return existing[0]

        flag = CIFlag(
            file_path=record.target_path,
            override_id=override_id,
            flagged_at=datetime.now(UTC),
            flagged_commit=commit_hash,
            message=f"Override active: {record.reason[:50]}...",
            severity=severity,
        )

        self._ci_flags.append(flag)
        record.ci_flagged = True
        record.ci_flag_commit = commit_hash
        self._save_records()
        self._save_ci_flags()

        return flag

    def get_ci_flags(self) -> list[CIFlag]:
        """Get all active CI flags.

        Returns:
            List of active CI flags.
        """
        # Filter to only include flags for active overrides
        active_ids = {r.override_id for r in self.get_active_overrides()}
        return [f for f in self._ci_flags if f.override_id in active_ids]

    def get_expiring_overrides(self, days: int = 7) -> list[OverrideRecord]:
        """Get overrides expiring within the specified days.

        Args:
            days: Number of days to look ahead.

        Returns:
            List of overrides that will expire soon.
        """
        expiring: list[OverrideRecord] = []
        now = datetime.now(UTC)

        for record in self.get_active_overrides():
            age_days = (now - record.created_at).days
            days_until_expiry = self.limits.max_override_age_days - age_days

            if 0 <= days_until_expiry <= days:
                expiring.append(record)

        return expiring

    def get_expired_overrides(self) -> list[OverrideRecord]:
        """Get overrides that have exceeded max age.

        Returns:
            List of expired overrides.
        """
        expired: list[OverrideRecord] = []
        now = datetime.now(UTC)

        for record in self.get_active_overrides():
            age_days = (now - record.created_at).days
            if age_days > self.limits.max_override_age_days:
                expired.append(record)

        return expired

    def check_scope_violations(self) -> list[str]:
        """Check for current scope violations.

        Returns:
            List of violation messages.
        """
        violations: list[str] = []
        active = self.get_active_overrides()

        counts = {
            OverrideScope.FILE: 0,
            OverrideScope.DIRECTORY: 0,
            OverrideScope.PROJECT: 0,
            OverrideScope.ARTIFACT: 0,
        }

        for record in active:
            counts[record.scope] += 1

        if counts[OverrideScope.FILE] > self.limits.max_file_overrides:
            violations.append(
                f"File override limit exceeded: {counts[OverrideScope.FILE]}/{self.limits.max_file_overrides}"
            )

        if counts[OverrideScope.DIRECTORY] > self.limits.max_directory_overrides:
            violations.append(
                f"Directory override limit exceeded: {counts[OverrideScope.DIRECTORY]}/{self.limits.max_directory_overrides}"
            )

        if counts[OverrideScope.PROJECT] > self.limits.max_project_overrides:
            violations.append(
                f"Project override limit exceeded: {counts[OverrideScope.PROJECT]}/{self.limits.max_project_overrides}"
            )

        # Check for expired overrides
        expired = self.get_expired_overrides()
        for record in expired:
            age_days = (datetime.now(UTC) - record.created_at).days
            violations.append(
                f"Expired override: {record.target_path} ({age_days} days old)"
            )

        return violations

    def generate_report(self) -> ScopeReport:
        """Generate a scope usage report.

        Returns:
            ScopeReport with current status.
        """
        active = self.get_active_overrides()

        counts = {
            OverrideScope.FILE: 0,
            OverrideScope.DIRECTORY: 0,
            OverrideScope.PROJECT: 0,
            OverrideScope.ARTIFACT: 0,
        }

        for record in active:
            counts[record.scope] += 1

        return ScopeReport(
            generated_at=datetime.now(UTC),
            file_overrides=counts[OverrideScope.FILE],
            directory_overrides=counts[OverrideScope.DIRECTORY],
            project_overrides=counts[OverrideScope.PROJECT],
            artifact_overrides=counts[OverrideScope.ARTIFACT],
            violations=self.check_scope_violations(),
            expiring_soon=self.get_expiring_overrides(),
            ci_flags=self.get_ci_flags(),
        )

    def is_path_overridden(self, path: str) -> bool:
        """Check if a path is currently overridden.

        Args:
            path: File or directory path to check.

        Returns:
            True if the path is under an active override.
        """
        path_normalized = path.replace("\\", "/")

        for record in self.get_active_overrides():
            target_normalized = record.target_path.replace("\\", "/")

            if record.scope == OverrideScope.FILE:
                if path_normalized == target_normalized:
                    return True

            elif record.scope == OverrideScope.DIRECTORY:
                if path_normalized.startswith(target_normalized + "/"):
                    return True
                if path_normalized == target_normalized:
                    return True

            elif record.scope == OverrideScope.PROJECT:
                # Project-wide override covers everything
                return True

        return False

    def get_override_for_path(self, path: str) -> OverrideRecord | None:
        """Get the override affecting a path.

        Args:
            path: File or directory path.

        Returns:
            The affecting OverrideRecord, or None.
        """
        path_normalized = path.replace("\\", "/")

        for record in self.get_active_overrides():
            target_normalized = record.target_path.replace("\\", "/")

            if record.scope == OverrideScope.FILE:
                if path_normalized == target_normalized:
                    return record

            elif record.scope == OverrideScope.DIRECTORY:
                if path_normalized.startswith(target_normalized + "/"):
                    return record
                if path_normalized == target_normalized:
                    return record

            elif record.scope == OverrideScope.PROJECT:
                return record

        return None
