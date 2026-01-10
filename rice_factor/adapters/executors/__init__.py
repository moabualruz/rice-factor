"""Executor adapters (scaffold, diff, refactor).

This module provides executor adapters that implement the ExecutorPort protocol
for applying changes to the repository based on approved artifacts.

Exports:
    CapabilityRegistry: Registry for tracking refactoring operation capabilities.
    CapabilityRegistryError: Error raised when registry operations fail.
    AuditLogger: Logger for executor audit trail.
    AuditLoggerError: Error raised when audit logging fails.
    execution_timer: Context manager for timing executor operations.
    ScaffoldExecutor: Executor for creating files from ScaffoldPlan artifacts.
    DiffExecutor: Executor for applying approved diffs using git apply.
"""

from rice_factor.adapters.executors.audit_logger import (
    AuditLogger,
    AuditLoggerError,
    execution_timer,
)
from rice_factor.adapters.executors.capability_registry import (
    CapabilityRegistry,
    CapabilityRegistryError,
)
from rice_factor.adapters.executors.diff_executor import DiffExecutor
from rice_factor.adapters.executors.refactor_executor_adapter import (
    RefactorExecutorAdapter,
)
from rice_factor.adapters.executors.scaffold_executor import ScaffoldExecutor

__all__ = [
    "AuditLogger",
    "AuditLoggerError",
    "CapabilityRegistry",
    "CapabilityRegistryError",
    "DiffExecutor",
    "RefactorExecutorAdapter",
    "ScaffoldExecutor",
    "execution_timer",
]
