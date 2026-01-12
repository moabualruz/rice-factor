"""Rust language extractor for tree-sitter.

Handles Rust-specific syntax including:
- Struct, enum, and trait definitions
- impl blocks and methods
- Use statements (single and grouped)
- Visibility modifiers (pub, pub(crate), pub(super))
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


class RustExtractor(LanguageExtractor):
    """Tree-sitter extractor for Rust."""

    language_id = "rust"
    treesitter_language = "rust"

    symbol_kind_map = {
        "struct_item": SymbolKind.STRUCT,
        "enum_item": SymbolKind.ENUM,
        "trait_item": SymbolKind.TRAIT,
        "impl_item": SymbolKind.CLASS,
        "function_item": SymbolKind.FUNCTION,
        "function_signature_item": SymbolKind.METHOD,
        "type_item": SymbolKind.TYPE_ALIAS,
    }

    def get_class_query(self) -> str:
        """Return query for Rust type definitions."""
        return """
        [
          (struct_item
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @generics) @struct

          (enum_item
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @generics) @enum

          (trait_item
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @generics) @trait

          (impl_item
            trait: (type_identifier)? @trait_name
            type: (type_identifier) @name
            type_parameters: (type_parameters)? @generics) @impl
        ]
        """

    def get_method_query(self) -> str:
        """Return query for Rust functions and methods."""
        return """
        [
          (function_item
            (visibility_modifier)? @visibility
            name: (identifier) @name
            parameters: (parameters) @params
            return_type: (_)? @return_type) @function

          (function_signature_item
            (visibility_modifier)? @visibility
            name: (identifier) @name
            parameters: (parameters) @params
            return_type: (_)? @return_type) @method_sig
        ]
        """

    def get_import_query(self) -> str:
        """Return query for Rust use statements."""
        return """
        (use_declaration
          (visibility_modifier)? @visibility
          argument: [
            (scoped_identifier) @module
            (use_wildcard
              (scoped_identifier)? @module) @wildcard
            (scoped_use_list
              path: (scoped_identifier)? @module
              list: (use_list) @symbols)
            (use_as_clause
              path: (scoped_identifier) @module
              alias: (identifier) @alias)
            (identifier) @module
          ]) @use
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a Rust AST match."""
        # Get name
        name_nodes = captures.get("name", [])
        if not name_nodes:
            return None
        name = self.get_node_text(name_nodes[0], source)

        # Determine kind
        if "struct" in captures:
            kind = SymbolKind.STRUCT
        elif "enum" in captures:
            kind = SymbolKind.ENUM
        elif "trait" in captures:
            kind = SymbolKind.TRAIT
        elif "impl" in captures:
            kind = SymbolKind.CLASS  # impl block treated as class
        elif "function" in captures:
            kind = SymbolKind.FUNCTION
        elif "method_sig" in captures:
            kind = SymbolKind.METHOD

        # Get main node for position
        main_node = node
        for capture_name in ["struct", "enum", "trait", "impl", "function", "method_sig"]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Determine visibility
        visibility = self._get_rust_visibility(main_node, source)

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_rust_params(captures["params"][0], source)

        # Extract return type
        return_type = None
        if "return_type" in captures:
            return_type = self.get_node_text(captures["return_type"][0], source)

        # Extract generic parameters
        generics: list[str] = []
        if "generics" in captures:
            generics = self._extract_rust_generics(captures["generics"][0], source)

        # Find parent (impl block type)
        parent_name = self._find_impl_type(main_node, source)

        # Extract modifiers
        modifiers = self._get_rust_modifiers(main_node, source)

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
        """Extract import information from a Rust AST match."""
        module_nodes = captures.get("module", [])
        if not module_nodes:
            return None

        module = self.get_node_text(module_nodes[0], source)

        # Get alias if present
        alias = None
        if "alias" in captures:
            alias = self.get_node_text(captures["alias"][0], source)

        # Extract specific symbols
        symbols: list[str] = []
        if "symbols" in captures:
            symbols = self._extract_use_list(captures["symbols"][0], source)

        # Check for wildcard
        is_wildcard = "wildcard" in captures

        # Get main node for line
        main_node = captures.get("use", [node])[0]

        return ImportInfo(
            module=module,
            symbols=symbols,
            line=main_node.start_point[0] + 1,
            is_relative=module.startswith("self::") or module.startswith("super::"),
            alias=alias,
            is_wildcard=is_wildcard,
        )

    def _get_rust_visibility(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> Visibility:
        """Get Rust visibility from a node.

        Handles:
        - pub -> PUBLIC
        - pub(crate) -> INTERNAL
        - pub(super) -> PROTECTED
        - (none) -> PRIVATE
        """
        for child in node.children:
            if child.type == "visibility_modifier":
                vis_text = self.get_node_text(child, source)
                if vis_text == "pub":
                    return Visibility.PUBLIC
                elif "crate" in vis_text:
                    return Visibility.INTERNAL
                elif "super" in vis_text:
                    return Visibility.PROTECTED
                elif "self" in vis_text:
                    return Visibility.PRIVATE
        return Visibility.PRIVATE

    def _extract_rust_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract Rust function parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type == "parameter":
                name = ""
                type_annotation = None
                is_variadic = False

                for param_child in child.children:
                    if param_child.type == "identifier":
                        name = self.get_node_text(param_child, source)
                    elif param_child.type in (
                        "type_identifier",
                        "reference_type",
                        "generic_type",
                        "scoped_type_identifier",
                        "primitive_type",
                        "array_type",
                        "tuple_type",
                        "function_type",
                    ):
                        type_annotation = self.get_node_text(param_child, source)
                    elif param_child.type == "mutable_specifier":
                        # mut in parameter
                        pass

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            type_annotation=type_annotation,
                            is_variadic=is_variadic,
                        )
                    )

            elif child.type == "self_parameter":
                # Handle self, &self, &mut self
                self_text = self.get_node_text(child, source)
                params.append(
                    ParameterInfo(
                        name="self",
                        type_annotation=self_text if self_text != "self" else None,
                    )
                )

        return params

    def _extract_rust_generics(
        self,
        generics_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract generic type parameters."""
        generics: list[str] = []
        for child in generics_node.children:
            if child.type in ("type_identifier", "lifetime"):
                generics.append(self.get_node_text(child, source))
            elif child.type == "constrained_type_parameter":
                for gc in child.children:
                    if gc.type == "type_identifier":
                        generics.append(self.get_node_text(gc, source))
                        break
        return generics

    def _find_impl_type(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> str | None:
        """Find the type name for methods in impl blocks."""
        parent = node.parent
        while parent:
            if parent.type == "impl_item":
                for child in parent.children:
                    if child.type == "type_identifier":
                        return self.get_node_text(child, source)
            parent = parent.parent
        return None

    def _get_rust_modifiers(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract Rust function modifiers."""
        modifiers: list[str] = []
        for child in node.children:
            if child.type == "async":
                modifiers.append("async")
            elif child.type == "const":
                modifiers.append("const")
            elif child.type == "unsafe":
                modifiers.append("unsafe")
            elif child.type == "extern":
                modifiers.append("extern")
        return modifiers

    def _extract_use_list(
        self,
        use_list_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract symbols from a use list like {A, B, C}."""
        symbols: list[str] = []
        for child in use_list_node.children:
            if child.type == "identifier":
                symbols.append(self.get_node_text(child, source))
            elif child.type == "use_as_clause":
                # Get the original name
                for uc in child.children:
                    if uc.type == "identifier":
                        symbols.append(self.get_node_text(uc, source))
                        break
        return symbols

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """Rust default visibility is private."""
        return Visibility.PRIVATE
