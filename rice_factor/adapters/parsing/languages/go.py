"""Go language extractor for tree-sitter.

Handles Go-specific syntax including:
- Struct and interface definitions
- Method declarations with receivers
- Import statements (single and grouped)
- Visibility by naming convention (exported = capitalized)
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


class GoExtractor(LanguageExtractor):
    """Tree-sitter extractor for Go."""

    language_id = "go"
    treesitter_language = "go"

    symbol_kind_map = {
        "type_declaration": SymbolKind.CLASS,
        "struct_type": SymbolKind.STRUCT,
        "interface_type": SymbolKind.INTERFACE,
        "function_declaration": SymbolKind.FUNCTION,
        "method_declaration": SymbolKind.METHOD,
    }

    def get_class_query(self) -> str:
        """Return query for Go type declarations."""
        return """
        (type_declaration
          (type_spec
            name: (type_identifier) @name
            type: [
              (struct_type) @struct
              (interface_type) @interface
            ])) @type_decl
        """

    def get_method_query(self) -> str:
        """Return query for Go functions and methods."""
        return """
        [
          (function_declaration
            name: (identifier) @name
            parameters: (parameter_list) @params
            result: (_)? @return_type) @function

          (method_declaration
            receiver: (parameter_list) @receiver
            name: (field_identifier) @name
            parameters: (parameter_list) @params
            result: (_)? @return_type) @method
        ]
        """

    def get_import_query(self) -> str:
        """Return query for Go import statements."""
        return """
        [
          (import_declaration
            (import_spec
              name: (package_identifier)? @alias
              path: (interpreted_string_literal) @module)) @import

          (import_declaration
            (import_spec_list
              (import_spec
                name: (package_identifier)? @alias
                path: (interpreted_string_literal) @module))) @import_group
        ]
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a Go AST match."""
        # Get name
        name_nodes = captures.get("name", [])
        if not name_nodes:
            return None
        name = self.get_node_text(name_nodes[0], source)

        # Determine visibility (Go: exported if capitalized)
        visibility = Visibility.PUBLIC if name[0].isupper() else Visibility.PACKAGE

        # Determine kind
        if "struct" in captures:
            kind = SymbolKind.STRUCT
        elif "interface" in captures:
            kind = SymbolKind.INTERFACE
        elif "method" in captures or "receiver" in captures:
            kind = SymbolKind.METHOD
        elif "function" in captures:
            kind = SymbolKind.FUNCTION

        # Get main node for position
        main_node = node
        if "type_decl" in captures:
            main_node = captures["type_decl"][0]
        elif "function" in captures:
            main_node = captures["function"][0]
        elif "method" in captures:
            main_node = captures["method"][0]

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_go_params(captures["params"][0], source)

        # Extract return type
        return_type = None
        if "return_type" in captures:
            return_type = self.get_node_text(captures["return_type"][0], source)

        # Find parent class for methods
        parent_name = None
        if "receiver" in captures:
            receiver = self.get_node_text(captures["receiver"][0], source)
            # Extract type name from receiver like "(r *Receiver)"
            parent_name = self._extract_receiver_type(receiver)

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
            modifiers=[],
            parent_name=parent_name,
            docstring=self.get_docstring(main_node, source),
            generic_params=self._extract_type_params(main_node, source),
        )

    def extract_import_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
    ) -> ImportInfo | None:
        """Extract import information from a Go AST match."""
        module_nodes = captures.get("module", [])
        if not module_nodes:
            return None

        # Get module path (remove quotes)
        module = self.get_node_text(module_nodes[0], source).strip('"')

        # Get alias if present
        alias = None
        if "alias" in captures:
            alias = self.get_node_text(captures["alias"][0], source)
            # Handle "." import (dot import)
            if alias == ".":
                alias = None  # Treat as wildcard

        # Determine line
        main_node = node
        if "import" in captures:
            main_node = captures["import"][0]
        elif "import_group" in captures:
            main_node = captures["import_group"][0]

        return ImportInfo(
            module=module,
            symbols=[],  # Go doesn't have selective imports
            line=main_node.start_point[0] + 1,
            is_relative=False,  # Go doesn't have relative imports
            alias=alias,
            is_wildcard=alias == ".",
        )

    def _extract_go_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract Go function parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type == "parameter_declaration":
                # Parameters can have multiple names: a, b int
                names: list[str] = []
                type_annotation = None

                for param_child in child.children:
                    if param_child.type == "identifier":
                        names.append(self.get_node_text(param_child, source))
                    elif param_child.type in (
                        "type_identifier",
                        "pointer_type",
                        "slice_type",
                        "array_type",
                        "map_type",
                        "channel_type",
                        "function_type",
                        "struct_type",
                        "interface_type",
                        "qualified_type",
                    ):
                        type_annotation = self.get_node_text(param_child, source)

                # Handle variadic parameters
                is_variadic = False
                if child.type == "variadic_parameter_declaration":
                    is_variadic = True

                for name in names:
                    params.append(
                        ParameterInfo(
                            name=name,
                            type_annotation=type_annotation,
                            is_variadic=is_variadic,
                        )
                    )

            elif child.type == "variadic_parameter_declaration":
                name = ""
                type_annotation = None
                for param_child in child.children:
                    if param_child.type == "identifier":
                        name = self.get_node_text(param_child, source)
                    elif param_child.type not in ("...", ","):
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

    def _extract_receiver_type(self, receiver: str) -> str | None:
        """Extract type name from Go method receiver.

        Args:
            receiver: Receiver string like "(r *Receiver)" or "(r Receiver)"

        Returns:
            Type name without pointer or parentheses.
        """
        # Remove parentheses and split
        receiver = receiver.strip("()")
        parts = receiver.split()
        if len(parts) >= 2:
            type_part = parts[-1]
            # Remove pointer
            return type_part.lstrip("*")
        return None

    def _extract_type_params(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract generic type parameters (Go 1.18+)."""
        params: list[str] = []
        for child in node.children:
            if child.type == "type_parameter_list":
                for param in child.children:
                    if param.type == "type_parameter_declaration":
                        for p_child in param.children:
                            if p_child.type == "identifier":
                                params.append(self.get_node_text(p_child, source))
        return params

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """Go default visibility is package-private (unexported)."""
        return Visibility.PACKAGE
