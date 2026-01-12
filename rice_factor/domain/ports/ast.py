"""AST parsing port for language-agnostic code analysis.

This module defines the protocol for AST (Abstract Syntax Tree) parsing
that provides structural information about source code without requiring
language servers or external tools.

The ASTPort is designed to be implemented by tree-sitter for most languages,
while Python can use its native ast module.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class SymbolKind(str, Enum):
    """Kinds of symbols that can be extracted from source code."""

    CLASS = "class"
    INTERFACE = "interface"
    TRAIT = "trait"  # Rust traits, PHP traits
    STRUCT = "struct"  # Go, Rust structs
    ENUM = "enum"
    METHOD = "method"
    FUNCTION = "function"
    FIELD = "field"
    PROPERTY = "property"
    CONSTANT = "constant"
    IMPORT = "import"
    MODULE = "module"
    PACKAGE = "package"
    TYPE_ALIAS = "type_alias"


class Visibility(str, Enum):
    """Visibility modifiers for symbols."""

    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"  # C#, Kotlin
    PACKAGE = "package"  # Java package-private, Go unexported


@dataclass
class ParameterInfo:
    """Information about a function/method parameter.

    Attributes:
        name: Parameter name.
        type_annotation: Type annotation if present.
        default_value: Default value expression if present.
        is_variadic: True for *args, **kwargs, ...rest patterns.
        is_optional: True for optional parameters.
    """

    name: str
    type_annotation: str | None = None
    default_value: str | None = None
    is_variadic: bool = False
    is_optional: bool = False


@dataclass
class SymbolInfo:
    """Information about a code symbol (class, method, function, etc).

    Attributes:
        name: Symbol name.
        kind: Type of symbol (class, method, etc).
        visibility: Access modifier (public, private, etc).
        line_start: Starting line (1-indexed).
        line_end: Ending line (1-indexed).
        column_start: Starting column (0-indexed).
        column_end: Ending column (0-indexed).
        signature: Full signature for methods/functions.
        return_type: Return type annotation if present.
        parameters: List of parameters for methods/functions.
        modifiers: Additional modifiers (async, static, abstract, etc).
        parent_name: Name of containing class/struct/module.
        docstring: Documentation comment if present.
        generic_params: Generic type parameters if present.
    """

    name: str
    kind: SymbolKind
    visibility: Visibility
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    signature: str | None = None
    return_type: str | None = None
    parameters: list[ParameterInfo] = field(default_factory=list)
    modifiers: list[str] = field(default_factory=list)
    parent_name: str | None = None
    docstring: str | None = None
    generic_params: list[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Information about an import statement.

    Attributes:
        module: Module/package path being imported.
        symbols: Specific symbols imported (empty for whole module).
        line: Line number of the import statement.
        is_relative: True for relative imports (., ..).
        alias: Import alias if present (import X as Y).
        is_wildcard: True for wildcard imports (import *).
    """

    module: str
    symbols: list[str] = field(default_factory=list)
    line: int = 0
    is_relative: bool = False
    alias: str | None = None
    is_wildcard: bool = False


@dataclass
class ParseResult:
    """Result of parsing a source file.

    Attributes:
        success: Whether parsing succeeded.
        symbols: List of symbols found in the file.
        imports: List of import statements.
        errors: List of error messages if parsing failed.
        language: Detected language identifier.
        has_syntax_errors: True if file has syntax errors but was partially parsed.
        file_path: Path to the parsed file.
    """

    success: bool
    symbols: list[SymbolInfo]
    imports: list[ImportInfo]
    errors: list[str]
    language: str
    has_syntax_errors: bool = False
    file_path: str | None = None


class ASTPort(ABC):
    """Port for AST parsing operations.

    Provides language-agnostic interface for extracting structural
    information from source code. This is used for:
    - extract_interface: Extract method signatures from classes
    - enforce_dependency: Analyze import statements

    Implementations:
    - TreeSitterAdapter: Uses tree-sitter for most languages
    - Python's native ast module: Used for Python (via RopeAdapter)
    """

    @abstractmethod
    def parse_file(
        self,
        file_path: str,
        content: str | None = None,
    ) -> ParseResult:
        """Parse a source file and extract structural information.

        Args:
            file_path: Path to the file (used for language detection).
            content: Optional file content. If None, reads from file_path.

        Returns:
            ParseResult containing symbols, imports, and any errors.
        """
        ...

    @abstractmethod
    def get_methods(
        self,
        file_path: str,
        class_name: str | None = None,
        visibility: Visibility | None = None,
        content: str | None = None,
    ) -> list[SymbolInfo]:
        """Extract method/function signatures from a file.

        Args:
            file_path: Path to the source file.
            class_name: Optional class name to filter methods.
            visibility: Optional visibility filter (default: public only).
            content: Optional file content.

        Returns:
            List of SymbolInfo for matching methods/functions.
        """
        ...

    @abstractmethod
    def get_imports(
        self,
        file_path: str,
        content: str | None = None,
    ) -> list[ImportInfo]:
        """Extract import statements from a file.

        Args:
            file_path: Path to the source file.
            content: Optional file content.

        Returns:
            List of ImportInfo for all imports in the file.
        """
        ...

    @abstractmethod
    def find_symbol(
        self,
        file_path: str,
        symbol_name: str,
        line: int | None = None,
        content: str | None = None,
    ) -> SymbolInfo | None:
        """Find a symbol by name in a file.

        Args:
            file_path: Path to the source file.
            symbol_name: Name of the symbol to find.
            line: Optional line number to disambiguate.
            content: Optional file content.

        Returns:
            SymbolInfo if found, None otherwise.
        """
        ...

    @abstractmethod
    def get_classes(
        self,
        file_path: str,
        content: str | None = None,
    ) -> list[SymbolInfo]:
        """Extract class/struct/interface definitions from a file.

        Args:
            file_path: Path to the source file.
            content: Optional file content.

        Returns:
            List of SymbolInfo for classes, structs, interfaces, traits.
        """
        ...

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """Return list of supported language identifiers.

        Returns:
            List of language identifiers (e.g., ["go", "rust", "java"]).
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AST parser is available.

        Returns:
            True if the parser can be used, False otherwise.
        """
        ...

    def supports_language(self, language: str) -> bool:
        """Check if a specific language is supported.

        Args:
            language: Language identifier to check.

        Returns:
            True if the language is supported.
        """
        return language.lower() in [lang.lower() for lang in self.get_supported_languages()]

    def detect_language(self, file_path: str) -> str | None:
        """Detect language from file extension.

        Args:
            file_path: Path to the file.

        Returns:
            Language identifier or None if unknown.
        """
        from pathlib import Path

        ext = Path(file_path).suffix.lower()
        ext_to_lang: dict[str, str] = {
            ".py": "python",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".kt": "kotlin",
            ".kts": "kotlin",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".rb": "ruby",
            ".cs": "csharp",
            ".php": "php",
        }
        return ext_to_lang.get(ext)
