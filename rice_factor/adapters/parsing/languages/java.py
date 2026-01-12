"""Java language extractor for tree-sitter.

Handles Java-specific syntax including:
- Class, interface, enum, and record definitions
- Method declarations with modifiers
- Import statements (single and wildcard)
- Package-private default visibility
"""

from typing import TYPE_CHECKING

from rice_factor.adapters.parsing.languages.base import LanguageExtractor
from rice_factor.domain.ports.ast import (
    ImportInfo,
    ParameterInfo,
    SymbolInfo,
    SymbolKind,
    Visibility,
)

if TYPE_CHECKING:
    import tree_sitter


class JavaExtractor(LanguageExtractor):
    """Tree-sitter extractor for Java."""

    language_id = "java"
    treesitter_language = "java"

    symbol_kind_map = {
        "class_declaration": SymbolKind.CLASS,
        "interface_declaration": SymbolKind.INTERFACE,
        "enum_declaration": SymbolKind.ENUM,
        "record_declaration": SymbolKind.CLASS,
        "method_declaration": SymbolKind.METHOD,
        "constructor_declaration": SymbolKind.METHOD,
    }

    visibility_keywords = {
        "public": Visibility.PUBLIC,
        "private": Visibility.PRIVATE,
        "protected": Visibility.PROTECTED,
    }

    def get_class_query(self) -> str:
        """Return query for Java type declarations."""
        return """
        [
          (class_declaration
            (modifiers)? @modifiers
            name: (identifier) @name
            type_parameters: (type_parameters)? @generics) @class

          (interface_declaration
            (modifiers)? @modifiers
            name: (identifier) @name
            type_parameters: (type_parameters)? @generics) @interface

          (enum_declaration
            (modifiers)? @modifiers
            name: (identifier) @name) @enum

          (record_declaration
            (modifiers)? @modifiers
            name: (identifier) @name
            type_parameters: (type_parameters)? @generics) @record
        ]
        """

    def get_method_query(self) -> str:
        """Return query for Java methods and constructors."""
        return """
        [
          (method_declaration
            (modifiers)? @modifiers
            type: (_)? @return_type
            name: (identifier) @name
            parameters: (formal_parameters) @params) @method

          (constructor_declaration
            (modifiers)? @modifiers
            name: (identifier) @name
            parameters: (formal_parameters) @params) @constructor
        ]
        """

    def get_import_query(self) -> str:
        """Return query for Java import statements."""
        return """
        (import_declaration
          (scoped_identifier) @module
          (asterisk)? @wildcard) @import
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a Java AST match."""
        # Get name
        name_nodes = captures.get("name", [])
        if not name_nodes:
            return None
        name = self.get_node_text(name_nodes[0], source)

        # Determine kind
        if "class" in captures:
            kind = SymbolKind.CLASS
        elif "interface" in captures:
            kind = SymbolKind.INTERFACE
        elif "enum" in captures:
            kind = SymbolKind.ENUM
        elif "record" in captures:
            kind = SymbolKind.CLASS
        elif "method" in captures or "constructor" in captures:
            kind = SymbolKind.METHOD

        # Get main node for position
        main_node = node
        for capture_name in [
            "class",
            "interface",
            "enum",
            "record",
            "method",
            "constructor",
        ]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Determine visibility
        visibility = self._get_java_visibility(
            captures.get("modifiers", []), source
        )

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_java_params(captures["params"][0], source)

        # Extract return type
        return_type = None
        if "return_type" in captures:
            return_type = self.get_node_text(captures["return_type"][0], source)

        # Extract generic parameters
        generics: list[str] = []
        if "generics" in captures:
            generics = self._extract_java_generics(captures["generics"][0], source)

        # Find parent class
        parent_name = self.find_parent_class(main_node, source)

        # Extract modifiers
        modifiers = self._get_java_modifiers(
            captures.get("modifiers", []), source
        )

        # Build signature
        signature = self.build_signature(name, params, return_type)

        return SymbolInfo(
            name=name,
            kind=kind,
            visibility=visibility,
            line_start=main_node.start_point[0] + 1,
            line_end=main_node.end_point[0] + 1,
            column_start=main_node.start_point[1],
            column_end=main_node.end_point[1],
            signature=signature,
            return_type=return_type,
            parameters=params,
            modifiers=modifiers,
            parent_name=parent_name,
            docstring=self.get_docstring(main_node, source),
            generic_params=generics,
        )

    def extract_import_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
    ) -> ImportInfo | None:
        """Extract import information from a Java AST match."""
        module_nodes = captures.get("module", [])
        if not module_nodes:
            return None

        module = self.get_node_text(module_nodes[0], source)

        # Check for static import
        main_node = captures.get("import", [node])[0]
        import_text = self.get_node_text(main_node, source)
        # Note: is_static could be used in the future to distinguish static imports
        _ = "static" in import_text.split()

        # Check for wildcard
        is_wildcard = "wildcard" in captures

        # Extract specific symbol if not wildcard
        symbols: list[str] = []
        if not is_wildcard and "." in module:
            # Last part is the symbol
            parts = module.split(".")
            symbols = [parts[-1]]
            module = ".".join(parts[:-1])

        return ImportInfo(
            module=module,
            symbols=symbols,
            line=main_node.start_point[0] + 1,
            is_relative=False,
            alias=None,
            is_wildcard=is_wildcard,
        )

    def _get_java_visibility(
        self,
        modifier_nodes: list["tree_sitter.Node"],
        source: bytes,
    ) -> Visibility:
        """Get Java visibility from modifiers.

        Default is package-private if no modifier.
        """
        for mod_node in modifier_nodes:
            mod_text = self.get_node_text(mod_node, source)
            for keyword in ("public", "private", "protected"):
                if keyword in mod_text:
                    return self.visibility_keywords[keyword]
        return Visibility.PACKAGE  # Package-private is default

    def _extract_java_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract Java method parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type == "formal_parameter":
                name = ""
                type_annotation = None
                is_variadic = False

                for param_child in child.children:
                    if param_child.type == "identifier":
                        name = self.get_node_text(param_child, source)
                    elif param_child.type in (
                        "type_identifier",
                        "generic_type",
                        "array_type",
                        "integral_type",
                        "floating_point_type",
                        "boolean_type",
                        "void_type",
                        "scoped_type_identifier",
                    ):
                        type_annotation = self.get_node_text(param_child, source)
                    elif param_child.type == "...":
                        is_variadic = True

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            type_annotation=type_annotation,
                            is_variadic=is_variadic,
                        )
                    )

            elif child.type == "spread_parameter":
                name = ""
                type_annotation = None
                for param_child in child.children:
                    if param_child.type == "identifier":
                        name = self.get_node_text(param_child, source)
                    elif param_child.type not in ("...", "modifiers"):
                        type_annotation = self.get_node_text(param_child, source)

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            type_annotation=type_annotation,
                            is_variadic=True,
                        )
                    )

        return params

    def _extract_java_generics(
        self,
        generics_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract generic type parameters."""
        generics: list[str] = []
        for child in generics_node.children:
            if child.type == "type_parameter":
                for gc in child.children:
                    if gc.type == "type_identifier":
                        generics.append(self.get_node_text(gc, source))
                        break
        return generics

    def _get_java_modifiers(
        self,
        modifier_nodes: list["tree_sitter.Node"],
        source: bytes,
    ) -> list[str]:
        """Extract Java modifiers (static, abstract, final, etc)."""
        modifiers: list[str] = []
        for mod_node in modifier_nodes:
            mod_text = self.get_node_text(mod_node, source)
            for keyword in (
                "static",
                "abstract",
                "final",
                "synchronized",
                "native",
                "strictfp",
                "default",
            ):
                if keyword in mod_text:
                    modifiers.append(keyword)
        return modifiers

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """Java default visibility is package-private."""
        return Visibility.PACKAGE

    def find_parent_class(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> str | None:
        """Find the name of the containing class."""
        parent = node.parent
        while parent:
            if parent.type in (
                "class_declaration",
                "interface_declaration",
                "enum_declaration",
                "record_declaration",
            ):
                for child in parent.children:
                    if child.type == "identifier":
                        return self.get_node_text(child, source)
            parent = parent.parent
        return None
