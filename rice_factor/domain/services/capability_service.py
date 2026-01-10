"""Capability verification service for refactoring operations.

This service verifies that the required refactoring operations are
supported for the target language.
"""

from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorOperationType,
    RefactorPlanPayload,
)

# Stub capability matrix - defines which operations are supported per language
# In a real implementation, this would query actual tooling/LSP capabilities
CAPABILITY_MATRIX: dict[str, set[RefactorOperationType]] = {
    "python": {
        RefactorOperationType.MOVE_FILE,
        RefactorOperationType.RENAME_SYMBOL,
        RefactorOperationType.EXTRACT_INTERFACE,
        RefactorOperationType.ENFORCE_DEPENDENCY,
    },
    "rust": {
        RefactorOperationType.MOVE_FILE,
        RefactorOperationType.RENAME_SYMBOL,
    },
    "go": {
        RefactorOperationType.MOVE_FILE,
        RefactorOperationType.RENAME_SYMBOL,
    },
    "java": {
        RefactorOperationType.MOVE_FILE,
        RefactorOperationType.RENAME_SYMBOL,
        RefactorOperationType.EXTRACT_INTERFACE,
    },
    "typescript": {
        RefactorOperationType.MOVE_FILE,
        RefactorOperationType.RENAME_SYMBOL,
        RefactorOperationType.EXTRACT_INTERFACE,
    },
    "javascript": {
        RefactorOperationType.MOVE_FILE,
        RefactorOperationType.RENAME_SYMBOL,
    },
}


class CapabilityService:
    """Service for verifying refactoring capability support.

    This service checks whether the required refactoring operations
    are supported for the target language.
    """

    def __init__(self, language: str = "python") -> None:
        """Initialize the capability service.

        Args:
            language: The target programming language.
        """
        self._language = language.lower()

    @property
    def language(self) -> str:
        """Get the target language."""
        return self._language

    def is_operation_supported(self, operation: RefactorOperationType) -> bool:
        """Check if a single operation is supported.

        Args:
            operation: The refactor operation type to check.

        Returns:
            True if the operation is supported, False otherwise.
        """
        supported = CAPABILITY_MATRIX.get(self._language, set())
        return operation in supported

    def get_supported_operations(self) -> set[RefactorOperationType]:
        """Get all supported operations for the current language.

        Returns:
            Set of supported refactor operation types.
        """
        return CAPABILITY_MATRIX.get(self._language, set()).copy()

    def get_unsupported_operations(
        self, plan: RefactorPlanPayload
    ) -> list[RefactorOperationType]:
        """Get operations in the plan that are not supported.

        Args:
            plan: The refactor plan to check.

        Returns:
            List of unsupported operation types.
        """
        unsupported = []
        supported = CAPABILITY_MATRIX.get(self._language, set())

        for op in plan.operations:
            if op.type not in supported and op.type not in unsupported:
                unsupported.append(op.type)

        return unsupported

    def check_capabilities(self, plan: RefactorPlanPayload) -> bool:
        """Check if all operations in the plan are supported.

        Args:
            plan: The refactor plan to check.

        Returns:
            True if all operations are supported, False otherwise.
        """
        return len(self.get_unsupported_operations(plan)) == 0

    def get_capability_summary(
        self, plan: RefactorPlanPayload
    ) -> dict[RefactorOperationType, bool]:
        """Get a summary of capability support for plan operations.

        Args:
            plan: The refactor plan to check.

        Returns:
            Dict mapping operation types to their support status.
        """
        supported = CAPABILITY_MATRIX.get(self._language, set())
        summary: dict[RefactorOperationType, bool] = {}

        for op in plan.operations:
            summary[op.type] = op.type in supported

        return summary
