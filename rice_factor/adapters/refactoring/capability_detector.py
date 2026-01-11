"""Capability detector for refactoring tools.

Automatically detects available refactoring tools at runtime and provides
capability information for each supported language.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field


@dataclass
class ToolAvailability:
    """Availability information for a refactoring tool.

    Attributes:
        name: Name of the tool.
        available: Whether the tool is installed and usable.
        version: Version string if available.
        languages: Languages supported by this tool.
        operations: Operations supported by this tool.
    """

    name: str
    available: bool
    version: str | None = None
    languages: list[str] = field(default_factory=list)
    operations: list[str] = field(default_factory=list)


@dataclass
class LanguageCapability:
    """Capability information for a language.

    Attributes:
        language: Language identifier.
        adapter: Name of the adapter used.
        available: Whether the adapter is available.
        operations: Dictionary of operation -> supported status.
    """

    language: str
    adapter: str
    available: bool
    operations: dict[str, bool] = field(default_factory=dict)


class CapabilityDetector:
    """Detects available refactoring tools at runtime.

    Probes for installed tools and provides capability information
    for tool selection and user feedback.

    Attributes:
        _cache: Cached tool availability results.
    """

    def __init__(self) -> None:
        """Initialize the detector."""
        self._cache: dict[str, ToolAvailability] | None = None

    def detect_all(self) -> dict[str, ToolAvailability]:
        """Probe for all supported refactoring tools.

        Returns:
            Dictionary mapping tool names to their availability.
        """
        if self._cache is not None:
            return self._cache

        self._cache = {
            "rope": self._detect_rope(),
            "openrewrite": self._detect_openrewrite(),
            "roslyn": self._detect_roslyn(),
            "ruby_parser": self._detect_ruby_parser(),
            "rector": self._detect_rector(),
            "jscodeshift": self._detect_jscodeshift(),
            "gopls": self._detect_gopls(),
            "rust_analyzer": self._detect_rust_analyzer(),
        }

        return self._cache

    def refresh(self) -> dict[str, ToolAvailability]:
        """Refresh the cache and re-detect all tools.

        Returns:
            Dictionary mapping tool names to their availability.
        """
        self._cache = None
        return self.detect_all()

    def get_tool(self, name: str) -> ToolAvailability | None:
        """Get availability for a specific tool.

        Args:
            name: Tool name.

        Returns:
            ToolAvailability or None if unknown tool.
        """
        return self.detect_all().get(name)

    def is_available(self, name: str) -> bool:
        """Check if a specific tool is available.

        Args:
            name: Tool name.

        Returns:
            True if the tool is available.
        """
        tool = self.get_tool(name)
        return tool.available if tool else False

    def get_language_capabilities(self) -> list[LanguageCapability]:
        """Get capabilities for all supported languages.

        Returns:
            List of LanguageCapability objects.
        """
        tools = self.detect_all()

        # Language to tool mapping
        language_adapters = {
            "python": "rope",
            "java": "openrewrite",
            "kotlin": "openrewrite",
            "groovy": "openrewrite",
            "csharp": "roslyn",
            "javascript": "jscodeshift",
            "typescript": "jscodeshift",
            "jsx": "jscodeshift",
            "tsx": "jscodeshift",
            "go": "gopls",
            "rust": "rust_analyzer",
            "ruby": "ruby_parser",
            "php": "rector",
        }

        capabilities: list[LanguageCapability] = []

        for lang, adapter_name in language_adapters.items():
            tool = tools.get(adapter_name)
            if tool:
                capabilities.append(
                    LanguageCapability(
                        language=lang,
                        adapter=adapter_name,
                        available=tool.available,
                        operations=dict.fromkeys(tool.operations, tool.available),
                    )
                )
            else:
                capabilities.append(
                    LanguageCapability(
                        language=lang,
                        adapter=adapter_name,
                        available=False,
                        operations={},
                    )
                )

        return capabilities

    def _detect_rope(self) -> ToolAvailability:
        """Detect Rope availability.

        Returns:
            ToolAvailability for Rope.
        """
        version = self._check_python_package("rope")
        return ToolAvailability(
            name="rope",
            available=version is not None,
            version=version,
            languages=["python"],
            operations=["rename", "move", "extract_method", "extract_variable"],
        )

    def _detect_openrewrite(self) -> ToolAvailability:
        """Detect OpenRewrite availability.

        Returns:
            ToolAvailability for OpenRewrite.
        """
        # Check for OpenRewrite CLI or Maven/Gradle plugin
        available = self._check_command("rewrite") or self._check_maven_plugin(
            "org.openrewrite.maven:rewrite-maven-plugin"
        )
        return ToolAvailability(
            name="openrewrite",
            available=available,
            version=None,  # Version detection is complex for plugins
            languages=["java", "kotlin", "groovy"],
            operations=["rename", "move", "extract_interface", "enforce_dependency"],
        )

    def _detect_roslyn(self) -> ToolAvailability:
        """Detect Roslyn/dotnet availability.

        Returns:
            ToolAvailability for Roslyn.
        """
        version = self._check_command_version("dotnet", ["--version"])
        return ToolAvailability(
            name="roslyn",
            available=version is not None,
            version=version,
            languages=["csharp"],
            operations=["rename", "move", "extract_interface", "enforce_dependency"],
        )

    def _detect_ruby_parser(self) -> ToolAvailability:
        """Detect Ruby Parser gem availability.

        Returns:
            ToolAvailability for Ruby Parser.
        """
        version = self._check_ruby_gem("parser")
        return ToolAvailability(
            name="ruby_parser",
            available=version is not None,
            version=version,
            languages=["ruby"],
            operations=["rename", "move", "extract_interface", "enforce_dependency"],
        )

    def _detect_rector(self) -> ToolAvailability:
        """Detect Rector availability.

        Returns:
            ToolAvailability for Rector.
        """
        # Check for local or global Rector installation
        available = self._check_command("rector") or self._check_php_package(
            "rector/rector"
        )
        version = None
        if available:
            version = self._check_command_version("rector", ["--version"])
        return ToolAvailability(
            name="rector",
            available=available,
            version=version,
            languages=["php"],
            operations=["rename", "move", "extract_interface", "enforce_dependency"],
        )

    def _detect_jscodeshift(self) -> ToolAvailability:
        """Detect jscodeshift availability.

        Returns:
            ToolAvailability for jscodeshift.
        """
        version = self._check_npm_package("jscodeshift")
        return ToolAvailability(
            name="jscodeshift",
            available=version is not None,
            version=version,
            languages=["javascript", "typescript", "jsx", "tsx"],
            operations=["rename", "move"],
        )

    def _detect_gopls(self) -> ToolAvailability:
        """Detect gopls availability.

        Returns:
            ToolAvailability for gopls.
        """
        version = self._check_command_version("gopls", ["version"])
        return ToolAvailability(
            name="gopls",
            available=version is not None,
            version=version,
            languages=["go"],
            operations=["rename", "move"],
        )

    def _detect_rust_analyzer(self) -> ToolAvailability:
        """Detect rust-analyzer availability.

        Returns:
            ToolAvailability for rust-analyzer.
        """
        version = self._check_command_version("rust-analyzer", ["--version"])
        return ToolAvailability(
            name="rust_analyzer",
            available=version is not None,
            version=version,
            languages=["rust"],
            operations=["rename", "move"],
        )

    def _check_python_package(self, package: str) -> str | None:
        """Check if a Python package is installed.

        Args:
            package: Package name.

        Returns:
            Version string or None if not installed.
        """
        try:
            import importlib.metadata

            return importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            return None

    def _check_command(self, cmd: str) -> bool:
        """Check if a command is available.

        Args:
            cmd: Command name.

        Returns:
            True if the command exists.
        """
        return shutil.which(cmd) is not None

    def _check_command_version(
        self,
        cmd: str,
        args: list[str],
    ) -> str | None:
        """Check command availability and get version.

        Args:
            cmd: Command name.
            args: Arguments to get version.

        Returns:
            Version string or None if not available.
        """
        if not self._check_command(cmd):
            return None

        try:
            result = subprocess.run(
                [cmd, *args],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Return first non-empty line
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        return line.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return None

    def _check_ruby_gem(self, gem: str) -> str | None:
        """Check if a Ruby gem is installed.

        Args:
            gem: Gem name.

        Returns:
            Version string or None if not installed.
        """
        try:
            result = subprocess.run(
                ["gem", "list", "-i", gem],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip().lower() == "true":
                # Get version
                version_result = subprocess.run(
                    ["gem", "list", gem],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if version_result.returncode == 0:
                    # Parse version from output like "parser (3.2.0)"
                    for line in version_result.stdout.split("\n"):
                        if gem in line and "(" in line:
                            start = line.index("(") + 1
                            end = line.index(")")
                            return line[start:end]
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return None

    def _check_php_package(self, package: str) -> bool:
        """Check if a PHP Composer package is installed.

        Args:
            package: Package name (vendor/package).

        Returns:
            True if installed.
        """
        try:
            result = subprocess.run(
                ["composer", "show", package],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def _check_npm_package(self, package: str) -> str | None:
        """Check if an npm package is installed globally.

        Args:
            package: Package name.

        Returns:
            Version string or None if not installed.
        """
        try:
            result = subprocess.run(
                ["npm", "list", "-g", package, "--depth=0"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Parse version from output
                for line in result.stdout.split("\n"):
                    if package in line and "@" in line:
                        # Format: "package@version"
                        parts = line.split("@")
                        if len(parts) >= 2:
                            return parts[-1].strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return None

    def _check_maven_plugin(self, _plugin: str) -> bool:
        """Check if a Maven plugin is available.

        Args:
            _plugin: Plugin coordinates (groupId:artifactId). Not used currently
                     as we just check if Maven is available.

        Returns:
            True if Maven is available (we can't easily check plugin).
        """
        # We just check if Maven is available
        # Actual plugin availability depends on project pom.xml
        return self._check_command("mvn")

    def format_capabilities_table(self) -> str:
        """Format capabilities as a human-readable table.

        Returns:
            Formatted table string.
        """
        capabilities = self.get_language_capabilities()

        # Header
        lines = [
            "Language    | move_file | rename | extract_if | enforce_dep | Adapter",
            "------------|-----------|--------|------------|-------------|----------",
        ]

        for cap in sorted(capabilities, key=lambda c: c.language):
            move = "yes" if cap.operations.get("move", False) else " - "
            rename = "yes" if cap.operations.get("rename", False) else " - "
            extract = "yes" if cap.operations.get("extract_interface", False) else " - "
            enforce = "yes" if cap.operations.get("enforce_dependency", False) else " - "

            status = cap.adapter if cap.available else f"{cap.adapter} (not installed)"
            lines.append(
                f"{cap.language:<11} | {move:^9} | {rename:^6} | {extract:^10} | {enforce:^11} | {status}"
            )

        return "\n".join(lines)


# Module-level singleton for convenience
_detector: CapabilityDetector | None = None


def get_detector() -> CapabilityDetector:
    """Get the global capability detector instance.

    Returns:
        CapabilityDetector singleton.
    """
    global _detector
    if _detector is None:
        _detector = CapabilityDetector()
    return _detector


def detect_all() -> dict[str, ToolAvailability]:
    """Detect all available tools using the global detector.

    Returns:
        Dictionary mapping tool names to their availability.
    """
    return get_detector().detect_all()


def is_available(tool_name: str) -> bool:
    """Check if a tool is available using the global detector.

    Args:
        tool_name: Name of the tool.

    Returns:
        True if the tool is available.
    """
    return get_detector().is_available(tool_name)
