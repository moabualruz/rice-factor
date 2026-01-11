"""Refactoring tool registry.

Manages available refactoring tools and routes operations to the
appropriate tool based on language and capability.
"""

from pathlib import Path

from rice_factor.domain.ports.refactor import (
    RefactorOperation,
    RefactorRequest,
    RefactorResult,
    RefactorToolPort,
    ToolCapability,
)


class RefactoringToolRegistry:
    """Registry of available refactoring tools.

    Manages tool discovery, capability tracking, and operation routing.
    Tools are prioritized by specificity (language-specific > fallback).

    Attributes:
        project_root: Root directory of the project.
        tools: List of registered refactoring tools.
    """

    def __init__(
        self,
        project_root: Path,
        tools: list[RefactorToolPort] | None = None,
    ) -> None:
        """Initialize the registry.

        Args:
            project_root: Root directory of the project.
            tools: Optional list of tools. If not provided, will use defaults.
        """
        self.project_root = project_root
        self._tools: list[RefactorToolPort] = []
        self._capabilities: dict[str, ToolCapability] = {}

        if tools:
            for tool in tools:
                self.register(tool)
        else:
            self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default refactoring tools."""
        # Import adapters here to avoid circular imports
        from rice_factor.adapters.refactoring.diff_patch_adapter import (
            DiffPatchAdapter,
        )
        from rice_factor.adapters.refactoring.gopls_adapter import GoplsAdapter
        from rice_factor.adapters.refactoring.jscodeshift_adapter import (
            JscodeshiftAdapter,
        )
        from rice_factor.adapters.refactoring.openrewrite_adapter import (
            OpenRewriteAdapter,
        )
        from rice_factor.adapters.refactoring.rope_adapter import RopeAdapter
        from rice_factor.adapters.refactoring.roslyn_adapter import RoslynAdapter
        from rice_factor.adapters.refactoring.rector_adapter import RectorAdapter
        from rice_factor.adapters.refactoring.ruby_parser_adapter import (
            RubyParserAdapter,
        )
        from rice_factor.adapters.refactoring.rust_analyzer_adapter import (
            RustAnalyzerAdapter,
        )

        # Register in priority order (most specific first)
        self.register(RopeAdapter(self.project_root))  # Python
        self.register(OpenRewriteAdapter(self.project_root))  # Java/Kotlin
        self.register(RoslynAdapter(self.project_root))  # C#
        self.register(RubyParserAdapter(self.project_root))  # Ruby
        self.register(RectorAdapter(self.project_root))  # PHP
        self.register(GoplsAdapter(self.project_root))  # Go
        self.register(RustAnalyzerAdapter(self.project_root))  # Rust
        self.register(JscodeshiftAdapter(self.project_root))  # JS/TS
        # Fallback last
        self.register(DiffPatchAdapter(self.project_root))

    def register(self, tool: RefactorToolPort) -> None:
        """Register a refactoring tool.

        Args:
            tool: The tool to register.
        """
        self._tools.append(tool)
        self._update_capabilities(tool)

    def _update_capabilities(self, tool: RefactorToolPort) -> None:
        """Update capability cache for a tool.

        Args:
            tool: The tool to update capabilities for.
        """
        cap = tool.get_capability()
        for lang in cap.languages:
            # Only update if this tool is available or no other tool is available
            existing = self._capabilities.get(lang)
            if not existing or (cap.is_available and not existing.is_available):
                self._capabilities[lang] = cap

    def refresh(self) -> None:
        """Refresh tool availability status."""
        self._capabilities.clear()
        for tool in self._tools:
            self._update_capabilities(tool)

    def get_tool_for_language(
        self,
        language: str,
    ) -> RefactorToolPort | None:
        """Get the best available tool for a language.

        Args:
            language: Language identifier (e.g., "java", "python").

        Returns:
            Best available tool or None.
        """
        # First, try to find a language-specific tool
        for tool in self._tools:
            if language in tool.get_supported_languages() and tool.is_available():
                return tool

        # Fall back to wildcard (*) tools
        for tool in self._tools:
            if "*" in tool.get_supported_languages() and tool.is_available():
                return tool

        return None

    def get_tool_for_operation(
        self,
        language: str,
        operation: RefactorOperation,
    ) -> RefactorToolPort | None:
        """Get a tool that supports a specific operation for a language.

        Args:
            language: Language identifier.
            operation: Refactoring operation.

        Returns:
            Tool that supports the operation or None.
        """
        for tool in self._tools:
            languages = tool.get_supported_languages()
            supports_lang = language in languages or "*" in languages
            supports_op = operation in tool.get_supported_operations()
            if supports_lang and supports_op and tool.is_available():
                return tool

        return None

    def get_all_capabilities(self) -> list[ToolCapability]:
        """Get capabilities of all registered tools.

        Returns:
            List of tool capabilities.
        """
        return [tool.get_capability() for tool in self._tools]

    def get_available_tools(self) -> list[RefactorToolPort]:
        """Get all available (installed) tools.

        Returns:
            List of available tools.
        """
        return [tool for tool in self._tools if tool.is_available()]

    def supports_operation(
        self,
        language: str,
        operation: RefactorOperation,
    ) -> bool:
        """Check if an operation is supported for a language.

        Args:
            language: Language identifier.
            operation: Refactoring operation.

        Returns:
            True if the operation is supported.
        """
        return self.get_tool_for_operation(language, operation) is not None

    def execute(
        self,
        request: RefactorRequest,
        language: str,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute a refactoring operation using the best available tool.

        Args:
            request: The refactoring request.
            language: Language identifier for tool selection.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult from the selected tool.
        """
        tool = self.get_tool_for_operation(language, request.operation)

        if tool is None:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[
                    f"No tool available for {request.operation.value} "
                    f"in {language}"
                ],
                tool_used="none",
                dry_run=dry_run,
            )

        return tool.execute(request, dry_run)

    def detect_language(self, file_path: str) -> str:
        """Detect language from file extension.

        Args:
            file_path: Path to the file.

        Returns:
            Language identifier.
        """
        extension = Path(file_path).suffix.lower()

        extension_map = {
            ".java": "java",
            ".kt": "kotlin",
            ".kts": "kotlin",
            ".groovy": "groovy",
            ".scala": "scala",
            ".go": "go",
            ".rs": "rust",
            ".js": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".py": "python",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".ex": "elixir",
            ".exs": "elixir",
            ".clj": "clojure",
            ".erl": "erlang",
        }

        return extension_map.get(extension, "unknown")

    def get_summary(self) -> dict[str, list[str]]:
        """Get a summary of available tools and their capabilities.

        Returns:
            Dictionary mapping tool names to supported languages.
        """
        summary: dict[str, list[str]] = {}

        for tool in self._tools:
            cap = tool.get_capability()
            status = "available" if cap.is_available else "not installed"
            name = f"{cap.tool_name} ({status})"
            summary[name] = cap.languages

        return summary
