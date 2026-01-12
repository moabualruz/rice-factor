"""Kotlin language extractor for tree-sitter.

Handles Kotlin-specific syntax including:
- Class, interface, object, and data class definitions
- Function declarations with default parameters
- Import statements
- Visibility modifiers (public, private, internal, protected)
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


class KotlinExtractor(LanguageExtractor):
    """Tree-sitter extractor for Kotlin."""

    language_id = "kotlin"
    treesitter_language = "kotlin"

    symbol_kind_map = {
        "class_declaration": SymbolKind.CLASS,
        "interface_declaration": SymbolKind.INTERFACE,
        "object_declaration": SymbolKind.CLASS,
        "enum_class_body": SymbolKind.ENUM,
        "function_declaration": SymbolKind.METHOD,
    }

    visibility_keywords = {
        "public": Visibility.PUBLIC,
        "private": Visibility.PRIVATE,
        "protected": Visibility.PROTECTED,
        "internal": Visibility.INTERNAL,
    }

    def get_class_query(self) -> str:
        """Return query for Kotlin type declarations."""
        return """
        [
          (class_declaration
            (modifiers)? @modifiers
            (type_identifier) @name
            (type_parameters)? @generics) @class

          (interface_declaration
            (modifiers)? @modifiers
            (type_identifier) @name
            (type_parameters)? @generics) @interface

          (object_declaration
            (modifiers)? @modifiers
            (type_identifier) @name) @object
        ]
        """

    def get_method_query(self) -> str:
        """Return query for Kotlin functions."""
        return """
        (function_declaration
          (modifiers)? @modifiers
          (simple_identifier) @name
          (function_value_parameters) @params
          (type_identifier)? @return_type) @function
        """

    def get_import_query(self) -> str:
        """Return query for Kotlin import statements."""
        return """
        (import_header
          (import_list
            (import_alias
              (identifier) @module
              (import_alias)? @alias)?
            (identifier) @module)?) @import
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a Kotlin AST match."""
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
        elif "object" in captures:
            kind = SymbolKind.CLASS
        elif "function" in captures:
            kind = SymbolKind.METHOD

        # Get main node
        main_node = node
        for capture_name in ["class", "interface", "object", "function"]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Determine visibility
        visibility = self._get_kotlin_visibility(
            captures.get("modifiers", []), source
        )

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_kotlin_params(captures["params"][0], source)

        # Extract return type
        return_type = None
        if "return_type" in captures:
            return_type = self.get_node_text(captures["return_type"][0], source)

        # Extract generic parameters
        generics: list[str] = []
        if "generics" in captures:
            generics = self._extract_kotlin_generics(captures["generics"][0], source)

        # Find parent class
        parent_name = self.find_parent_class(main_node, source)

        # Extract modifiers
        modifiers = self._get_kotlin_modifiers(
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
        """Extract import information from a Kotlin AST match."""
        module_nodes = captures.get("module", [])
        if not module_nodes:
            return None

        module = self.get_node_text(module_nodes[0], source)

        # Get alias if present
        alias = None
        if "alias" in captures:
            alias = self.get_node_text(captures["alias"][0], source)

        # Get main node for line
        main_node = captures.get("import", [node])[0]

        # Check for wildcard
        import_text = self.get_node_text(main_node, source)
        is_wildcard = import_text.endswith(".*")

        return ImportInfo(
            module=module,
            symbols=[],
            line=main_node.start_point[0] + 1,
            is_relative=False,
            alias=alias,
            is_wildcard=is_wildcard,
        )

    def _get_kotlin_visibility(
        self,
        modifier_nodes: list["tree_sitter.Node"],
        source: bytes,
    ) -> Visibility:
        """Get Kotlin visibility from modifiers.

        Default is public if no modifier.
        """
        for mod_node in modifier_nodes:
            mod_text = self.get_node_text(mod_node, source)
            for keyword in ("public", "private", "protected", "internal"):
                if keyword in mod_text:
                    return self.visibility_keywords[keyword]
        return Visibility.PUBLIC  # Public is default in Kotlin

    def _extract_kotlin_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract Kotlin function parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type == "parameter":
                name = ""
                type_annotation = None
                default_value = None
                is_variadic = False

                for param_child in child.children:
                    if param_child.type == "simple_identifier":
                        name = self.get_node_text(param_child, source)
                    elif param_child.type == "type_identifier" or param_child.type == "user_type":
                        type_annotation = self.get_node_text(param_child, source)
                    elif param_child.type == "default_value":
                        default_value = self.get_node_text(param_child, source)

                # Check for vararg
                param_text = self.get_node_text(child, source)
                if "vararg" in param_text:
                    is_variadic = True

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            type_annotation=type_annotation,
                            default_value=default_value,
                            is_variadic=is_variadic,
                            is_optional=default_value is not None,
                        )
                    )

        return params

    def _extract_kotlin_generics(
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

    def _get_kotlin_modifiers(
        self,
        modifier_nodes: list["tree_sitter.Node"],
        source: bytes,
    ) -> list[str]:
        """Extract Kotlin modifiers."""
        modifiers: list[str] = []
        for mod_node in modifier_nodes:
            mod_text = self.get_node_text(mod_node, source)
            for keyword in (
                "suspend",
                "inline",
                "abstract",
                "final",
                "open",
                "override",
                "data",
                "sealed",
                "companion",
                "tailrec",
            ):
                if keyword in mod_text:
                    modifiers.append(keyword)
        return modifiers

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """Kotlin default visibility is public."""
        return Visibility.PUBLIC

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
                "object_declaration",
            ):
                for child in parent.children:
                    if child.type == "type_identifier":
                        return self.get_node_text(child, source)
            parent = parent.parent
        return None
