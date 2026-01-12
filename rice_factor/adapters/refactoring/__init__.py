"""Language-specific refactoring tool adapters.

This package contains adapters for various language-specific refactoring tools:
- Rope: Python
- OpenRewrite: JVM (Java, Kotlin, Groovy)
- Roslyn: C# (.NET)
- RubyParser: Ruby
- Rector: PHP
- gopls: Go
- rust-analyzer: Rust
- jscodeshift: JavaScript/TypeScript

Each adapter implements RefactorToolPort and provides language-native
refactoring capabilities.
"""

from rice_factor.adapters.refactoring.capability_detector import (
    CapabilityDetector,
    LanguageCapability,
    ToolAvailability,
    detect_all,
    get_detector,
    is_available,
)
from rice_factor.adapters.refactoring.diff_patch_adapter import DiffPatchAdapter
from rice_factor.adapters.refactoring.gopls_adapter import GoplsAdapter
from rice_factor.adapters.refactoring.jscodeshift_adapter import (
    JscodeshiftAdapter,
    JsDependencyRule,
    JsDependencyViolation,
)
from rice_factor.adapters.refactoring.openrewrite_adapter import OpenRewriteAdapter
from rice_factor.adapters.refactoring.rector_adapter import RectorAdapter
from rice_factor.adapters.refactoring.rope_adapter import RopeAdapter
from rice_factor.adapters.refactoring.roslyn_adapter import RoslynAdapter
from rice_factor.adapters.refactoring.ruby_parser_adapter import RubyParserAdapter
from rice_factor.adapters.refactoring.rust_analyzer_adapter import RustAnalyzerAdapter
from rice_factor.adapters.refactoring.tool_registry import RefactoringToolRegistry

__all__ = [
    "CapabilityDetector",
    "DiffPatchAdapter",
    "GoplsAdapter",
    "JsDependencyRule",
    "JsDependencyViolation",
    "JscodeshiftAdapter",
    "LanguageCapability",
    "OpenRewriteAdapter",
    "RectorAdapter",
    "RefactoringToolRegistry",
    "RopeAdapter",
    "RoslynAdapter",
    "RubyParserAdapter",
    "RustAnalyzerAdapter",
    "ToolAvailability",
    "detect_all",
    "get_detector",
    "is_available",
]
