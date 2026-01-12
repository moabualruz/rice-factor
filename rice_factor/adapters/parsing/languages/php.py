"""PHP language extractor for tree-sitter.

Handles PHP-specific syntax including:
- Class, interface, trait definitions
- Method declarations with type hints
- Use/namespace statements
- Visibility modifiers (public, private, protected)
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


class PHPExtractor(LanguageExtractor):
    """Tree-sitter extractor for PHP."""

    language_id = "php"
    treesitter_language = "php"

    symbol_kind_map = {
        "class_declaration": SymbolKind.CLASS,
        "interface_declaration": SymbolKind.INTERFACE,
        "trait_declaration": SymbolKind.TRAIT,
        "enum_declaration": SymbolKind.ENUM,
        "method_declaration": SymbolKind.METHOD,
        "function_definition": SymbolKind.FUNCTION,
    }

    visibility_keywords = {
        "public": Visibility.PUBLIC,
        "private": Visibility.PRIVATE,
        "protected": Visibility.PROTECTED,
    }

    def get_class_query(self) -> str:
        """Return query for PHP type declarations."""
        return """
        [
          (class_declaration
            (visibility_modifier)? @visibility
            (final_modifier)? @final
            (abstract_modifier)? @abstract
            (readonly_modifier)? @readonly
            name: (name) @name) @class

          (interface_declaration
            name: (name) @name) @interface

          (trait_declaration
            name: (name) @name) @trait

          (enum_declaration
            name: (name) @name) @enum
        ]
        """

    def get_method_query(self) -> str:
        """Return query for PHP functions and methods."""
        return """
        [
          (method_declaration
            (visibility_modifier)? @visibility
            (final_modifier)? @final
            (abstract_modifier)? @abstract
            (static_modifier)? @static
            name: (name) @name
            parameters: (formal_parameters) @params
            return_type: (return_type)? @return_type) @method

          (function_definition
            name: (name) @name
            parameters: (formal_parameters) @params
            return_type: (return_type)? @return_type) @function
        ]
        """

    def get_import_query(self) -> str:
        """Return query for PHP use statements."""
        return """
        [
          (namespace_use_declaration
            (namespace_use_clause
              (qualified_name) @module
              (namespace_aliasing_clause
                (name) @alias)?)) @use

          (namespace_use_declaration
            (namespace_use_group
              (namespace_name) @prefix
              (namespace_use_group_clause
                (namespace_name) @module
                (namespace_aliasing_clause
                  (name) @alias)?)*)) @use_group
        ]
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a PHP AST match."""
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
        elif "trait" in captures:
            kind = SymbolKind.TRAIT
        elif "enum" in captures:
            kind = SymbolKind.ENUM
        elif "method" in captures:
            kind = SymbolKind.METHOD
        elif "function" in captures:
            kind = SymbolKind.FUNCTION

        # Get main node
        main_node = node
        for capture_name in [
            "class",
            "interface",
            "trait",
            "enum",
            "method",
            "function",
        ]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Determine visibility
        visibility = self._get_php_visibility(captures, source)

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_php_params(captures["params"][0], source)

        # Extract return type
        return_type = None
        if "return_type" in captures:
            rt_text = self.get_node_text(captures["return_type"][0], source)
            # Remove leading ": "
            return_type = rt_text.lstrip(": ").strip()

        # Find parent class
        parent_name = self.find_parent_class(main_node, source)

        # Extract modifiers
        modifiers = self._get_php_modifiers(captures, source)

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
            generic_params=[],  # PHP doesn't have native generics (PHPDoc only)
        )

    def extract_import_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
    ) -> ImportInfo | None:
        """Extract import information from a PHP AST match."""
        module_nodes = captures.get("module", [])
        if not module_nodes:
            return None

        module = self.get_node_text(module_nodes[0], source)

        # Handle grouped use with prefix
        if "prefix" in captures:
            prefix = self.get_node_text(captures["prefix"][0], source)
            module = f"{prefix}\\{module}"

        # Get alias if present
        alias = None
        if "alias" in captures:
            alias = self.get_node_text(captures["alias"][0], source)

        # Determine main node
        main_node = node
        for capture_name in ["use", "use_group"]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        return ImportInfo(
            module=module,
            symbols=[],
            line=main_node.start_point[0] + 1,
            is_relative=not module.startswith("\\"),
            alias=alias,
            is_wildcard=False,
        )

    def _get_php_visibility(
        self,
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
    ) -> Visibility:
        """Get PHP visibility from captures.

        Default is public for interfaces, public for class members.
        """
        if "visibility" in captures:
            vis_text = self.get_node_text(captures["visibility"][0], source)
            if vis_text in self.visibility_keywords:
                return self.visibility_keywords[vis_text]

        # Interface methods are always public
        if "interface" in captures:
            return Visibility.PUBLIC

        return Visibility.PUBLIC  # PHP 8 default is public for methods

    def _extract_php_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract PHP function parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type == "simple_parameter":
                name = ""
                type_annotation = None
                default_value = None
                is_variadic = False
                is_reference = False

                for param_child in child.children:
                    if param_child.type == "variable_name":
                        name = self.get_node_text(param_child, source)
                        # Remove $ prefix for cleaner display
                        name = name.lstrip("$")
                    elif param_child.type in (
                        "named_type",
                        "optional_type",
                        "union_type",
                        "intersection_type",
                        "primitive_type",
                    ):
                        type_annotation = self.get_node_text(param_child, source)
                    elif param_child.type == "property_promotion_parameter":
                        # Constructor property promotion
                        pass
                    elif param_child.type == "...":
                        is_variadic = True
                    elif param_child.type == "&":
                        is_reference = True

                # Check for default value
                for param_child in child.children:
                    if param_child.type not in (
                        "variable_name",
                        "named_type",
                        "optional_type",
                        "union_type",
                        "intersection_type",
                        "primitive_type",
                        "visibility_modifier",
                        "readonly_modifier",
                        "...",
                        "&",
                        "=",
                        ",",
                    ):
                        default_value = self.get_node_text(param_child, source)

                if name:
                    params.append(
                        ParameterInfo(
                            name=f"&{name}" if is_reference else name,
                            type_annotation=type_annotation,
                            default_value=default_value,
                            is_variadic=is_variadic,
                            is_optional=default_value is not None,
                        )
                    )

            elif child.type == "variadic_parameter":
                name = ""
                type_annotation = None
                for vc in child.children:
                    if vc.type == "variable_name":
                        name = self.get_node_text(vc, source).lstrip("$")
                    elif vc.type in ("named_type", "union_type"):
                        type_annotation = self.get_node_text(vc, source)

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            type_annotation=type_annotation,
                            is_variadic=True,
                        )
                    )

        return params

    def _get_php_modifiers(
        self,
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
    ) -> list[str]:
        """Extract PHP modifiers."""
        modifiers: list[str] = []

        if "final" in captures:
            modifiers.append("final")
        if "abstract" in captures:
            modifiers.append("abstract")
        if "static" in captures:
            modifiers.append("static")
        if "readonly" in captures:
            modifiers.append("readonly")

        return modifiers

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """PHP default visibility is public."""
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
                "trait_declaration",
            ):
                for child in parent.children:
                    if child.type == "name":
                        return self.get_node_text(child, source)
            parent = parent.parent
        return None
