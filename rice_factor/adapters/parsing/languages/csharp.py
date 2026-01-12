"""C# language extractor for tree-sitter.

Handles C#-specific syntax including:
- Class, interface, struct, record definitions
- Method and property declarations
- Using statements
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


class CSharpExtractor(LanguageExtractor):
    """Tree-sitter extractor for C#."""

    language_id = "csharp"
    treesitter_language = "c_sharp"

    symbol_kind_map = {
        "class_declaration": SymbolKind.CLASS,
        "interface_declaration": SymbolKind.INTERFACE,
        "struct_declaration": SymbolKind.STRUCT,
        "record_declaration": SymbolKind.CLASS,
        "enum_declaration": SymbolKind.ENUM,
        "method_declaration": SymbolKind.METHOD,
        "constructor_declaration": SymbolKind.METHOD,
        "property_declaration": SymbolKind.PROPERTY,
    }

    visibility_keywords = {
        "public": Visibility.PUBLIC,
        "private": Visibility.PRIVATE,
        "protected": Visibility.PROTECTED,
        "internal": Visibility.INTERNAL,
    }

    def get_class_query(self) -> str:
        """Return query for C# type declarations."""
        return """
        [
          (class_declaration
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @generics) @class

          (interface_declaration
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @generics) @interface

          (struct_declaration
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @generics) @struct

          (record_declaration
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @generics) @record

          (enum_declaration
            (modifier)* @modifiers
            name: (identifier) @name) @enum
        ]
        """

    def get_method_query(self) -> str:
        """Return query for C# methods and constructors."""
        return """
        [
          (method_declaration
            (modifier)* @modifiers
            type: (_) @return_type
            name: (identifier) @name
            parameters: (parameter_list) @params) @method

          (constructor_declaration
            (modifier)* @modifiers
            name: (identifier) @name
            parameters: (parameter_list) @params) @constructor

          (property_declaration
            (modifier)* @modifiers
            type: (_) @return_type
            name: (identifier) @name) @property
        ]
        """

    def get_import_query(self) -> str:
        """Return query for C# using statements."""
        return """
        [
          (using_directive
            (identifier) @module) @using

          (using_directive
            (qualified_name) @module) @using_qualified

          (using_directive
            (name_equals
              (identifier) @alias)
            [
              (identifier)
              (qualified_name)
            ] @module) @using_alias
        ]
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a C# AST match."""
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
        elif "struct" in captures:
            kind = SymbolKind.STRUCT
        elif "record" in captures:
            kind = SymbolKind.CLASS
        elif "enum" in captures:
            kind = SymbolKind.ENUM
        elif "method" in captures or "constructor" in captures:
            kind = SymbolKind.METHOD
        elif "property" in captures:
            kind = SymbolKind.PROPERTY

        # Get main node
        main_node = node
        for capture_name in [
            "class",
            "interface",
            "struct",
            "record",
            "enum",
            "method",
            "constructor",
            "property",
        ]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Determine visibility
        visibility = self._get_csharp_visibility(
            captures.get("modifiers", []), source
        )

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_csharp_params(captures["params"][0], source)

        # Extract return type
        return_type = None
        if "return_type" in captures:
            return_type = self.get_node_text(captures["return_type"][0], source)

        # Extract generic parameters
        generics: list[str] = []
        if "generics" in captures:
            generics = self._extract_csharp_generics(captures["generics"][0], source)

        # Find parent class
        parent_name = self.find_parent_class(main_node, source)

        # Extract modifiers
        modifiers = self._get_csharp_modifiers(
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
        """Extract import information from a C# AST match."""
        module_nodes = captures.get("module", [])
        if not module_nodes:
            return None

        module = self.get_node_text(module_nodes[0], source)

        # Get alias if present
        alias = None
        if "alias" in captures:
            alias = self.get_node_text(captures["alias"][0], source)

        # Determine main node
        main_node = node
        for capture_name in ["using", "using_qualified", "using_alias"]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        return ImportInfo(
            module=module,
            symbols=[],
            line=main_node.start_point[0] + 1,
            is_relative=False,
            alias=alias,
            is_wildcard=False,
        )

    def _get_csharp_visibility(
        self,
        modifier_nodes: list["tree_sitter.Node"],
        source: bytes,
    ) -> Visibility:
        """Get C# visibility from modifiers.

        Default is private for class members, internal for types.
        """
        for mod_node in modifier_nodes:
            mod_text = self.get_node_text(mod_node, source)
            # Handle "protected internal" or "private protected"
            if "public" in mod_text:
                return Visibility.PUBLIC
            elif "protected" in mod_text and "internal" in mod_text:
                return Visibility.PROTECTED  # protected internal
            elif "private" in mod_text and "protected" in mod_text:
                return Visibility.PRIVATE  # private protected
            elif "protected" in mod_text:
                return Visibility.PROTECTED
            elif "internal" in mod_text:
                return Visibility.INTERNAL
            elif "private" in mod_text:
                return Visibility.PRIVATE
        return Visibility.PRIVATE  # Private is default for members

    def _extract_csharp_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract C# method parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type == "parameter":
                name = ""
                type_annotation = None
                default_value = None
                is_variadic = False

                for param_child in child.children:
                    if param_child.type == "identifier":
                        name = self.get_node_text(param_child, source)
                    elif param_child.type in (
                        "predefined_type",
                        "identifier",
                        "generic_name",
                        "nullable_type",
                        "array_type",
                        "tuple_type",
                    ):
                        if not name:  # Type comes before name
                            type_annotation = self.get_node_text(param_child, source)
                    elif param_child.type == "equals_value_clause":
                        for ec in param_child.children:
                            if ec.type != "=":
                                default_value = self.get_node_text(ec, source)
                    elif param_child.type == "parameter_modifier":
                        mod_text = self.get_node_text(param_child, source)
                        if mod_text == "params":
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

    def _extract_csharp_generics(
        self,
        generics_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract generic type parameters."""
        generics: list[str] = []
        for child in generics_node.children:
            if child.type == "type_parameter":
                for gc in child.children:
                    if gc.type == "identifier":
                        generics.append(self.get_node_text(gc, source))
                        break
        return generics

    def _get_csharp_modifiers(
        self,
        modifier_nodes: list["tree_sitter.Node"],
        source: bytes,
    ) -> list[str]:
        """Extract C# modifiers."""
        modifiers: list[str] = []
        for mod_node in modifier_nodes:
            mod_text = self.get_node_text(mod_node, source)
            for keyword in (
                "static",
                "abstract",
                "virtual",
                "override",
                "sealed",
                "readonly",
                "async",
                "partial",
                "extern",
                "unsafe",
                "volatile",
            ):
                if keyword in mod_text:
                    modifiers.append(keyword)
        return modifiers

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """C# default visibility is private for members."""
        return Visibility.PRIVATE

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
                "struct_declaration",
                "record_declaration",
            ):
                for child in parent.children:
                    if child.type == "identifier":
                        return self.get_node_text(child, source)
            parent = parent.parent
        return None
