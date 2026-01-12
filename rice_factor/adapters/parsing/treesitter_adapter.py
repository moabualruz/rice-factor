"""Tree-sitter based AST parsing adapter.

This adapter uses tree-sitter for language-agnostic AST parsing.
It supports 9 languages via tree-sitter-language-pack:
- Go, Rust, Java, Kotlin, TypeScript, JavaScript, Ruby, C#, PHP

Python uses its native ast module (handled by RopeAdapter).
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from rice_factor.domain.ports.ast import (
    ASTPort,
    ImportInfo,
    ParseResult,
    SymbolInfo,
    SymbolKind,
    Visibility,
)

if TYPE_CHECKING:
    import tree_sitter

    from rice_factor.adapters.parsing.languages.base import LanguageExtractor

logger = logging.getLogger(__name__)


class TreeSitterAdapter(ASTPort):
    """AST parser using tree-sitter.

    Provides language-agnostic AST parsing for extract_interface
    and enforce_dependency operations.

    Attributes:
        _parsers: Cache of tree-sitter parsers by language.
        _extractors: Language-specific extractor instances.
        _available: Whether tree-sitter is available.
    """

    # Language to tree-sitter grammar name mapping
    LANGUAGE_MAP: dict[str, str] = {
        "go": "go",
        "rust": "rust",
        "java": "java",
        "kotlin": "kotlin",
        "typescript": "typescript",
        "javascript": "javascript",
        "ruby": "ruby",
        "csharp": "c_sharp",
        "php": "php",
    }

    # File extension to language mapping
    EXTENSION_MAP: dict[str, str] = {
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".rb": "ruby",
        ".cs": "csharp",
        ".php": "php",
    }

    def __init__(self) -> None:
        """Initialize the tree-sitter adapter."""
        self._parsers: dict[str, tree_sitter.Parser] = {}
        self._extractors: dict[str, LanguageExtractor] = {}
        self._available: bool | None = None
        self._ts_module: object | None = None

    def _get_tree_sitter(self) -> object | None:
        """Get the tree-sitter module.

        Returns:
            tree_sitter module or None if not available.
        """
        if self._ts_module is None:
            try:
                import tree_sitter

                self._ts_module = tree_sitter
            except ImportError:
                logger.warning("tree-sitter not installed")
                return None
        return self._ts_module

    def is_available(self) -> bool:
        """Check if tree-sitter is available.

        Returns:
            True if tree-sitter and language pack are installed.
        """
        if self._available is not None:
            return self._available

        try:
            import tree_sitter  # noqa: F401
            import tree_sitter_language_pack  # noqa: F401

            self._available = True
        except ImportError:
            logger.warning(
                "tree-sitter-language-pack not installed. "
                "Install with: pip install tree-sitter-language-pack"
            )
            self._available = False

        return self._available

    def get_supported_languages(self) -> list[str]:
        """Return list of supported language identifiers.

        Returns:
            List of language identifiers.
        """
        return list(self.LANGUAGE_MAP.keys())

    def _get_parser(self, language: str) -> "tree_sitter.Parser | None":
        """Get or create a parser for the given language.

        Args:
            language: Language identifier.

        Returns:
            Parser instance or None if not available.
        """
        if language in self._parsers:
            return self._parsers[language]

        if not self.is_available():
            return None

        if language not in self.LANGUAGE_MAP:
            logger.warning(f"Unsupported language: {language}")
            return None

        try:
            import tree_sitter
            import tree_sitter_language_pack as ts_pack

            ts_language = self.LANGUAGE_MAP[language]
            lang = ts_pack.get_language(ts_language)
            parser = tree_sitter.Parser(lang)
            self._parsers[language] = parser
            return parser
        except Exception as e:
            logger.error(f"Failed to create parser for {language}: {e}")
            return None

    def _get_extractor(self, language: str) -> "LanguageExtractor | None":
        """Get the extractor for a language.

        Args:
            language: Language identifier.

        Returns:
            LanguageExtractor instance or None.
        """
        if language in self._extractors:
            return self._extractors[language]

        extractor = self._create_extractor(language)
        if extractor:
            self._extractors[language] = extractor
        return extractor

    def _create_extractor(self, language: str) -> "LanguageExtractor | None":
        """Create a language-specific extractor.

        Args:
            language: Language identifier.

        Returns:
            LanguageExtractor instance or None.
        """
        # Import extractors lazily to avoid circular imports
        try:
            if language == "go":
                from rice_factor.adapters.parsing.languages.go import GoExtractor

                return GoExtractor()
            elif language == "rust":
                from rice_factor.adapters.parsing.languages.rust import RustExtractor

                return RustExtractor()
            elif language == "java":
                from rice_factor.adapters.parsing.languages.java import JavaExtractor

                return JavaExtractor()
            elif language == "kotlin":
                from rice_factor.adapters.parsing.languages.kotlin import (
                    KotlinExtractor,
                )

                return KotlinExtractor()
            elif language == "typescript":
                from rice_factor.adapters.parsing.languages.typescript import (
                    TypeScriptExtractor,
                )

                return TypeScriptExtractor()
            elif language == "javascript":
                from rice_factor.adapters.parsing.languages.javascript import (
                    JavaScriptExtractor,
                )

                return JavaScriptExtractor()
            elif language == "ruby":
                from rice_factor.adapters.parsing.languages.ruby import RubyExtractor

                return RubyExtractor()
            elif language == "csharp":
                from rice_factor.adapters.parsing.languages.csharp import (
                    CSharpExtractor,
                )

                return CSharpExtractor()
            elif language == "php":
                from rice_factor.adapters.parsing.languages.php import PHPExtractor

                return PHPExtractor()
        except ImportError as e:
            logger.error(f"Failed to import extractor for {language}: {e}")
        return None

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
        # Detect language
        language = self.detect_language(file_path)
        if not language:
            return ParseResult(
                success=False,
                symbols=[],
                imports=[],
                errors=[f"Unknown language for file: {file_path}"],
                language="unknown",
                file_path=file_path,
            )

        # Get content
        if content is None:
            try:
                content = Path(file_path).read_text(encoding="utf-8")
            except Exception as e:
                return ParseResult(
                    success=False,
                    symbols=[],
                    imports=[],
                    errors=[f"Failed to read file: {e}"],
                    language=language,
                    file_path=file_path,
                )

        # Get parser
        parser = self._get_parser(language)
        if not parser:
            return ParseResult(
                success=False,
                symbols=[],
                imports=[],
                errors=[
                    f"Parser not available for {language}. "
                    "Install tree-sitter-language-pack."
                ],
                language=language,
                file_path=file_path,
            )

        # Get extractor
        extractor = self._get_extractor(language)
        if not extractor:
            return ParseResult(
                success=False,
                symbols=[],
                imports=[],
                errors=[f"No extractor available for {language}"],
                language=language,
                file_path=file_path,
            )

        # Parse
        try:
            source = content.encode("utf-8")
            tree = parser.parse(source)
        except Exception as e:
            return ParseResult(
                success=False,
                symbols=[],
                imports=[],
                errors=[f"Parse error: {e}"],
                language=language,
                file_path=file_path,
            )

        # Check for errors
        has_errors = tree.root_node.has_error

        # Extract symbols and imports
        symbols = self._extract_symbols(tree, extractor, source)
        imports = self._extract_imports(tree, extractor, source)

        return ParseResult(
            success=True,
            symbols=symbols,
            imports=imports,
            errors=[],
            language=language,
            has_syntax_errors=has_errors,
            file_path=file_path,
        )

    def _extract_symbols(
        self,
        tree: "tree_sitter.Tree",
        extractor: "LanguageExtractor",
        source: bytes,
    ) -> list[SymbolInfo]:
        """Extract all symbols from the parse tree.

        Args:
            tree: Parsed tree.
            extractor: Language-specific extractor.
            source: Source code bytes.

        Returns:
            List of extracted symbols.
        """
        symbols: list[SymbolInfo] = []

        # Extract classes
        try:
            import tree_sitter_language_pack as ts_pack

            lang = ts_pack.get_language(
                self.LANGUAGE_MAP.get(extractor.language_id, extractor.language_id)
            )
            class_query = lang.query(extractor.get_class_query())

            for match in class_query.matches(tree.root_node):
                captures: dict[str, list[tree_sitter.Node]] = {}
                for name, node in match[1]:
                    if name not in captures:
                        captures[name] = []
                    captures[name].append(node)

                symbol = extractor.extract_symbol_from_match(
                    match[1][0][1] if match[1] else tree.root_node,
                    captures,
                    source,
                    SymbolKind.CLASS,
                )
                if symbol:
                    symbols.append(symbol)
        except Exception as e:
            logger.debug(f"Error extracting classes: {e}")

        # Extract methods/functions
        try:
            method_query = lang.query(extractor.get_method_query())

            for match in method_query.matches(tree.root_node):
                method_captures: dict[str, list[tree_sitter.Node]] = {}
                for name, node in match[1]:
                    if name not in method_captures:
                        method_captures[name] = []
                    method_captures[name].append(node)

                symbol = extractor.extract_symbol_from_match(
                    match[1][0][1] if match[1] else tree.root_node,
                    method_captures,
                    source,
                    SymbolKind.METHOD,
                )
                if symbol:
                    symbols.append(symbol)
        except Exception as e:
            logger.debug(f"Error extracting methods: {e}")

        return symbols

    def _extract_imports(
        self,
        tree: "tree_sitter.Tree",
        extractor: "LanguageExtractor",
        source: bytes,
    ) -> list[ImportInfo]:
        """Extract all imports from the parse tree.

        Args:
            tree: Parsed tree.
            extractor: Language-specific extractor.
            source: Source code bytes.

        Returns:
            List of extracted imports.
        """
        imports: list[ImportInfo] = []

        try:
            import tree_sitter_language_pack as ts_pack

            lang = ts_pack.get_language(
                self.LANGUAGE_MAP.get(extractor.language_id, extractor.language_id)
            )
            import_query = lang.query(extractor.get_import_query())

            for match in import_query.matches(tree.root_node):
                captures: dict[str, list[tree_sitter.Node]] = {}
                for name, node in match[1]:
                    if name not in captures:
                        captures[name] = []
                    captures[name].append(node)

                imp = extractor.extract_import_from_match(
                    match[1][0][1] if match[1] else tree.root_node,
                    captures,
                    source,
                )
                if imp:
                    imports.append(imp)
        except Exception as e:
            logger.debug(f"Error extracting imports: {e}")

        return imports

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
            visibility: Optional visibility filter.
            content: Optional file content.

        Returns:
            List of SymbolInfo for matching methods/functions.
        """
        result = self.parse_file(file_path, content)
        if not result.success:
            return []

        methods = [
            s
            for s in result.symbols
            if s.kind in (SymbolKind.METHOD, SymbolKind.FUNCTION)
        ]

        if class_name:
            methods = [m for m in methods if m.parent_name == class_name]

        if visibility:
            methods = [m for m in methods if m.visibility == visibility]

        return methods

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
        result = self.parse_file(file_path, content)
        return result.imports

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
        result = self.parse_file(file_path, content)
        if not result.success:
            return None

        for symbol in result.symbols:
            if symbol.name == symbol_name:
                if line is None or symbol.line_start == line:
                    return symbol

        return None

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
        result = self.parse_file(file_path, content)
        if not result.success:
            return []

        return [
            s
            for s in result.symbols
            if s.kind
            in (
                SymbolKind.CLASS,
                SymbolKind.STRUCT,
                SymbolKind.INTERFACE,
                SymbolKind.TRAIT,
            )
        ]
