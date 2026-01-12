"""Ruby language extractor for tree-sitter.

Handles Ruby-specific syntax including:
- Class and module definitions
- Method definitions (def, attr_*, singleton methods)
- Require and include statements
- Visibility (public, private, protected methods)
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


class RubyExtractor(LanguageExtractor):
    """Tree-sitter extractor for Ruby."""

    language_id = "ruby"
    treesitter_language = "ruby"

    symbol_kind_map = {
        "class": SymbolKind.CLASS,
        "module": SymbolKind.MODULE,
        "method": SymbolKind.METHOD,
        "singleton_method": SymbolKind.METHOD,
    }

    def get_class_query(self) -> str:
        """Return query for Ruby class and module definitions."""
        return """
        [
          (class
            name: [
              (constant) @name
              (scope_resolution
                name: (constant) @name)
            ]) @class

          (module
            name: [
              (constant) @name
              (scope_resolution
                name: (constant) @name)
            ]) @module
        ]
        """

    def get_method_query(self) -> str:
        """Return query for Ruby method definitions."""
        return """
        [
          (method
            name: (identifier) @name
            parameters: (method_parameters)? @params) @method

          (singleton_method
            object: (_) @receiver
            name: (identifier) @name
            parameters: (method_parameters)? @params) @singleton_method
        ]
        """

    def get_import_query(self) -> str:
        """Return query for Ruby require and include statements."""
        return """
        [
          (call
            method: (identifier) @method (#match? @method "^require")
            arguments: (argument_list
              (string
                (string_content) @module))) @require

          (call
            method: (identifier) @method (#eq? @method "include")
            arguments: (argument_list
              (constant) @module)) @include

          (call
            method: (identifier) @method (#eq? @method "extend")
            arguments: (argument_list
              (constant) @module)) @extend
        ]
        """

    def extract_symbol_from_match(
        self,
        node: "tree_sitter.Node",
        captures: dict[str, list["tree_sitter.Node"]],
        source: bytes,
        kind: SymbolKind,
    ) -> SymbolInfo | None:
        """Extract symbol information from a Ruby AST match."""
        # Get name
        name_nodes = captures.get("name", [])
        if not name_nodes:
            return None
        name = self.get_node_text(name_nodes[0], source)

        # Determine kind
        if "class" in captures:
            kind = SymbolKind.CLASS
        elif "module" in captures:
            kind = SymbolKind.MODULE
        elif "method" in captures or "singleton_method" in captures:
            kind = SymbolKind.METHOD

        # Get main node
        main_node = node
        for capture_name in ["class", "module", "method", "singleton_method"]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Determine visibility
        visibility = self._get_ruby_visibility(main_node, source)

        # For singleton methods (self.method), mark as static
        modifiers: list[str] = []
        if "singleton_method" in captures:
            modifiers.append("static")

        # Extract parameters
        params: list[ParameterInfo] = []
        if "params" in captures:
            params = self._extract_ruby_params(captures["params"][0], source)

        # Find parent class/module
        parent_name = self.find_parent_class(main_node, source)

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
            return_type=None,  # Ruby doesn't have return types
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
        """Extract import information from a Ruby AST match."""
        module_nodes = captures.get("module", [])
        if not module_nodes:
            return None

        module = self.get_node_text(module_nodes[0], source)

        # Determine main node
        main_node = node
        for capture_name in ["require", "include", "extend"]:
            if capture_name in captures:
                main_node = captures[capture_name][0]
                break

        # Check import type
        method_nodes = captures.get("method", [])
        import_type = ""
        if method_nodes:
            import_type = self.get_node_text(method_nodes[0], source)

        # require_relative is relative import
        is_relative = import_type == "require_relative"

        return ImportInfo(
            module=module,
            symbols=[],
            line=main_node.start_point[0] + 1,
            is_relative=is_relative,
            alias=None,
            is_wildcard=False,
        )

    def _get_ruby_visibility(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> Visibility:
        """Get Ruby method visibility.

        Ruby uses visibility modifiers that affect all following methods
        until the next modifier. We need to look back for the most recent
        visibility call.
        """
        # Look for visibility modifier before this method
        current = node.prev_sibling
        while current:
            if current.type == "call":
                call_text = self.get_node_text(current, source)
                if call_text.strip() == "private":
                    return Visibility.PRIVATE
                elif call_text.strip() == "protected":
                    return Visibility.PROTECTED
                elif call_text.strip() == "public":
                    return Visibility.PUBLIC
            current = current.prev_sibling

        # Default is public
        return Visibility.PUBLIC

    def _extract_ruby_params(
        self,
        params_node: "tree_sitter.Node",
        source: bytes,
    ) -> list[ParameterInfo]:
        """Extract Ruby method parameters."""
        params: list[ParameterInfo] = []

        for child in params_node.children:
            if child.type == "identifier":
                name = self.get_node_text(child, source)
                params.append(ParameterInfo(name=name))

            elif child.type == "optional_parameter":
                # Parameter with default value
                name = ""
                default_value = None
                for oc in child.children:
                    if oc.type == "identifier":
                        name = self.get_node_text(oc, source)
                    elif oc.type not in ("=", ","):
                        default_value = self.get_node_text(oc, source)

                if name:
                    params.append(
                        ParameterInfo(
                            name=name,
                            default_value=default_value,
                            is_optional=True,
                        )
                    )

            elif child.type == "splat_parameter":
                # *args parameter
                for sc in child.children:
                    if sc.type == "identifier":
                        name = self.get_node_text(sc, source)
                        params.append(
                            ParameterInfo(
                                name=name,
                                is_variadic=True,
                            )
                        )
                        break

            elif child.type == "hash_splat_parameter":
                # **kwargs parameter
                for hc in child.children:
                    if hc.type == "identifier":
                        name = self.get_node_text(hc, source)
                        params.append(
                            ParameterInfo(
                                name=name,
                                is_variadic=True,
                            )
                        )
                        break

            elif child.type == "block_parameter":
                # &block parameter
                for bc in child.children:
                    if bc.type == "identifier":
                        name = self.get_node_text(bc, source)
                        params.append(
                            ParameterInfo(
                                name=f"&{name}",
                            )
                        )
                        break

            elif child.type == "keyword_parameter":
                # keyword: parameter
                name = ""
                default_value = None
                for kc in child.children:
                    if kc.type == "identifier":
                        name = self.get_node_text(kc, source)
                    elif kc.type not in (":", ","):
                        default_value = self.get_node_text(kc, source)

                if name:
                    params.append(
                        ParameterInfo(
                            name=f"{name}:",
                            default_value=default_value,
                            is_optional=default_value is not None,
                        )
                    )

        return params

    def get_default_visibility(self, node: "tree_sitter.Node") -> Visibility:
        """Ruby default visibility is public."""
        return Visibility.PUBLIC

    def find_parent_class(
        self,
        node: "tree_sitter.Node",
        source: bytes,
    ) -> str | None:
        """Find the name of the containing class or module."""
        parent = node.parent
        while parent:
            if parent.type in ("class", "module"):
                for child in parent.children:
                    if child.type == "constant":
                        return self.get_node_text(child, source)
                    elif child.type == "scope_resolution":
                        for sc in child.children:
                            if sc.type == "constant":
                                return self.get_node_text(sc, source)
            parent = parent.parent
        return None
