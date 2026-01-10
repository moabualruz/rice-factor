"""Override service for bypassing blocked operations.

This module provides the OverrideService for recording manual overrides
of blocked operations with audit trail support.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4


@dataclass
class Override:
    """Record of a manual override.

    Attributes:
        id: Unique identifier for the override.
        target: What was overridden (e.g., "phase_gating", "unapproved_artifact").
        reason: User-provided reason for the override.
        context: Additional context about the override.
        timestamp: When the override was recorded.
        reconciled: Whether the override has been reconciled.
        reconciled_at: When the override was reconciled.
    """

    id: UUID
    target: str
    reason: str
    context: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    reconciled: bool = False
    reconciled_at: datetime | None = None


class OverrideService:
    """Service for managing manual overrides.

    Overrides are recorded in the audit trail and flagged for reconciliation.
    This provides an escape hatch for blocked operations while maintaining
    full traceability.

    Attributes:
        project_path: Path to the project root.
    """

    def __init__(self, project_path: Path) -> None:
        """Initialize the override service.

        Args:
            project_path: Path to the project root directory.
        """
        self._project_path = project_path
        self._audit_dir = project_path / "audit"
        self._overrides_file = self._audit_dir / "overrides.json"
        self._overrides: dict[UUID, Override] = {}
        self._load()

    @property
    def project_path(self) -> Path:
        """Get the project path."""
        return self._project_path

    @property
    def overrides_file(self) -> Path:
        """Get the path to the overrides file."""
        return self._overrides_file

    def record_override(
        self,
        target: str,
        reason: str,
        context: dict[str, str] | None = None,
    ) -> Override:
        """Record a manual override.

        Args:
            target: What is being overridden.
            reason: User-provided reason for the override.
            context: Optional additional context.

        Returns:
            The created Override record.
        """
        override = Override(
            id=uuid4(),
            target=target,
            reason=reason,
            context=context or {},
        )
        self._overrides[override.id] = override
        self._save()
        return override

    def get_pending_overrides(self) -> list[Override]:
        """Get all unreconciled overrides.

        Returns:
            List of Override records that haven't been reconciled.
        """
        return [o for o in self._overrides.values() if not o.reconciled]

    def get_all_overrides(self) -> list[Override]:
        """Get all overrides.

        Returns:
            List of all Override records.
        """
        return list(self._overrides.values())

    def mark_reconciled(self, override_id: UUID) -> bool:
        """Mark an override as reconciled.

        Args:
            override_id: UUID of the override to reconcile.

        Returns:
            True if marked, False if not found.
        """
        override = self._overrides.get(override_id)
        if override is None:
            return False

        override.reconciled = True
        override.reconciled_at = datetime.now(UTC)
        self._save()
        return True

    def get_override(self, override_id: UUID) -> Override | None:
        """Get an override by ID.

        Args:
            override_id: UUID of the override.

        Returns:
            The Override record, or None if not found.
        """
        return self._overrides.get(override_id)

    def _load(self) -> None:
        """Load overrides from the JSON file."""
        if not self._overrides_file.exists():
            self._overrides = {}
            return

        try:
            content = self._overrides_file.read_text(encoding="utf-8")
            data = json.loads(content)

            self._overrides = {}
            for item in data.get("overrides", []):
                reconciled_at = None
                if item.get("reconciled_at"):
                    reconciled_at = datetime.fromisoformat(item["reconciled_at"])

                override = Override(
                    id=UUID(item["id"]),
                    target=item["target"],
                    reason=item["reason"],
                    context=item.get("context", {}),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    reconciled=item.get("reconciled", False),
                    reconciled_at=reconciled_at,
                )
                self._overrides[override.id] = override
        except (json.JSONDecodeError, KeyError, ValueError):
            self._overrides = {}

    def _save(self) -> None:
        """Save overrides to the JSON file."""
        self._audit_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "overrides": [
                {
                    "id": str(override.id),
                    "target": override.target,
                    "reason": override.reason,
                    "context": override.context,
                    "timestamp": override.timestamp.isoformat(),
                    "reconciled": override.reconciled,
                    "reconciled_at": (
                        override.reconciled_at.isoformat()
                        if override.reconciled_at
                        else None
                    ),
                }
                for override in self._overrides.values()
            ]
        }

        json_str = json.dumps(data, indent=2)
        self._overrides_file.write_text(json_str, encoding="utf-8")
