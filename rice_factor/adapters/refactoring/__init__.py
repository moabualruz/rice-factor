"""Language-specific refactoring tool adapters.

This package contains adapters for various language-specific refactoring tools:
- OpenRewrite: JVM (Java, Kotlin, Groovy)
- gopls: Go
- rust-analyzer: Rust
- jscodeshift: JavaScript/TypeScript

Each adapter implements RefactorToolPort and provides language-native
refactoring capabilities.
"""

from rice_factor.adapters.refactoring.diff_patch_adapter import DiffPatchAdapter
from rice_factor.adapters.refactoring.gopls_adapter import GoplsAdapter
from rice_factor.adapters.refactoring.jscodeshift_adapter import JscodeshiftAdapter
from rice_factor.adapters.refactoring.openrewrite_adapter import OpenRewriteAdapter
from rice_factor.adapters.refactoring.rust_analyzer_adapter import RustAnalyzerAdapter
from rice_factor.adapters.refactoring.tool_registry import RefactoringToolRegistry

__all__ = [
    "DiffPatchAdapter",
    "GoplsAdapter",
    "JscodeshiftAdapter",
    "OpenRewriteAdapter",
    "RefactoringToolRegistry",
    "RustAnalyzerAdapter",
]
