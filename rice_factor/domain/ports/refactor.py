"""Refactoring tool port for language-specific refactoring adapters.

This module defines the protocol for refactoring tools that can perform
language-aware code transformations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class RefactorOperation(str, Enum):
    """Supported refactoring operations."""

    RENAME = "rename"
    EXTRACT_METHOD = "extract_method"
    EXTRACT_VARIABLE = "extract_variable"
    EXTRACT_INTERFACE = "extract_interface"
    INLINE = "inline"
    MOVE = "move"
    CHANGE_SIGNATURE = "change_signature"
    ADD_PARAMETER = "add_parameter"
    REMOVE_PARAMETER = "remove_parameter"
    ENFORCE_DEPENDENCY = "enforce_dependency"


@dataclass
class RefactorRequest:
    """Request for a refactoring operation.

    Attributes:
        operation: The type of refactoring operation to perform.
        target: Symbol or file path to refactor.
        new_value: New name or value (for rename, move operations).
        parameters: Operation-specific parameters.
        file_path: Optional specific file to operate on.
        line: Optional line number for position-based operations.
        column: Optional column number for position-based operations.
        interface_name: Name for extracted interface (EXTRACT_INTERFACE operation).
        dependency_rules: Dependency rules for ENFORCE_DEPENDENCY operation.
            Format: {"forbidden": ["pkg1", "pkg2"], "allowed": ["pkg3"]}.
    """

    operation: RefactorOperation
    target: str
    new_value: str | None = None
    parameters: dict[str, str] | None = None
    file_path: str | None = None
    line: int | None = None
    column: int | None = None
    interface_name: str | None = None
    dependency_rules: dict[str, list[str]] | None = None


@dataclass
class RefactorChange:
    """A single change resulting from a refactoring operation.

    Attributes:
        file_path: Path to the file that was changed.
        original_content: Original content before the change.
        new_content: New content after the change.
        description: Human-readable description of the change.
        line_start: Starting line of the change (1-indexed).
        line_end: Ending line of the change (1-indexed).
    """

    file_path: str
    original_content: str
    new_content: str
    description: str
    line_start: int | None = None
    line_end: int | None = None


@dataclass
class RefactorResult:
    """Result of a refactoring operation.

    Attributes:
        success: Whether the refactoring succeeded.
        changes: List of changes made (or to be made in dry-run mode).
        errors: List of error messages if any.
        warnings: List of warning messages.
        tool_used: Name of the tool that performed the refactoring.
        dry_run: Whether this was a dry-run (preview only).
    """

    success: bool
    changes: list[RefactorChange]
    errors: list[str]
    tool_used: str
    dry_run: bool
    warnings: list[str] = field(default_factory=list)


@dataclass
class ToolCapability:
    """Capability of a refactoring tool.

    Attributes:
        tool_name: Name of the tool.
        languages: List of supported language identifiers.
        operations: List of supported refactoring operations.
        is_available: Whether the tool is currently available.
        version: Tool version if available.
    """

    tool_name: str
    languages: list[str]
    operations: list[RefactorOperation]
    is_available: bool
    version: str | None = None


class RefactorToolPort(ABC):
    """Port for language-specific refactoring tools.

    This abstract base class defines the interface for refactoring tool
    adapters. Each adapter implements this interface for a specific
    language ecosystem (e.g., OpenRewrite for JVM, gopls for Go).
    """

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """Return list of supported language identifiers.

        Returns:
            List of language identifiers (e.g., ["java", "kotlin"]).
        """
        ...

    @abstractmethod
    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return list of supported refactoring operations.

        Returns:
            List of RefactorOperation enums that this tool supports.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool is installed and usable.

        This method should check for the presence of required binaries,
        configuration files, or other dependencies.

        Returns:
            True if the tool can be used, False otherwise.
        """
        ...

    @abstractmethod
    def get_version(self) -> str | None:
        """Get the version of the tool if available.

        Returns:
            Version string or None if not available.
        """
        ...

    @abstractmethod
    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute a refactoring operation.

        Args:
            request: The refactoring request specifying what to do.
            dry_run: If True, only preview changes without applying them.

        Returns:
            RefactorResult containing the outcome and any changes.
        """
        ...

    @abstractmethod
    def rollback(self, result: RefactorResult) -> bool:
        """Rollback a previously applied refactoring.

        This method should restore files to their state before the
        refactoring was applied. Typically uses git checkout.

        Args:
            result: The result from a previous execute() call.

        Returns:
            True if rollback succeeded, False otherwise.
        """
        ...

    def get_capability(self) -> ToolCapability:
        """Get the capability descriptor for this tool.

        Returns:
            ToolCapability describing what this tool can do.
        """
        return ToolCapability(
            tool_name=self.__class__.__name__,
            languages=self.get_supported_languages(),
            operations=self.get_supported_operations(),
            is_available=self.is_available(),
            version=self.get_version(),
        )
