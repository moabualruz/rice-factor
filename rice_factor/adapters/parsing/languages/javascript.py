"""JavaScript language extractor for tree-sitter.

Handles JavaScript-specific syntax including:
- Class definitions (ES6+)
- Function and method declarations
- Import statements (ES modules and CommonJS)
- No formal visibility (convention-based with _ prefix)
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


class JavaScriptExtractor(LanguageExtractor):
    """Tree-sitter extractor for JavaScript."""

    language_id = "javascript"
    treesitter_language = "javascript"

    symbol_kind_map = {
        "class_declaration": SymbolKind.CLASS,
        "function_declaration": SymbolKind.FUNCTION,
        "method_definition": SymbolKind.METHOD,
        "arrow_function": SymbolKind.FUNCTION,
        "generator_function_declaration": SymbolKind.FUNCTION,
    }

    def get_class_query(self) -> str:
        """Return query for JavaScript class declarations."""
        return """
        (class_declaration
          name: (identifier) @name) @class
        """

    def get_method_query(self) -> str:
        """Return query for JavaScript functions and methods."""
        return """
        [
          (function_declaration
            name: (identifier) @name
            parameters: (formal_parameters) @params) @function

          (method_definition
            name: (property_identifier) @name
            parameters: (formal_parameters) @params) @method

          (generator_function_declaration
            name: (identifier) @name
            parameters: (formal_parameters) @params) @generator

          (variable_declarator
            name: (identifier) @name
            value: (arrow_function
              parameters: (formal_parameters) @params)) @arrow_var
        ]
        """

    def get_import_query(self) -> str:
        """Return query for JavaScript import statements."""
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

          (call_expression
            function: (identifier) @require (#eq? @require "require")
            arguments: (arguments
              (string) @module)) @commonjs
        ]
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a JavaScript AST match."""
        # Get name
        name_nodes = captures.get("name", [])
        if not name_nodes:
            return None
        name = self.get_node_text(name_nodes[0], source)

        # Determine kind
        if "class" in captures:
            kind = SymbolKind.CLASS
        elif "function" in captures:
            kind = SymbolKind.FUNCTION
        elif "method" in captures:
            kind = SymbolKind.METHOD
        elif "generator" in captures or "arrow_var" in captures:
            kind = SymbolKind.FUNCTION

        # Get main node
        main_node = node
        for capture_name in ["class", "function", "method", "generator", "arrow_var"]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Determine visibility (convention-based)
        visibility = Visibility.PRIVATE if name.startswith("_") else Visibility.PUBLIC

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_js_params(captures["params"][0], source)

        # Find parent class
        parent_name = self.find_parent_class(main_node, source)

        # Extract modifiers
        modifiers = self._get_js_modifiers(main_node, source)

        # Build signature
        signature = self.build_signature(name, params, None)

        return SymbolInfo(
            name=name,
            kind=kind,
            visibility=visibility,
            line_start=main_node.start_point[0] + 1,
            line_end=main_node.end_point[0] + 1,
            column_start=main_node.start_point[1],
            column_end=main_node.end_point[1],
            signature=signature,
            return_type=None,  # JS doesn't have return types
            parameters=params,
            modifiers=modifiers,
            parent_name=parent_name,
            docstring=self.get_docstring(main_node, source),
            generic_params=[],
        )

    def extract_import_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
    ) -> ImportInfo | None:
        """Extract import information from a JavaScript AST match."""
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

        # Determine main node
        main_node = node
        if "import" in captures:
            main_node = captures["import"][0]
        elif "commonjs" in captures:
            main_node = captures["commonjs"][0]

        return ImportInfo(
            module=module,
            symbols=symbols,
            line=main_node.start_point[0] + 1,
            is_relative=is_relative,
            alias=alias,
            is_wildcard=alias is not None and not symbols,
        )

    def _extract_js_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract JavaScript function parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type == "identifier":
                name = self.get_node_text(child, source)
                params.append(ParameterInfo(name=name))

            elif child.type == "assignment_pattern":
                # Parameter with default value
                name = ""
                default_value = None
                for ac in child.children:
                    if ac.type == "identifier":
                        name = self.get_node_text(ac, source)
                    elif ac.type not in ("=", ","):
                        default_value = self.get_node_text(ac, source)

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            default_value=default_value,
                            is_optional=True,
                        )
                    )

            elif child.type == "rest_pattern":
                # ...args parameter
                for rc in child.children:
                    if rc.type == "identifier":
                        name = self.get_node_text(rc, source)
                        params.append(
                            ParameterInfo(
                                name=name,
                                is_variadic=True,
                            )
                        )
                        break

            elif child.type == "object_pattern":
                # Destructured parameter
                params.append(
                    ParameterInfo(
                        name=self.get_node_text(child, source),
                    )
                )

            elif child.type == "array_pattern":
                # Destructured array parameter
                params.append(
                    ParameterInfo(
                        name=self.get_node_text(child, source),
                    )
                )

        return params

    def _get_js_modifiers(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> list[str]:
        """Extract JavaScript modifiers."""
        modifiers: list[str] = []

        # Check for async
        for child in node.children:
            if child.type == "async":
                modifiers.append("async")
            elif child.type == "static":
                modifiers.append("static")
            elif child.type == "get":
                modifiers.append("getter")
            elif child.type == "set":
                modifiers.append("setter")

        # Check if generator
        node_text = self.get_node_text(node, source)
        if node_text.startswith("function*") or node_text.startswith("*"):
            modifiers.append("generator")

        return modifiers

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """JavaScript default visibility is public (convention-based)."""
        return Visibility.PUBLIC

    def find_parent_class(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> str | None:
        """Find the name of the containing class."""
        parent = node.parent
        while parent:
            if parent.type == "class_declaration":
                for child in parent.children:
                    if child.type == "identifier":
                        return self.get_node_text(child, source)
            elif parent.type == "class_body":
                # Go up one more level
                pass
            parent = parent.parent
        return None
