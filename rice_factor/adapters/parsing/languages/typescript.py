"""TypeScript language extractor for tree-sitter.

Handles TypeScript-specific syntax including:
- Class and interface definitions
- Function and method declarations with type annotations
- Import statements (ES modules)
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


class TypeScriptExtractor(LanguageExtractor):
    """Tree-sitter extractor for TypeScript."""

    language_id = "typescript"
    treesitter_language = "typescript"

    symbol_kind_map = {
        "class_declaration": SymbolKind.CLASS,
        "interface_declaration": SymbolKind.INTERFACE,
        "enum_declaration": SymbolKind.ENUM,
        "type_alias_declaration": SymbolKind.TYPE_ALIAS,
        "function_declaration": SymbolKind.FUNCTION,
        "method_definition": SymbolKind.METHOD,
        "method_signature": SymbolKind.METHOD,
    }

    visibility_keywords = {
        "public": Visibility.PUBLIC,
        "private": Visibility.PRIVATE,
        "protected": Visibility.PROTECTED,
    }

    def get_class_query(self) -> str:
        """Return query for TypeScript type declarations."""
        return """
        [
          (class_declaration
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @generics) @class

          (interface_declaration
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @generics) @interface

          (enum_declaration
            name: (identifier) @name) @enum

          (type_alias_declaration
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @generics) @type_alias
        ]
        """

    def get_method_query(self) -> str:
        """Return query for TypeScript functions and methods."""
        return """
        [
          (function_declaration
            name: (identifier) @name
            parameters: (formal_parameters) @params
            return_type: (type_annotation)? @return_type) @function

          (method_definition
            name: (property_identifier) @name
            parameters: (formal_parameters) @params
            return_type: (type_annotation)? @return_type) @method

          (method_signature
            name: (property_identifier) @name
            parameters: (formal_parameters) @params
            return_type: (type_annotation)? @return_type) @method_sig

          (arrow_function
            parameters: (formal_parameters) @params
            return_type: (type_annotation)? @return_type) @arrow
        ]
        """

    def get_import_query(self) -> str:
        """Return query for TypeScript import statements."""
        return """
        [
          (import_statement
            (import_clause
              (identifier) @default_import)?
            (import_clause
              (named_imports
                (import_specifier
                  name: (identifier) @symbol
                  alias: (identifier)? @alias)*))?
            (import_clause
              (namespace_import
                (identifier) @namespace))?
            source: (string) @module) @import
        ]
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a TypeScript AST match."""
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
        elif "type_alias" in captures:
            kind = SymbolKind.TYPE_ALIAS
        elif "function" in captures:
            kind = SymbolKind.FUNCTION
        elif "method" in captures or "method_sig" in captures:
            kind = SymbolKind.METHOD
        elif "arrow" in captures:
            kind = SymbolKind.FUNCTION

        # Get main node
        main_node = node
        for capture_name in [
            "class",
            "interface",
            "enum",
            "type_alias",
            "function",
            "method",
            "method_sig",
            "arrow",
        ]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Determine visibility
        visibility = self._get_ts_visibility(main_node, source)

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_ts_params(captures["params"][0], source)

        # Extract return type
        return_type = None
        if "return_type" in captures:
            rt_text = self.get_node_text(captures["return_type"][0], source)
            # Remove the leading ": "
            return_type = rt_text.lstrip(": ").strip()

        # Extract generic parameters
        generics: list[str] = []
        if "generics" in captures:
            generics = self._extract_ts_generics(captures["generics"][0], source)

        # Find parent class
        parent_name = self.find_parent_class(main_node, source)

        # Extract modifiers
        modifiers = self._get_ts_modifiers(main_node, source)

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
        """Extract import information from a TypeScript AST match."""
        module_nodes = captures.get("module", [])
        if not module_nodes:
            return None

        # Get module path (remove quotes)
        module = self.get_node_text(module_nodes[0], source)
        module = module.strip("'\"")

        # Get specific symbols
        symbols: list[str] = []
        if "symbol" in captures:
            for sym_node in captures["symbol"]:
                symbols.append(self.get_node_text(sym_node, source))

        # Get default import
        if "default_import" in captures:
            default_name = self.get_node_text(captures["default_import"][0], source)
            symbols.insert(0, f"default as {default_name}")

        # Get namespace import
        alias = None
        if "namespace" in captures:
            alias = self.get_node_text(captures["namespace"][0], source)

        # Check for relative import
        is_relative = module.startswith(".")

        # Get main node for line
        main_node = captures.get("import", [node])[0]

        return ImportInfo(
            module=module,
            symbols=symbols,
            line=main_node.start_point[0] + 1,
            is_relative=is_relative,
            alias=alias,
            is_wildcard=alias is not None and not symbols,
        )

    def _get_ts_visibility(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> Visibility:
        """Get TypeScript visibility from a node."""
        # Check accessibility modifier in children
        for child in node.children:
            if child.type == "accessibility_modifier":
                mod_text = self.get_node_text(child, source)
                if mod_text in self.visibility_keywords:
                    return self.visibility_keywords[mod_text]
        return Visibility.PUBLIC  # Public is default

    def _extract_ts_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract TypeScript function parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type in ("required_parameter", "optional_parameter"):
                name = ""
                type_annotation = None
                default_value = None
                is_optional = child.type == "optional_parameter"
                is_variadic = False

                for param_child in child.children:
                    if param_child.type == "identifier":
                        name = self.get_node_text(param_child, source)
                    elif param_child.type == "type_annotation":
                        ta_text = self.get_node_text(param_child, source)
                        type_annotation = ta_text.lstrip(": ").strip()
                    elif param_child.type in (
                        "string",
                        "number",
                        "true",
                        "false",
                        "null",
                        "undefined",
                    ):
                        default_value = self.get_node_text(param_child, source)
                    elif param_child.type == "...":
                        is_variadic = True

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            type_annotation=type_annotation,
                            default_value=default_value,
                            is_variadic=is_variadic,
                            is_optional=is_optional or default_value is not None,
                        )
                    )

            elif child.type == "rest_parameter":
                name = ""
                type_annotation = None
                for param_child in child.children:
                    if param_child.type == "identifier":
                        name = self.get_node_text(param_child, source)
                    elif param_child.type == "type_annotation":
                        ta_text = self.get_node_text(param_child, source)
                        type_annotation = ta_text.lstrip(": ").strip()

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            type_annotation=type_annotation,
                            is_variadic=True,
                        )
                    )

        return params

    def _extract_ts_generics(
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

    def _get_ts_modifiers(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract TypeScript modifiers."""
        modifiers: list[str] = []
        for child in node.children:
            if child.type == "async":
                modifiers.append("async")
            elif child.type == "static":
                modifiers.append("static")
            elif child.type == "readonly":
                modifiers.append("readonly")
            elif child.type == "abstract":
                modifiers.append("abstract")
            elif child.type == "override":
                modifiers.append("override")
            elif child.type == "decorator":
                modifiers.append("decorated")
        return modifiers

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """TypeScript default visibility is public."""
        return Visibility.PUBLIC

    def find_parent_class(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> str | None:
        """Find the name of the containing class."""
        parent = node.parent
        while parent:
            if parent.type in ("class_declaration", "interface_declaration"):
                for child in parent.children:
                    if child.type == "type_identifier":
                        return self.get_node_text(child, source)
            parent = parent.parent
        return None
