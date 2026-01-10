"""Artifact storage adapters.

This module provides implementations of the StoragePort for persisting
artifacts to various backends.
"""

from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.adapters.storage.registry import ArtifactRegistry

__all__ = [
    "ApprovalsTracker",
    "ArtifactRegistry",
    "FilesystemStorageAdapter",
]
