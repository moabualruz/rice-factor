"""Language detection service for polyglot repositories.

This module provides the LanguageDetector that detects and analyzes
multiple programming languages within a repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class Language(Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    KOTLIN = "kotlin"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    CPP = "cpp"
    C = "c"
    SCALA = "scala"
    UNKNOWN = "unknown"


# File extension to language mapping
EXTENSION_MAP: dict[str, Language] = {
    ".py": Language.PYTHON,
    ".pyi": Language.PYTHON,
    ".pyw": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".mts": Language.TYPESCRIPT,
    ".cts": Language.TYPESCRIPT,
    ".java": Language.JAVA,
    ".kt": Language.KOTLIN,
    ".kts": Language.KOTLIN,
    ".cs": Language.CSHARP,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".rb": Language.RUBY,
    ".rake": Language.RUBY,
    ".php": Language.PHP,
    ".swift": Language.SWIFT,
    ".cpp": Language.CPP,
    ".cxx": Language.CPP,
    ".cc": Language.CPP,
    ".hpp": Language.CPP,
    ".hxx": Language.CPP,
    ".c": Language.C,
    ".h": Language.C,
    ".scala": Language.SCALA,
    ".sc": Language.SCALA,
}

# Build file to language mapping
BUILD_FILE_MAP: dict[str, Language] = {
    "setup.py": Language.PYTHON,
    "pyproject.toml": Language.PYTHON,
    "requirements.txt": Language.PYTHON,
    "Pipfile": Language.PYTHON,
    "setup.cfg": Language.PYTHON,
    "package.json": Language.JAVASCRIPT,
    "tsconfig.json": Language.TYPESCRIPT,
    "pom.xml": Language.JAVA,
    "build.gradle": Language.JAVA,
    "build.gradle.kts": Language.KOTLIN,
    "settings.gradle.kts": Language.KOTLIN,
    "*.csproj": Language.CSHARP,
    "*.sln": Language.CSHARP,
    "go.mod": Language.GO,
    "go.sum": Language.GO,
    "Cargo.toml": Language.RUST,
    "Cargo.lock": Language.RUST,
    "Gemfile": Language.RUBY,
    "Rakefile": Language.RUBY,
    "composer.json": Language.PHP,
    "Package.swift": Language.SWIFT,
    "CMakeLists.txt": Language.CPP,
    "Makefile": Language.C,
    "build.sbt": Language.SCALA,
}


@dataclass
class LanguageStats:
    """Statistics for a single language.

    Attributes:
        language: The language.
        file_count: Number of files.
        line_count: Total lines of code.
        byte_count: Total bytes.
        percentage: Percentage of total code.
    """

    language: Language
    file_count: int = 0
    line_count: int = 0
    byte_count: int = 0
    percentage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language.value,
            "file_count": self.file_count,
            "line_count": self.line_count,
            "byte_count": self.byte_count,
            "percentage": round(self.percentage, 2),
        }


@dataclass
class DetectionResult:
    """Result of language detection.

    Attributes:
        languages: List of detected languages with stats.
        primary_language: The most prevalent language.
        is_polyglot: Whether multiple languages are present.
        build_systems: Detected build systems by language.
        total_files: Total number of source files.
        total_lines: Total lines of code.
        analyzed_at: When analysis was performed.
    """

    languages: list[LanguageStats] = field(default_factory=list)
    primary_language: Language | None = None
    is_polyglot: bool = False
    build_systems: dict[str, list[str]] = field(default_factory=dict)
    total_files: int = 0
    total_lines: int = 0
    analyzed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "languages": [l.to_dict() for l in self.languages],
            "primary_language": (
                self.primary_language.value if self.primary_language else None
            ),
            "is_polyglot": self.is_polyglot,
            "build_systems": self.build_systems,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "analyzed_at": (
                self.analyzed_at.isoformat() if self.analyzed_at else None
            ),
        }


@dataclass
class LanguageDetector:
    """Service for detecting languages in a repository.

    Analyzes file extensions, build files, and code distribution
    to determine what languages are used in a project.

    Attributes:
        repo_root: Root directory of the repository.
        exclude_patterns: Patterns to exclude from analysis.
    """

    repo_root: Path
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            # Use path separators to avoid matching substrings
            # e.g., "dist" should not match "test_get_distribution"
            "/node_modules/",
            "/.git/",
            "/__pycache__/",
            "/.venv/",
            "/venv/",
            "/.env/",
            "/dist/",
            "/build/",
            "/target/",
            "/.idea/",
            "/.vscode/",
            "/vendor/",
            "/bin/",
            "/obj/",
            # Windows path separators
            "\\node_modules\\",
            "\\.git\\",
            "\\__pycache__\\",
            "\\.venv\\",
            "\\venv\\",
            "\\.env\\",
            "\\dist\\",
            "\\build\\",
            "\\target\\",
            "\\.idea\\",
            "\\.vscode\\",
            "\\vendor\\",
            "\\bin\\",
            "\\obj\\",
        ]
    )

    def detect(self) -> DetectionResult:
        """Detect languages in the repository.

        Returns:
            DetectionResult with language analysis.
        """
        stats_by_language: dict[Language, LanguageStats] = {}
        build_systems: dict[str, list[str]] = {}
        total_files = 0
        total_lines = 0

        # Walk the repository
        for file_path in self._walk_files():
            language = self._detect_file_language(file_path)

            if language == Language.UNKNOWN:
                continue

            total_files += 1

            if language not in stats_by_language:
                stats_by_language[language] = LanguageStats(language=language)

            stats = stats_by_language[language]
            stats.file_count += 1

            # Count lines and bytes
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                lines = len(content.split("\n"))
                stats.line_count += lines
                stats.byte_count += len(content.encode("utf-8"))
                total_lines += lines
            except OSError:
                pass

        # Detect build systems
        build_systems = self._detect_build_systems()

        # Add languages from build files that might not have source files yet
        for lang_name, files in build_systems.items():
            if files:
                try:
                    lang = Language(lang_name)
                    if lang not in stats_by_language:
                        stats_by_language[lang] = LanguageStats(language=lang)
                except ValueError:
                    pass

        # Calculate percentages and sort
        language_list = list(stats_by_language.values())
        for stats in language_list:
            if total_lines > 0:
                stats.percentage = (stats.line_count / total_lines) * 100

        language_list.sort(key=lambda x: x.line_count, reverse=True)

        # Determine primary language and polyglot status
        primary_language = language_list[0].language if language_list else None
        is_polyglot = len(language_list) > 1

        return DetectionResult(
            languages=language_list,
            primary_language=primary_language,
            is_polyglot=is_polyglot,
            build_systems=build_systems,
            total_files=total_files,
            total_lines=total_lines,
            analyzed_at=datetime.now(UTC),
        )

    def _walk_files(self) -> list[Path]:
        """Walk repository and yield source files.

        Yields:
            Path objects for each source file.
        """
        files: list[Path] = []

        for file_path in self.repo_root.rglob("*"):
            if not file_path.is_file():
                continue

            # Check exclusions
            path_str = str(file_path)
            if any(excl in path_str for excl in self.exclude_patterns):
                continue

            files.append(file_path)

        return files

    def _detect_file_language(self, file_path: Path) -> Language:
        """Detect language from file extension.

        Args:
            file_path: Path to file.

        Returns:
            Detected language or UNKNOWN.
        """
        suffix = file_path.suffix.lower()
        return EXTENSION_MAP.get(suffix, Language.UNKNOWN)

    def _detect_build_systems(self) -> dict[str, list[str]]:
        """Detect build systems by looking for build files.

        Returns:
            Dict mapping language to list of build file paths.
        """
        build_systems: dict[str, list[str]] = {}

        for build_file, language in BUILD_FILE_MAP.items():
            lang_name = language.value

            if lang_name not in build_systems:
                build_systems[lang_name] = []

            # Handle glob patterns
            if "*" in build_file:
                # Use glob pattern
                for match in self.repo_root.glob(build_file):
                    build_systems[lang_name].append(str(match))
                for match in self.repo_root.glob("**/" + build_file):
                    if str(match) not in build_systems[lang_name]:
                        build_systems[lang_name].append(str(match))
            else:
                # Direct file check
                direct_path = self.repo_root / build_file
                if direct_path.exists():
                    build_systems[lang_name].append(str(direct_path))

                # Also check subdirectories
                for match in self.repo_root.glob("**/" + build_file):
                    path_str = str(match)
                    if (
                        not any(excl in path_str for excl in self.exclude_patterns)
                        and path_str not in build_systems[lang_name]
                    ):
                        build_systems[lang_name].append(path_str)

        # Remove empty entries
        return {k: v for k, v in build_systems.items() if v}

    def get_language_for_file(self, file_path: Path) -> Language:
        """Get the language for a specific file.

        Args:
            file_path: Path to file.

        Returns:
            Detected language.
        """
        return self._detect_file_language(file_path)

    def get_files_for_language(
        self,
        language: Language,
    ) -> list[Path]:
        """Get all files for a specific language.

        Args:
            language: Language to filter by.

        Returns:
            List of file paths.
        """
        files: list[Path] = []

        for file_path in self._walk_files():
            if self._detect_file_language(file_path) == language:
                files.append(file_path)

        return files

    def get_distribution(self) -> dict[str, float]:
        """Get language distribution as percentages.

        Returns:
            Dict mapping language name to percentage.
        """
        result = self.detect()
        return {
            stats.language.value: stats.percentage
            for stats in result.languages
        }

    def is_language_present(self, language: Language) -> bool:
        """Check if a specific language is present.

        Args:
            language: Language to check.

        Returns:
            True if language is present.
        """
        for file_path in self._walk_files():
            if self._detect_file_language(file_path) == language:
                return True
        return False

    def get_primary_language(self) -> Language | None:
        """Get the primary (most prevalent) language.

        Returns:
            Primary language or None if empty.
        """
        result = self.detect()
        return result.primary_language
