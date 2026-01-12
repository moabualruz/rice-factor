"""Base class for language-specific tree-sitter extractors.

Each language extractor provides:
- Tree-sitter queries for extracting symbols and imports
- Language-specific visibility detection
- Language-specific modifier handling
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from rice_factor.domain.ports.ast import (
    ImportInfo,
    ParameterInfo,
    SymbolInfo,
    SymbolKind,
    Visibility,
)

if TYPE_CHECKING:
    import tree_sitter


@dataclass
class QueryMatch:
    """Result of a tree-sitter query match.

    Attributes:
        node: The matched tree-sitter node.
        captures: Dictionary of capture name to node.
    """

    node: "tree_sitter.Node"
    captures: dict[str, "tree_sitter.Node"] = field(default_factory=dict)


class LanguageExtractor(ABC):
    """Base class for language-specific tree-sitter extractors.

    Subclasses must implement:
    - get_class_query(): Query to find classes/structs/interfaces
    - get_method_query(): Query to find methods/functions
    - get_import_query(): Query to find imports
    - extract_symbol_from_match(): Convert match to SymbolInfo
    - extract_import_from_match(): Convert match to ImportInfo
    """

    # Class attribute: language identifier for tree-sitter
    language_id: str = ""

    # Class attribute: tree-sitter language name
    treesitter_language: str = ""

    # Common node type mappings to SymbolKind
    symbol_kind_map: ClassVar[dict[str, SymbolKind]] = {}

    # Common visibility patterns
    visibility_keywords: ClassVar[dict[str, Visibility]] = {
        "public": Visibility.PUBLIC,
        "private": Visibility.PRIVATE,
        "protected": Visibility.PROTECTED,
        "internal": Visibility.INTERNAL,
    }

    @abstractmethod
    def get_class_query(self) -> str:
        """Return tree-sitter query to find class/struct/interface definitions.

        The query should capture:
        - @name: The identifier/name of the class
        - @class (optional): The whole class node
        - @modifiers (optional): Modifier nodes

        Returns:
            Tree-sitter query string.
        """
        ...

    @abstractmethod
    def get_method_query(self) -> str:
        """Return tree-sitter query to find method/function definitions.

        The query should capture:
        - @name: The identifier/name of the method
        - @method (optional): The whole method node
        - @params (optional): Parameter list node
        - @return_type (optional): Return type node
        - @modifiers (optional): Modifier nodes

        Returns:
            Tree-sitter query string.
        """
        ...

    @abstractmethod
    def get_import_query(self) -> str:
        """Return tree-sitter query to find import statements.

        The query should capture:
        - @module: The module/package path
        - @import (optional): The whole import statement
        - @symbols (optional): Imported symbols (for selective imports)
        - @alias (optional): Import alias

        Returns:
            Tree-sitter query string.
        """
        ...

    @abstractmethod
    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a query match.

        Args:
            node: The matched node.
            captures: Dictionary of capture names to matched nodes.
            source: Source code bytes.
            kind: The kind of symbol being extracted.

        Returns:
            SymbolInfo or None if extraction failed.
        """
        ...

    @abstractmethod
    def extract_import_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
    ) -> ImportInfo | None:
        """Extract import information from a query match.

        Args:
            node: The matched node.
            captures: Dictionary of capture names to matched nodes.
            source: Source code bytes.

        Returns:
            ImportInfo or None if extraction failed.
        """
        ...

    def get_node_text(self, node: "tree_sitter.Node", source: bytes) -> str:
        """Get text content of a node.

        Args:
            node: The tree-sitter node.
            source: Source code bytes.

        Returns:
            Text content as string.
        """
        return source[node.start_byte : node.end_byte].decode("utf-8")

    def get_visibility(
        self,
        node: "tree_sitter.Node",
        modifiers: list["tree_sitter.Node"] | None,
        source: bytes,
    ) -> Visibility:
        """Determine visibility from modifiers.

        Default implementation checks for common visibility keywords.
        Override in subclasses for language-specific rules.

        Args:
            node: The symbol node.
            modifiers: List of modifier nodes.
            source: Source code bytes.

        Returns:
            Visibility level.
        """
        if not modifiers:
            return self.get_default_visibility(node)

        for mod in modifiers:
            mod_text = self.get_node_text(mod, source).lower()
            if mod_text in self.visibility_keywords:
                return self.visibility_keywords[mod_text]

        return self.get_default_visibility(node)

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """Get default visibility when no modifier is present.

        Override in subclasses for language-specific defaults.
        - Java: package-private
        - Go: public if starts with uppercase
        - Python: public (convention-based)

        Args:
            node: The symbol node.

        Returns:
            Default visibility for the language.
        """
        return Visibility.PUBLIC

    def extract_parameters(
        self,
        params_node: "tree_sitter.Node | None",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract parameters from a parameter list node.

        Default implementation handles common patterns.
        Override for language-specific parameter syntax.

        Args:
            params_node: The parameter list node.
            source: Source code bytes.

        Returns:
            List of ParameterInfo.
        """
        if not params_node:
            return []

        params: list[ParameterInfo] = []
        # Default implementation - subclasses should override
        return params

    def build_signature(
        self,
        name: str,
        params: list[ParameterInfo],
        return_type: str | None,
    ) -> str:
        """Build a method signature string.

        Args:
            name: Method name.
            params: List of parameters.
            return_type: Return type if any.

        Returns:
            Formatted signature string.
        """
        param_strs = []
        for p in params:
            s = p.name
            if p.type_annotation:
                s = f"{p.name}: {p.type_annotation}"
            if p.default_value:
                s = f"{s} = {p.default_value}"
            param_strs.append(s)

        sig = f"{name}({', '.join(param_strs)})"
        if return_type:
            sig = f"{sig} -> {return_type}"
        return sig

    def find_parent_class(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> str | None:
        """Find the name of the containing class/struct.

        Args:
            node: The symbol node.
            source: Source code bytes.

        Returns:
            Parent class name or None.
        """
        parent = node.parent
        while parent:
            if parent.type in self.symbol_kind_map:
                kind = self.symbol_kind_map[parent.type]
                if kind in (
                    SymbolKind.CLASS,
                    SymbolKind.STRUCT,
                    SymbolKind.INTERFACE,
                    SymbolKind.TRAIT,
                ):
                    # Find name child
                    for child in parent.children:
                        if child.type in ("identifier", "name", "type_identifier"):
                            return self.get_node_text(child, source)
            parent = parent.parent
        return None

    def get_modifiers(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract modifiers from a node (async, static, abstract, etc).

        Args:
            node: The symbol node.
            source: Source code bytes.

        Returns:
            List of modifier strings.
        """
        modifiers = []
        # Look for modifier nodes in children or siblings
        for child in node.children:
            if child.type in ("modifiers", "modifier"):
                modifiers.append(self.get_node_text(child, source))
            elif child.type in ("async", "static", "abstract", "final", "const"):
                modifiers.append(child.type)
        return modifiers

    def get_generic_params(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract generic type parameters.

        Args:
            node: The symbol node.
            source: Source code bytes.

        Returns:
            List of generic parameter names.
        """
        generics = []
        for child in node.children:
            if child.type in (
                "type_parameters",
                "generic_parameters",
                "type_params",
            ):
                # Extract individual type params
                for param in child.children:
                    if param.type in (
                        "type_parameter",
                        "type_identifier",
                        "identifier",
                    ):
                        generics.append(self.get_node_text(param, source))
        return generics

    def get_docstring(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> str | None:
        """Extract documentation comment for a node.

        Args:
            node: The symbol node.
            source: Source code bytes.

        Returns:
            Docstring text or None.
        """
        # Look for comment immediately before the node
        prev = node.prev_sibling
        while prev:
            if prev.type in ("comment", "block_comment", "doc_comment"):
                return self.get_node_text(prev, source).strip()
            elif prev.type not in ("newline", "whitespace"):
                break
            prev = prev.prev_sibling
        return None
