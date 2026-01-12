"""Domain service adapter for web interface.

Provides a facade over the core rice_factor domain services,
handling project root configuration and service instantiation.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rice_factor.adapters.audit.trail import AuditTrail
    from rice_factor.adapters.storage.approvals import ApprovalsTracker
    from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
    from rice_factor.adapters.viz.graph_generator import GraphGenerator
    from rice_factor.domain.services.artifact_service import ArtifactService
    from rice_factor.domain.services.lifecycle_service import LifecycleService


class WebServiceAdapter:
    """Adapts domain services for web interface use.

    This class provides a facade over the core domain services,
    handling project root configuration and service instantiation.
    Follows the hexagonal architecture pattern where the web entrypoint
    adapts domain services to HTTP protocol.

    Attributes:
        project_root: Path to the rice-factor project root.
    """

    def __init__(self, project_root: Path) -> None:
        """Initialize with project root path.

        Args:
            project_root: Path to the rice-factor project root.
        """
        self._project_root = project_root
        self._artifacts_dir = project_root / "artifacts"

        # Lazy initialization - services created on first access
        self._storage: "FilesystemStorageAdapter | None" = None
        self._approvals: "ApprovalsTracker | None" = None
        self._audit_trail: "AuditTrail | None" = None
        self._artifact_service: "ArtifactService | None" = None
        self._lifecycle_service: "LifecycleService | None" = None
        self._graph_generator: "GraphGenerator | None" = None

    @property
    def project_root(self) -> Path:
        """Get the project root path."""
        return self._project_root

    @property
    def artifacts_dir(self) -> Path:
        """Get the artifacts directory path."""
        return self._artifacts_dir

    @property
    def storage(self) -> "FilesystemStorageAdapter":
        """Get the storage adapter (lazy initialization).

        Returns:
            FilesystemStorageAdapter instance.
        """
        if self._storage is None:
            from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter

            self._storage = FilesystemStorageAdapter(self._artifacts_dir)
        return self._storage

    @property
    def approvals(self) -> "ApprovalsTracker":
        """Get the approvals tracker (lazy initialization).

        Returns:
            ApprovalsTracker instance.
        """
        if self._approvals is None:
            from rice_factor.adapters.storage.approvals import ApprovalsTracker

            self._approvals = ApprovalsTracker(self._artifacts_dir)
        return self._approvals

    @property
    def audit_trail(self) -> "AuditTrail":
        """Get the audit trail (lazy initialization).

        Returns:
            AuditTrail instance.
        """
        if self._audit_trail is None:
            from rice_factor.adapters.audit.trail import AuditTrail

            self._audit_trail = AuditTrail(self._project_root)
        return self._audit_trail

    @property
    def artifact_service(self) -> "ArtifactService":
        """Get the artifact service (lazy initialization).

        Returns:
            ArtifactService instance.
        """
        if self._artifact_service is None:
            from rice_factor.domain.services.artifact_service import ArtifactService

            self._artifact_service = ArtifactService(self.storage, self.approvals)
        return self._artifact_service

    @property
    def lifecycle_service(self) -> "LifecycleService":
        """Get the lifecycle service (lazy initialization).

        Returns:
            LifecycleService instance.
        """
        if self._lifecycle_service is None:
            from rice_factor.domain.services.lifecycle_service import LifecycleService

            self._lifecycle_service = LifecycleService(artifact_store=self.storage)
        return self._lifecycle_service

    @property
    def graph_generator(self) -> "GraphGenerator":
        """Get the graph generator (lazy initialization).

        Returns:
            GraphGenerator instance.
        """
        if self._graph_generator is None:
            from rice_factor.adapters.viz.graph_generator import GraphGenerator

            self._graph_generator = GraphGenerator()
        return self._graph_generator

    def is_initialized(self) -> bool:
        """Check if the project is initialized (has artifacts directory).

        Returns:
            True if artifacts directory exists.
        """
        return self._artifacts_dir.exists()

    def ensure_initialized(self) -> None:
        """Ensure the project is initialized.

        Raises:
            ValueError: If project is not initialized.
        """
        if not self.is_initialized():
            raise ValueError(
                f"Project not initialized at {self._project_root}. "
                "Run 'rice-factor init' first."
            )
