"""Language-specific tree-sitter extractors.

Each language module provides query patterns and extraction logic
specific to that language's syntax.
"""

from rice_factor.adapters.parsing.languages.base import LanguageExtractor
from rice_factor.adapters.parsing.languages.csharp import CSharpExtractor
from rice_factor.adapters.parsing.languages.go import GoExtractor
from rice_factor.adapters.parsing.languages.java import JavaExtractor
from rice_factor.adapters.parsing.languages.javascript import JavaScriptExtractor
from rice_factor.adapters.parsing.languages.kotlin import KotlinExtractor
from rice_factor.adapters.parsing.languages.php import PHPExtractor
from rice_factor.adapters.parsing.languages.ruby import RubyExtractor
from rice_factor.adapters.parsing.languages.rust import RustExtractor
from rice_factor.adapters.parsing.languages.typescript import TypeScriptExtractor

__all__ = [
    "CSharpExtractor",
    "GoExtractor",
    "JavaExtractor",
    "JavaScriptExtractor",
    "KotlinExtractor",
    "LanguageExtractor",
    "PHPExtractor",
    "RubyExtractor",
    "RustExtractor",
    "TypeScriptExtractor",
]
