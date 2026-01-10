"""Unit tests for PassRegistry."""

import pytest

from rice_factor.domain.artifacts.compiler_types import CompilerPassType
from rice_factor.domain.services.compiler_pass import CompilerPass
from rice_factor.domain.services.passes import (
    PassNotFoundError,
    PassRegistry,
    get_pass,
)
from rice_factor.domain.services.passes.architecture_planner import (
    ArchitecturePlannerPass,
)
from rice_factor.domain.services.passes.implementation_planner import (
    ImplementationPlannerPass,
)
from rice_factor.domain.services.passes.project_planner import ProjectPlannerPass
from rice_factor.domain.services.passes.refactor_planner import RefactorPlannerPass
from rice_factor.domain.services.passes.scaffold_planner import ScaffoldPlannerPass
from rice_factor.domain.services.passes.test_designer import TestDesignerPass


class TestPassRegistry:
    """Tests for PassRegistry class."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset singleton before each test."""
        PassRegistry.reset_instance()

    def test_get_instance_returns_singleton(self) -> None:
        """get_instance returns the same instance."""
        instance1 = PassRegistry.get_instance()
        instance2 = PassRegistry.get_instance()
        assert instance1 is instance2

    def test_reset_instance_clears_singleton(self) -> None:
        """reset_instance clears the singleton."""
        instance1 = PassRegistry.get_instance()
        PassRegistry.reset_instance()
        instance2 = PassRegistry.get_instance()
        assert instance1 is not instance2


class TestPassRegistryGetPass:
    """Tests for get_pass method."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset singleton before each test."""
        PassRegistry.reset_instance()

    @pytest.fixture
    def registry(self) -> PassRegistry:
        """Create a registry instance."""
        return PassRegistry.get_instance()

    def test_get_pass_project(self, registry: PassRegistry) -> None:
        """get_pass returns ProjectPlannerPass for PROJECT."""
        result = registry.get_pass(CompilerPassType.PROJECT)
        assert isinstance(result, ProjectPlannerPass)

    def test_get_pass_architecture(self, registry: PassRegistry) -> None:
        """get_pass returns ArchitecturePlannerPass for ARCHITECTURE."""
        result = registry.get_pass(CompilerPassType.ARCHITECTURE)
        assert isinstance(result, ArchitecturePlannerPass)

    def test_get_pass_scaffold(self, registry: PassRegistry) -> None:
        """get_pass returns ScaffoldPlannerPass for SCAFFOLD."""
        result = registry.get_pass(CompilerPassType.SCAFFOLD)
        assert isinstance(result, ScaffoldPlannerPass)

    def test_get_pass_test(self, registry: PassRegistry) -> None:
        """get_pass returns TestDesignerPass for TEST."""
        result = registry.get_pass(CompilerPassType.TEST)
        assert isinstance(result, TestDesignerPass)

    def test_get_pass_implementation(self, registry: PassRegistry) -> None:
        """get_pass returns ImplementationPlannerPass for IMPLEMENTATION."""
        result = registry.get_pass(CompilerPassType.IMPLEMENTATION)
        assert isinstance(result, ImplementationPlannerPass)

    def test_get_pass_refactor(self, registry: PassRegistry) -> None:
        """get_pass returns RefactorPlannerPass for REFACTOR."""
        result = registry.get_pass(CompilerPassType.REFACTOR)
        assert isinstance(result, RefactorPlannerPass)

    def test_get_pass_returns_new_instance(self, registry: PassRegistry) -> None:
        """get_pass returns a new instance each time."""
        pass1 = registry.get_pass(CompilerPassType.PROJECT)
        pass2 = registry.get_pass(CompilerPassType.PROJECT)
        assert pass1 is not pass2

    def test_all_passes_are_compiler_pass_subclasses(
        self, registry: PassRegistry
    ) -> None:
        """All registered passes are CompilerPass subclasses."""
        for pass_type in CompilerPassType:
            result = registry.get_pass(pass_type)
            assert isinstance(result, CompilerPass)


class TestPassRegistryGetPassClass:
    """Tests for get_pass_class method."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset singleton before each test."""
        PassRegistry.reset_instance()

    @pytest.fixture
    def registry(self) -> PassRegistry:
        """Create a registry instance."""
        return PassRegistry.get_instance()

    def test_get_pass_class_project(self, registry: PassRegistry) -> None:
        """get_pass_class returns ProjectPlannerPass class."""
        result = registry.get_pass_class(CompilerPassType.PROJECT)
        assert result is ProjectPlannerPass

    def test_get_pass_class_architecture(self, registry: PassRegistry) -> None:
        """get_pass_class returns ArchitecturePlannerPass class."""
        result = registry.get_pass_class(CompilerPassType.ARCHITECTURE)
        assert result is ArchitecturePlannerPass


class TestPassRegistryListPasses:
    """Tests for list_passes method."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset singleton before each test."""
        PassRegistry.reset_instance()

    @pytest.fixture
    def registry(self) -> PassRegistry:
        """Create a registry instance."""
        return PassRegistry.get_instance()

    def test_list_passes_returns_all_types(self, registry: PassRegistry) -> None:
        """list_passes returns all registered pass types."""
        result = registry.list_passes()
        assert len(result) == 6

    def test_list_passes_includes_all_pass_types(
        self, registry: PassRegistry
    ) -> None:
        """list_passes includes all CompilerPassType values."""
        result = registry.list_passes()
        for pass_type in CompilerPassType:
            assert pass_type in result


class TestPassNotFoundError:
    """Tests for PassNotFoundError."""

    def test_error_stores_pass_type(self) -> None:
        """PassNotFoundError stores the pass type."""
        error = PassNotFoundError(CompilerPassType.PROJECT)
        assert error.pass_type == CompilerPassType.PROJECT

    def test_error_message_includes_type(self) -> None:
        """PassNotFoundError message includes pass type."""
        error = PassNotFoundError(CompilerPassType.PROJECT)
        assert "project" in str(error).lower()


class TestGetPassConvenienceFunction:
    """Tests for the get_pass convenience function."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset singleton before each test."""
        PassRegistry.reset_instance()

    def test_get_pass_returns_correct_pass(self) -> None:
        """get_pass returns correct pass type."""
        result = get_pass(CompilerPassType.PROJECT)
        assert isinstance(result, ProjectPlannerPass)

    def test_get_pass_uses_singleton(self) -> None:
        """get_pass uses the singleton registry."""
        # First call creates registry
        get_pass(CompilerPassType.PROJECT)
        # Second call should use same registry
        result = get_pass(CompilerPassType.ARCHITECTURE)
        assert isinstance(result, ArchitecturePlannerPass)
