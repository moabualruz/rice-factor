"""Approvals tracker for managing artifact approvals.

This module provides persistence for artifact approvals in a JSON file.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from rice_factor.domain.artifacts.approval import Approval


class ApprovalsTracker:
    """Tracks and persists artifact approvals.

    Stores approvals in a JSON file at `artifacts/_meta/approvals.json`.

    Attributes:
        approvals_file: Path to the approvals JSON file.
    """

    def __init__(self, artifacts_dir: Path) -> None:
        """Initialize the approvals tracker.

        Args:
            artifacts_dir: Root directory for artifacts.
        """
        self._artifacts_dir = artifacts_dir
        self._meta_dir = artifacts_dir / "_meta"
        self._approvals_file = self._meta_dir / "approvals.json"
        self._approvals: dict[UUID, Approval] = {}

        # Load existing approvals
        self._load()

    @property
    def approvals_file(self) -> Path:
        """Get the path to the approvals file."""
        return self._approvals_file

    def approve(self, artifact_id: UUID, approved_by: str) -> Approval:
        """Record an artifact approval.

        Args:
            artifact_id: UUID of the artifact to approve.
            approved_by: Identifier of who approved.

        Returns:
            The created Approval record.
        """
        approval = Approval(artifact_id=artifact_id, approved_by=approved_by)
        self._approvals[artifact_id] = approval
        self._save()
        return approval

    def is_approved(self, artifact_id: UUID) -> bool:
        """Check if an artifact is approved.

        Args:
            artifact_id: UUID to check.

        Returns:
            True if approved, False otherwise.
        """
        return artifact_id in self._approvals

    def get_approval(self, artifact_id: UUID) -> Approval | None:
        """Get the approval record for an artifact.

        Args:
            artifact_id: UUID of the artifact.

        Returns:
            The Approval record, or None if not approved.
        """
        return self._approvals.get(artifact_id)

    def list_approvals(self) -> list[Approval]:
        """List all approvals.

        Returns:
            List of all Approval records.
        """
        return list(self._approvals.values())

    def revoke(self, artifact_id: UUID) -> bool:
        """Revoke an approval (for draft artifacts only).

        Args:
            artifact_id: UUID of the artifact.

        Returns:
            True if revoked, False if not found.
        """
        if artifact_id in self._approvals:
            del self._approvals[artifact_id]
            self._save()
            return True
        return False

    def _load(self) -> None:
        """Load approvals from the JSON file."""
        if not self._approvals_file.exists():
            self._approvals = {}
            return

        try:
            content = self._approvals_file.read_text(encoding="utf-8")
            data = json.loads(content)

            self._approvals = {}
            for item in data.get("approvals", []):
                approval = Approval(
                    artifact_id=UUID(item["artifact_id"]),
                    approved_by=item["approved_by"],
                    approved_at=datetime.fromisoformat(item["approved_at"]),
                )
                self._approvals[approval.artifact_id] = approval
        except (json.JSONDecodeError, KeyError, ValueError):
            # If file is corrupted, start fresh
            self._approvals = {}

    def _save(self) -> None:
        """Save approvals to the JSON file."""
        # Ensure meta directory exists
        self._meta_dir.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "approvals": [
                {
                    "artifact_id": str(approval.artifact_id),
                    "approved_by": approval.approved_by,
                    "approved_at": approval.approved_at.isoformat(),
                }
                for approval in self._approvals.values()
            ]
        }

        json_str = json.dumps(data, indent=2)
        self._approvals_file.write_text(json_str, encoding="utf-8")
