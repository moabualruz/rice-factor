"""Tests for LanguageDetector."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rice_factor.domain.services.language_detector import (
    BUILD_FILE_MAP,
    EXTENSION_MAP,
    DetectionResult,
    Language,
    LanguageDetector,
    LanguageStats,
)

if TYPE_CHECKING:
    pass


class TestLanguage:
    """Tests for Language enum."""

    def test_all_languages_exist(self) -> None:
        """Test all languages are defined."""
        assert Language.PYTHON
        assert Language.JAVASCRIPT
        assert Language.TYPESCRIPT
        assert Language.JAVA
        assert Language.KOTLIN
        assert Language.CSHARP
        assert Language.GO
        assert Language.RUST
        assert Language.RUBY
        assert Language.PHP
        assert Language.UNKNOWN


class TestExtensionMap:
    """Tests for extension mapping."""

    def test_python_extensions(self) -> None:
        """Test Python extensions."""
        assert EXTENSION_MAP[".py"] == Language.PYTHON
        assert EXTENSION_MAP[".pyi"] == Language.PYTHON

    def test_javascript_extensions(self) -> None:
        """Test JavaScript extensions."""
        assert EXTENSION_MAP[".js"] == Language.JAVASCRIPT
        assert EXTENSION_MAP[".jsx"] == Language.JAVASCRIPT
        assert EXTENSION_MAP[".mjs"] == Language.JAVASCRIPT

    def test_typescript_extensions(self) -> None:
        """Test TypeScript extensions."""
        assert EXTENSION_MAP[".ts"] == Language.TYPESCRIPT
        assert EXTENSION_MAP[".tsx"] == Language.TYPESCRIPT

    def test_java_extensions(self) -> None:
        """Test Java extensions."""
        assert EXTENSION_MAP[".java"] == Language.JAVA

    def test_rust_extensions(self) -> None:
        """Test Rust extensions."""
        assert EXTENSION_MAP[".rs"] == Language.RUST


class TestBuildFileMap:
    """Tests for build file mapping."""

    def test_python_build_files(self) -> None:
        """Test Python build files."""
        assert BUILD_FILE_MAP["setup.py"] == Language.PYTHON
        assert BUILD_FILE_MAP["pyproject.toml"] == Language.PYTHON

    def test_javascript_build_files(self) -> None:
        """Test JavaScript build files."""
        assert BUILD_FILE_MAP["package.json"] == Language.JAVASCRIPT

    def test_java_build_files(self) -> None:
        """Test Java build files."""
        assert BUILD_FILE_MAP["pom.xml"] == Language.JAVA
        assert BUILD_FILE_MAP["build.gradle"] == Language.JAVA


class TestLanguageStats:
    """Tests for LanguageStats model."""

    def test_creation(self) -> None:
        """Test stats creation."""
        stats = LanguageStats(language=Language.PYTHON)
        assert stats.language == Language.PYTHON
        assert stats.file_count == 0

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        stats = LanguageStats(
            language=Language.JAVASCRIPT,
            file_count=10,
            line_count=500,
            byte_count=10000,
            percentage=45.5,
        )
        d = stats.to_dict()
        assert d["language"] == "javascript"
        assert d["file_count"] == 10
        assert d["percentage"] == 45.5


class TestDetectionResult:
    """Tests for DetectionResult model."""

    def test_creation(self) -> None:
        """Test result creation."""
        result = DetectionResult()
        assert result.languages == []
        assert result.is_polyglot is False

    def test_with_languages(self) -> None:
        """Test result with languages."""
        result = DetectionResult(
            languages=[
                LanguageStats(language=Language.PYTHON, line_count=1000),
                LanguageStats(language=Language.JAVASCRIPT, line_count=500),
            ],
            primary_language=Language.PYTHON,
            is_polyglot=True,
        )
        assert len(result.languages) == 2
        assert result.is_polyglot is True

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        result = DetectionResult(
            primary_language=Language.PYTHON,
            total_files=100,
        )
        d = result.to_dict()
        assert d["primary_language"] == "python"
        assert d["total_files"] == 100


class TestLanguageDetector:
    """Tests for LanguageDetector."""

    def test_creation(self, tmp_path: Path) -> None:
        """Test detector creation."""
        detector = LanguageDetector(repo_root=tmp_path)
        assert detector.repo_root == tmp_path
        assert len(detector.exclude_patterns) > 0

    def test_detect_empty_directory(self, tmp_path: Path) -> None:
        """Test detecting empty directory."""
        detector = LanguageDetector(repo_root=tmp_path)
        result = detector.detect()

        assert result.total_files == 0
        assert result.is_polyglot is False

    def test_detect_single_language(self, tmp_path: Path) -> None:
        """Test detecting single language."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create Python files
        (tmp_path / "main.py").write_text("print('hello')\n")
        (tmp_path / "utils.py").write_text("def helper(): pass\n")

        result = detector.detect()

        assert result.total_files == 2
        assert result.primary_language == Language.PYTHON
        assert result.is_polyglot is False

    def test_detect_multiple_languages(self, tmp_path: Path) -> None:
        """Test detecting multiple languages."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create mixed language files
        (tmp_path / "main.py").write_text("print('hello')\n")
        (tmp_path / "app.js").write_text("console.log('hello');\n")
        (tmp_path / "Main.java").write_text("public class Main {}\n")

        result = detector.detect()

        assert result.total_files == 3
        assert result.is_polyglot is True
        assert len(result.languages) >= 3

    def test_detect_percentages(self, tmp_path: Path) -> None:
        """Test language percentages."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create unequal files
        (tmp_path / "large.py").write_text("x = 1\n" * 100)  # 100 lines
        (tmp_path / "small.js").write_text("x = 1;\n" * 10)  # 10 lines

        result = detector.detect()

        # Python should have higher percentage
        py_stats = next(
            s for s in result.languages if s.language == Language.PYTHON
        )
        js_stats = next(
            s for s in result.languages if s.language == Language.JAVASCRIPT
        )

        assert py_stats.percentage > js_stats.percentage

    def test_detect_build_systems_python(self, tmp_path: Path) -> None:
        """Test detecting Python build systems."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create pyproject.toml
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        result = detector.detect()

        assert "python" in result.build_systems
        assert len(result.build_systems["python"]) > 0

    def test_detect_build_systems_javascript(self, tmp_path: Path) -> None:
        """Test detecting JavaScript build systems."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create package.json
        (tmp_path / "package.json").write_text('{"name": "test"}\n')

        result = detector.detect()

        assert "javascript" in result.build_systems

    def test_detect_build_systems_java(self, tmp_path: Path) -> None:
        """Test detecting Java build systems."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create pom.xml
        (tmp_path / "pom.xml").write_text("<project></project>\n")

        result = detector.detect()

        assert "java" in result.build_systems

    def test_exclude_patterns(self, tmp_path: Path) -> None:
        """Test exclude patterns."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create files in excluded directory
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "lib.js").write_text("// library\n")

        # Create files in included directory
        (tmp_path / "src.py").write_text("# source\n")

        result = detector.detect()

        # Should only count src.py
        assert result.total_files == 1
        assert result.primary_language == Language.PYTHON

    def test_get_language_for_file(self, tmp_path: Path) -> None:
        """Test getting language for specific file."""
        detector = LanguageDetector(repo_root=tmp_path)

        assert detector.get_language_for_file(Path("test.py")) == Language.PYTHON
        assert detector.get_language_for_file(Path("test.js")) == Language.JAVASCRIPT
        assert detector.get_language_for_file(Path("test.txt")) == Language.UNKNOWN

    def test_get_files_for_language(self, tmp_path: Path) -> None:
        """Test getting files for a language."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create mixed files
        (tmp_path / "a.py").write_text("# a\n")
        (tmp_path / "b.py").write_text("# b\n")
        (tmp_path / "c.js").write_text("// c\n")

        py_files = detector.get_files_for_language(Language.PYTHON)

        assert len(py_files) == 2

    def test_get_distribution(self, tmp_path: Path) -> None:
        """Test getting distribution."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create files with multiple lines to ensure detection
        (tmp_path / "a.py").write_text("x = 1\ny = 2\n")
        (tmp_path / "b.js").write_text("x = 1;\ny = 2;\n")

        result = detector.detect()
        # Verify files were detected
        assert result.total_files == 2

        dist = detector.get_distribution()

        assert "python" in dist
        assert "javascript" in dist
        assert abs(dist["python"] + dist["javascript"] - 100) < 1

    def test_is_language_present(self, tmp_path: Path) -> None:
        """Test checking language presence."""
        detector = LanguageDetector(repo_root=tmp_path)

        (tmp_path / "main.py").write_text("# python\n")

        assert detector.is_language_present(Language.PYTHON) is True
        assert detector.is_language_present(Language.JAVA) is False

    def test_get_primary_language(self, tmp_path: Path) -> None:
        """Test getting primary language."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create more Python than JavaScript
        (tmp_path / "a.py").write_text("x = 1\n" * 100)
        (tmp_path / "b.js").write_text("x = 1;\n" * 10)

        primary = detector.get_primary_language()

        assert primary == Language.PYTHON

    def test_get_primary_language_empty(self, tmp_path: Path) -> None:
        """Test getting primary language from empty repo."""
        detector = LanguageDetector(repo_root=tmp_path)

        primary = detector.get_primary_language()

        assert primary is None

    def test_typescript_tsx(self, tmp_path: Path) -> None:
        """Test TypeScript/TSX detection."""
        detector = LanguageDetector(repo_root=tmp_path)

        (tmp_path / "component.tsx").write_text("const App = () => <div/>;\n")
        (tmp_path / "utils.ts").write_text("export const x = 1;\n")

        result = detector.detect()

        ts_stats = next(
            s for s in result.languages if s.language == Language.TYPESCRIPT
        )
        assert ts_stats.file_count == 2

    def test_kotlin_kts(self, tmp_path: Path) -> None:
        """Test Kotlin detection."""
        detector = LanguageDetector(repo_root=tmp_path)

        (tmp_path / "Main.kt").write_text("fun main() {}\n")
        (tmp_path / "build.gradle.kts").write_text("plugins {}\n")

        result = detector.detect()

        # Should detect Kotlin files and build system
        assert detector.is_language_present(Language.KOTLIN)

    def test_nested_directories(self, tmp_path: Path) -> None:
        """Test detecting in nested directories."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create nested structure
        src = tmp_path / "src" / "main"
        src.mkdir(parents=True)
        (src / "app.py").write_text("# app\n")

        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_app.py").write_text("# test\n")

        result = detector.detect()

        assert result.total_files == 2

    def test_subdirectory_build_files(self, tmp_path: Path) -> None:
        """Test detecting build files in subdirectories."""
        detector = LanguageDetector(repo_root=tmp_path)

        # Create nested package.json (using 'src' not 'packages' to avoid exclusions)
        subdir = tmp_path / "src" / "frontend"
        subdir.mkdir(parents=True)
        (subdir / "package.json").write_text('{"name": "frontend"}\n')

        result = detector.detect()

        assert "javascript" in result.build_systems
        assert len(result.build_systems["javascript"]) > 0

    def test_csproj_detection(self, tmp_path: Path) -> None:
        """Test C# project file detection."""
        detector = LanguageDetector(repo_root=tmp_path)

        (tmp_path / "MyApp.csproj").write_text("<Project></Project>\n")

        result = detector.detect()

        assert "csharp" in result.build_systems

    def test_rust_cargo(self, tmp_path: Path) -> None:
        """Test Rust Cargo detection."""
        detector = LanguageDetector(repo_root=tmp_path)

        (tmp_path / "Cargo.toml").write_text("[package]\nname = 'test'\n")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.rs").write_text("fn main() {}\n")

        result = detector.detect()

        assert "rust" in result.build_systems
        assert detector.is_language_present(Language.RUST)

    def test_go_mod(self, tmp_path: Path) -> None:
        """Test Go module detection."""
        detector = LanguageDetector(repo_root=tmp_path)

        (tmp_path / "go.mod").write_text("module test\n")
        (tmp_path / "main.go").write_text("package main\n")

        result = detector.detect()

        assert "go" in result.build_systems
        assert detector.is_language_present(Language.GO)
