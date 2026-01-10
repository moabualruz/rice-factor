"""Artifact service for managing artifact lifecycle.

This module provides the service layer for artifact operations including
status transitions and modification enforcement.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel

from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.approval import Approval
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.failures.errors import (
    ArtifactNotFoundError,
    ArtifactStatusError,
)


class ArtifactService:
    """Service for managing artifact lifecycle operations.

    Coordinates between storage and approval tracking to manage artifact
    status transitions and modifications.

    Attributes:
        storage: Storage adapter for persisting artifacts.
        approvals: Tracker for managing approvals.
    """

    def __init__(
        self,
        storage: FilesystemStorageAdapter,
        approvals: ApprovalsTracker,
    ) -> None:
        """Initialize the artifact service.

        Args:
            storage: Storage adapter for artifact persistence.
            approvals: Tracker for approval records.
        """
        self._storage = storage
        self._approvals = approvals

    @property
    def storage(self) -> FilesystemStorageAdapter:
        """Get the storage adapter."""
        return self._storage

    @property
    def approvals(self) -> ApprovalsTracker:
        """Get the approvals tracker."""
        return self._approvals

    def approve(
        self,
        artifact_id: UUID,
        approved_by: str,
        artifact_type: ArtifactType | None = None,
    ) -> Approval:
        """Approve an artifact, transitioning it from DRAFT to APPROVED.

        Args:
            artifact_id: UUID of the artifact to approve.
            approved_by: Identifier of who is approving.
            artifact_type: Optional type hint for faster lookup.

        Returns:
            The Approval record created.

        Raises:
            ArtifactNotFoundError: If artifact doesn't exist.
            ArtifactStatusError: If artifact is not in DRAFT status.
        """
        # Load the artifact
        artifact = self._storage.load_by_id(artifact_id, artifact_type)

        # Transition to approved (raises if invalid)
        approved_artifact = artifact.approve()

        # Save the updated artifact
        self._storage.save(approved_artifact)

        # Record the approval
        approval = self._approvals.approve(artifact_id, approved_by)

        return approval

    def lock(
        self,
        artifact_id: UUID,
        artifact_type: ArtifactType | None = None,
    ) -> ArtifactEnvelope[BaseModel]:
        """Lock a TestPlan artifact, transitioning from APPROVED to LOCKED.

        Args:
            artifact_id: UUID of the artifact to lock.
            artifact_type: Optional type hint (should be TEST_PLAN).

        Returns:
            The locked artifact.

        Raises:
            ArtifactNotFoundError: If artifact doesn't exist.
            ArtifactStatusError: If artifact is not APPROVED or not a TestPlan.
        """
        # Load the artifact
        artifact = self._storage.load_by_id(artifact_id, artifact_type)

        # Transition to locked (raises if invalid)
        locked_artifact = artifact.lock()

        # Save the updated artifact
        self._storage.save(locked_artifact)

        return locked_artifact

    def modify(
        self,
        artifact_id: UUID,
        updates: dict[str, Any],
        artifact_type: ArtifactType | None = None,
    ) -> ArtifactEnvelope[BaseModel]:
        """Modify an artifact's payload.

        Only DRAFT artifacts can be modified. Approved and locked artifacts
        reject all modifications.

        Args:
            artifact_id: UUID of the artifact to modify.
            updates: Dictionary of payload fields to update.
            artifact_type: Optional type hint for faster lookup.

        Returns:
            The modified artifact.

        Raises:
            ArtifactNotFoundError: If artifact doesn't exist.
            ArtifactStatusError: If artifact is not in DRAFT status.
        """
        # Load the artifact
        artifact = self._storage.load_by_id(artifact_id, artifact_type)

        # Check if modifiable
        if not artifact.is_modifiable():
            if artifact.status == ArtifactStatus.LOCKED:
                # Hard fail for locked TestPlan (M02-I-004)
                raise ArtifactStatusError(
                    f"LOCKED artifact '{artifact_id}' cannot be modified. "
                    "TestPlan artifacts are permanently immutable after locking."
                )
            raise ArtifactStatusError(
                f"Cannot modify artifact with status '{artifact.status.value}'. "
                "Only DRAFT artifacts can be modified."
            )

        # Update the payload
        current_payload = artifact.payload
        updated_payload = current_payload.model_copy(update=updates)

        # Create updated artifact
        modified_artifact = artifact.model_copy(update={"payload": updated_payload})

        # Save the updated artifact
        self._storage.save(modified_artifact)

        return modified_artifact

    def get(
        self,
        artifact_id: UUID,
        artifact_type: ArtifactType | None = None,
    ) -> ArtifactEnvelope[BaseModel]:
        """Get an artifact by ID.

        Args:
            artifact_id: UUID of the artifact.
            artifact_type: Optional type hint for faster lookup.

        Returns:
            The artifact envelope.

        Raises:
            ArtifactNotFoundError: If artifact doesn't exist.
        """
        return self._storage.load_by_id(artifact_id, artifact_type)

    def is_approved(self, artifact_id: UUID) -> bool:
        """Check if an artifact has been approved.

        Args:
            artifact_id: UUID of the artifact.

        Returns:
            True if the artifact has an approval record.
        """
        return self._approvals.is_approved(artifact_id)

    def get_approval(self, artifact_id: UUID) -> Approval | None:
        """Get the approval record for an artifact.

        Args:
            artifact_id: UUID of the artifact.

        Returns:
            The Approval record, or None if not approved.
        """
        return self._approvals.get_approval(artifact_id)

    def revoke_approval(self, artifact_id: UUID) -> bool:
        """Revoke an approval (revert to draft status).

        This is only allowed for APPROVED artifacts, not LOCKED ones.

        Args:
            artifact_id: UUID of the artifact.

        Returns:
            True if revoked, False if not found or not allowed.

        Raises:
            ArtifactStatusError: If artifact is LOCKED.
        """
        # Check if artifact is locked
        try:
            artifact = self._storage.load_by_id(artifact_id)
        except ArtifactNotFoundError:
            return False

        if artifact.status == ArtifactStatus.LOCKED:
            raise ArtifactStatusError(
                f"Cannot revoke approval for LOCKED artifact '{artifact_id}'. "
                "Locked artifacts are permanently immutable."
            )

        # Revoke from tracker
        if self._approvals.revoke(artifact_id):
            # Revert artifact status to draft
            draft_artifact = artifact.model_copy(
                update={"status": ArtifactStatus.DRAFT}
            )
            self._storage.save(draft_artifact)
            return True
        return False
