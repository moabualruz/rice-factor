"""Unit tests for CapabilityService."""


from rice_factor.domain.artifacts.payloads.refactor_plan import (
    RefactorOperation,
    RefactorOperationType,
    RefactorPlanPayload,
)
from rice_factor.domain.services.capability_service import (
    CAPABILITY_MATRIX,
    CapabilityService,
)


class TestCapabilityServiceInitialization:
    """Tests for CapabilityService initialization."""

    def test_initialization_with_language(self) -> None:
        """Service should initialize with specified language."""
        service = CapabilityService(language="python")
        assert service.language == "python"

    def test_initialization_normalizes_language(self) -> None:
        """Service should normalize language to lowercase."""
        service = CapabilityService(language="Python")
        assert service.language == "python"

    def test_initialization_default_language(self) -> None:
        """Service should default to python."""
        service = CapabilityService()
        assert service.language == "python"


class TestIsOperationSupported:
    """Tests for is_operation_supported method."""

    def test_move_file_supported_for_python(self) -> None:
        """MOVE_FILE should be supported for python."""
        service = CapabilityService(language="python")
        assert service.is_operation_supported(RefactorOperationType.MOVE_FILE) is True

    def test_rename_symbol_supported_for_python(self) -> None:
        """RENAME_SYMBOL should be supported for python."""
        service = CapabilityService(language="python")
        assert service.is_operation_supported(RefactorOperationType.RENAME_SYMBOL) is True

    def test_extract_interface_supported_for_python(self) -> None:
        """EXTRACT_INTERFACE should be supported for python."""
        service = CapabilityService(language="python")
        assert service.is_operation_supported(RefactorOperationType.EXTRACT_INTERFACE) is True

    def test_enforce_dependency_supported_for_python(self) -> None:
        """ENFORCE_DEPENDENCY should be supported for python."""
        service = CapabilityService(language="python")
        assert service.is_operation_supported(RefactorOperationType.ENFORCE_DEPENDENCY) is True

    def test_extract_interface_not_supported_for_go(self) -> None:
        """EXTRACT_INTERFACE should not be supported for go."""
        service = CapabilityService(language="go")
        assert service.is_operation_supported(RefactorOperationType.EXTRACT_INTERFACE) is False

    def test_unsupported_language_returns_false(self) -> None:
        """Unknown language should return False for all operations."""
        service = CapabilityService(language="cobol")
        assert service.is_operation_supported(RefactorOperationType.MOVE_FILE) is False


class TestGetSupportedOperations:
    """Tests for get_supported_operations method."""

    def test_returns_all_for_python(self) -> None:
        """Python should support all operations."""
        service = CapabilityService(language="python")
        supported = service.get_supported_operations()

        assert RefactorOperationType.MOVE_FILE in supported
        assert RefactorOperationType.RENAME_SYMBOL in supported
        assert RefactorOperationType.EXTRACT_INTERFACE in supported
        assert RefactorOperationType.ENFORCE_DEPENDENCY in supported

    def test_returns_subset_for_go(self) -> None:
        """Go should support a subset of operations."""
        service = CapabilityService(language="go")
        supported = service.get_supported_operations()

        assert RefactorOperationType.MOVE_FILE in supported
        assert RefactorOperationType.RENAME_SYMBOL in supported
        assert RefactorOperationType.EXTRACT_INTERFACE not in supported

    def test_returns_empty_for_unknown_language(self) -> None:
        """Unknown language should return empty set."""
        service = CapabilityService(language="unknown")
        supported = service.get_supported_operations()

        assert len(supported) == 0


class TestGetUnsupportedOperations:
    """Tests for get_unsupported_operations method."""

    def test_returns_empty_for_all_supported(self) -> None:
        """Should return empty list when all operations are supported."""
        service = CapabilityService(language="python")

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.MOVE_FILE),
                RefactorOperation(type=RefactorOperationType.RENAME_SYMBOL),
            ],
        )

        unsupported = service.get_unsupported_operations(plan)
        assert len(unsupported) == 0

    def test_returns_unsupported_operations(self) -> None:
        """Should return list of unsupported operations."""
        service = CapabilityService(language="go")

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.MOVE_FILE),
                RefactorOperation(type=RefactorOperationType.EXTRACT_INTERFACE),
            ],
        )

        unsupported = service.get_unsupported_operations(plan)
        assert len(unsupported) == 1
        assert RefactorOperationType.EXTRACT_INTERFACE in unsupported

    def test_deduplicates_unsupported(self) -> None:
        """Should not return duplicate unsupported operations."""
        service = CapabilityService(language="go")

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.EXTRACT_INTERFACE),
                RefactorOperation(type=RefactorOperationType.EXTRACT_INTERFACE),
            ],
        )

        unsupported = service.get_unsupported_operations(plan)
        assert len(unsupported) == 1


class TestCheckCapabilities:
    """Tests for check_capabilities method."""

    def test_returns_true_when_all_supported(self) -> None:
        """Should return True when all operations are supported."""
        service = CapabilityService(language="python")

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.MOVE_FILE),
            ],
        )

        assert service.check_capabilities(plan) is True

    def test_returns_false_when_unsupported(self) -> None:
        """Should return False when some operations are unsupported."""
        service = CapabilityService(language="go")

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.EXTRACT_INTERFACE),
            ],
        )

        assert service.check_capabilities(plan) is False


class TestGetCapabilitySummary:
    """Tests for get_capability_summary method."""

    def test_returns_summary_dict(self) -> None:
        """Should return dict mapping operations to support status."""
        service = CapabilityService(language="go")

        plan = RefactorPlanPayload(
            goal="Test refactoring",
            operations=[
                RefactorOperation(type=RefactorOperationType.MOVE_FILE),
                RefactorOperation(type=RefactorOperationType.EXTRACT_INTERFACE),
            ],
        )

        summary = service.get_capability_summary(plan)

        assert summary[RefactorOperationType.MOVE_FILE] is True
        assert summary[RefactorOperationType.EXTRACT_INTERFACE] is False


class TestCapabilityMatrix:
    """Tests for the capability matrix."""

    def test_python_has_all_operations(self) -> None:
        """Python should support all operation types."""
        assert len(CAPABILITY_MATRIX["python"]) == 4

    def test_matrix_contains_expected_languages(self) -> None:
        """Matrix should contain expected languages."""
        expected = ["python", "rust", "go", "java", "typescript", "javascript"]
        for lang in expected:
            assert lang in CAPABILITY_MATRIX
