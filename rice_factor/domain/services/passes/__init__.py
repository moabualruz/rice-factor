"""Compiler passes for artifact generation.

This module provides the PassRegistry and individual compiler pass
implementations for each artifact type.
"""

from typing import TYPE_CHECKING

from rice_factor.domain.artifacts.compiler_types import CompilerPassType

if TYPE_CHECKING:
    from rice_factor.domain.services.compiler_pass import CompilerPass


class PassNotFoundError(Exception):
    """Raised when a pass type is not found in the registry."""

    def __init__(self, pass_type: CompilerPassType) -> None:
        """Initialize the error.

        Args:
            pass_type: The pass type that was not found.
        """
        self.pass_type = pass_type
        super().__init__(f"No pass registered for type: {pass_type.value}")


class PassRegistry:
    """Registry for compiler passes.

    Provides a way to get the appropriate compiler pass implementation
    for a given pass type.
    """

    _instance: "PassRegistry | None" = None

    def __init__(self) -> None:
        """Initialize the registry with all passes."""
        # Import here to avoid circular imports
        from rice_factor.domain.services.passes.architecture_planner import (
            ArchitecturePlannerPass,
        )
        from rice_factor.domain.services.passes.implementation_planner import (
            ImplementationPlannerPass,
        )
        from rice_factor.domain.services.passes.project_planner import (
            ProjectPlannerPass,
        )
        from rice_factor.domain.services.passes.refactor_planner import (
            RefactorPlannerPass,
        )
        from rice_factor.domain.services.passes.scaffold_planner import (
            ScaffoldPlannerPass,
        )
        from rice_factor.domain.services.passes.test_designer import TestDesignerPass

        self._passes: dict[CompilerPassType, type[CompilerPass]] = {
            CompilerPassType.PROJECT: ProjectPlannerPass,
            CompilerPassType.ARCHITECTURE: ArchitecturePlannerPass,
            CompilerPassType.SCAFFOLD: ScaffoldPlannerPass,
            CompilerPassType.TEST: TestDesignerPass,
            CompilerPassType.IMPLEMENTATION: ImplementationPlannerPass,
            CompilerPassType.REFACTOR: RefactorPlannerPass,
        }

    @classmethod
    def get_instance(cls) -> "PassRegistry":
        """Get the singleton instance of the registry.

        Returns:
            The PassRegistry instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None

    def get_pass(self, pass_type: CompilerPassType) -> "CompilerPass":
        """Get a compiler pass instance for the given type.

        Args:
            pass_type: The type of pass to get.

        Returns:
            A new instance of the appropriate CompilerPass.

        Raises:
            PassNotFoundError: If no pass is registered for the type.
        """
        pass_class = self._passes.get(pass_type)
        if pass_class is None:
            raise PassNotFoundError(pass_type)
        return pass_class()

    def get_pass_class(
        self, pass_type: CompilerPassType
    ) -> type["CompilerPass"] | None:
        """Get the pass class for the given type.

        Args:
            pass_type: The type of pass to get.

        Returns:
            The CompilerPass class, or None if not found.
        """
        return self._passes.get(pass_type)

    def list_passes(self) -> list[CompilerPassType]:
        """List all registered pass types.

        Returns:
            List of registered pass types.
        """
        return list(self._passes.keys())


def get_pass(pass_type: CompilerPassType) -> "CompilerPass":
    """Convenience function to get a pass from the registry.

    Args:
        pass_type: The type of pass to get.

    Returns:
        A new instance of the appropriate CompilerPass.

    Raises:
        PassNotFoundError: If no pass is registered for the type.
    """
    return PassRegistry.get_instance().get_pass(pass_type)


__all__ = [
    "PassNotFoundError",
    "PassRegistry",
    "get_pass",
]
