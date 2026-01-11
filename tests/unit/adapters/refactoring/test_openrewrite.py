"""Unit tests for OpenRewrite adapter."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.refactoring.openrewrite_adapter import OpenRewriteAdapter
from rice_factor.domain.ports.refactor import (
    RefactorOperation,
    RefactorRequest,
)


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def adapter(tmp_project: Path) -> OpenRewriteAdapter:
    """Create an OpenRewrite adapter for testing."""
    return OpenRewriteAdapter(tmp_project)


class TestOpenRewriteAdapter:
    """Tests for OpenRewriteAdapter."""

    def test_supported_languages(self, adapter: OpenRewriteAdapter) -> None:
        """Test that JVM languages are supported."""
        languages = adapter.get_supported_languages()
        assert "java" in languages
        assert "kotlin" in languages
        assert "groovy" in languages

    def test_supported_operations(self, adapter: OpenRewriteAdapter) -> None:
        """Test that expected operations are supported."""
        operations = adapter.get_supported_operations()
        assert RefactorOperation.RENAME in operations
        assert RefactorOperation.MOVE in operations

    def test_not_available_without_pom_or_gradle(
        self, adapter: OpenRewriteAdapter
    ) -> None:
        """Test that adapter is not available without build file."""
        assert adapter.is_available() is False

    def test_available_with_maven_pom(
        self, tmp_project: Path, adapter: OpenRewriteAdapter
    ) -> None:
        """Test that adapter is available with pom.xml containing OpenRewrite."""
        pom = tmp_project / "pom.xml"
        pom.write_text(
            """<?xml version="1.0"?>
            <project>
                <plugins>
                    <plugin>
                        <groupId>org.openrewrite.maven</groupId>
                        <artifactId>rewrite-maven-plugin</artifactId>
                        <version>5.0.0</version>
                    </plugin>
                </plugins>
            </project>
            """
        )
        assert adapter.is_available() is True
        assert adapter._build_tool == "maven"

    def test_available_with_gradle(
        self, tmp_project: Path, adapter: OpenRewriteAdapter
    ) -> None:
        """Test that adapter is available with build.gradle containing OpenRewrite."""
        gradle = tmp_project / "build.gradle"
        gradle.write_text(
            """
            plugins {
                id 'org.openrewrite.rewrite' version '6.0.0'
            }
            """
        )
        assert adapter.is_available() is True
        assert adapter._build_tool == "gradle"

    def test_available_with_gradle_kts(
        self, tmp_project: Path, adapter: OpenRewriteAdapter
    ) -> None:
        """Test that adapter is available with build.gradle.kts."""
        gradle = tmp_project / "build.gradle.kts"
        gradle.write_text(
            """
            plugins {
                id("org.openrewrite.rewrite") version "6.0.0"
            }
            """
        )
        assert adapter.is_available() is True
        assert adapter._build_tool == "gradle"

    def test_execute_not_available(self, adapter: OpenRewriteAdapter) -> None:
        """Test execute when OpenRewrite is not available."""
        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="com.example.OldClass",
            new_value="com.example.NewClass",
        )
        result = adapter.execute(request, dry_run=True)
        assert result.success is False
        assert "not available" in result.errors[0]

    def test_execute_unsupported_operation(
        self, tmp_project: Path, adapter: OpenRewriteAdapter
    ) -> None:
        """Test execute with unsupported operation."""
        # Make adapter available
        pom = tmp_project / "pom.xml"
        pom.write_text("<project><plugin>openrewrite</plugin></project>")

        request = RefactorRequest(
            operation=RefactorOperation.EXTRACT_METHOD,
            target="someMethod",
        )
        result = adapter.execute(request, dry_run=True)
        assert result.success is False
        assert "No recipe found" in result.errors[0]

    @patch("subprocess.run")
    def test_execute_rename_maven(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: OpenRewriteAdapter,
    ) -> None:
        """Test rename execution with Maven."""
        # Setup
        pom = tmp_project / "pom.xml"
        pom.write_text("<project><plugin>openrewrite</plugin></project>")

        mock_run.return_value = MagicMock(
            returncode=0, stdout="Modified: src/main/java/Foo.java", stderr=""
        )

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="com.example.OldClass",
            new_value="com.example.NewClass",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        assert result.tool_used == "OpenRewrite"
        assert result.dry_run is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "mvn" in call_args
        assert "rewrite:dryRun" in call_args

    @patch("subprocess.run")
    def test_execute_rename_maven_apply(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: OpenRewriteAdapter,
    ) -> None:
        """Test rename execution with apply (not dry-run)."""
        pom = tmp_project / "pom.xml"
        pom.write_text("<project><plugin>openrewrite</plugin></project>")

        mock_run.return_value = MagicMock(
            returncode=0, stdout="Modified files", stderr=""
        )

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="com.example.OldClass",
            new_value="com.example.NewClass",
        )

        result = adapter.execute(request, dry_run=False)

        assert result.success is True
        assert result.dry_run is False
        call_args = mock_run.call_args[0][0]
        assert "rewrite:run" in call_args

    @patch("subprocess.run")
    def test_execute_timeout(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: OpenRewriteAdapter,
    ) -> None:
        """Test handling of command timeout."""
        import subprocess

        pom = tmp_project / "pom.xml"
        pom.write_text("<project><plugin>openrewrite</plugin></project>")

        mock_run.side_effect = subprocess.TimeoutExpired("mvn", 300)

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldClass",
            new_value="NewClass",
        )

        result = adapter.execute(request)
        assert result.success is False
        assert "timed out" in result.errors[0]

    @patch("subprocess.run")
    def test_execute_command_not_found(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: OpenRewriteAdapter,
    ) -> None:
        """Test handling of missing mvn/gradle command."""
        pom = tmp_project / "pom.xml"
        pom.write_text("<project><plugin>openrewrite</plugin></project>")

        mock_run.side_effect = FileNotFoundError("mvn not found")

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldClass",
            new_value="NewClass",
        )

        result = adapter.execute(request)
        assert result.success is False
        assert "not found" in result.errors[0].lower()

    @patch("subprocess.run")
    def test_execute_command_failure(
        self,
        mock_run: MagicMock,
        tmp_project: Path,
        adapter: OpenRewriteAdapter,
    ) -> None:
        """Test handling of command failure."""
        pom = tmp_project / "pom.xml"
        pom.write_text("<project><plugin>openrewrite</plugin></project>")

        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Recipe not found"
        )

        request = RefactorRequest(
            operation=RefactorOperation.RENAME,
            target="OldClass",
            new_value="NewClass",
        )

        result = adapter.execute(request)
        assert result.success is False
        assert "Recipe not found" in result.errors[0]

    @patch("subprocess.run")
    def test_rollback(
        self, mock_run: MagicMock, adapter: OpenRewriteAdapter
    ) -> None:
        """Test rollback functionality."""
        mock_run.return_value = MagicMock(returncode=0)

        from rice_factor.domain.ports.refactor import RefactorResult

        result = RefactorResult(
            success=True, changes=[], errors=[], tool_used="OpenRewrite", dry_run=False
        )

        assert adapter.rollback(result) is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "checkout" in call_args

    def test_get_version_maven(self, tmp_project: Path) -> None:
        """Test version extraction from pom.xml."""
        pom = tmp_project / "pom.xml"
        pom.write_text(
            """<?xml version="1.0"?>
            <project>
                <plugins>
                    <plugin>
                        <groupId>org.openrewrite.maven</groupId>
                        <artifactId>rewrite-maven-plugin</artifactId>
                        <version>5.2.1</version>
                    </plugin>
                </plugins>
            </project>
            """
        )
        adapter = OpenRewriteAdapter(tmp_project)
        adapter.is_available()  # Triggers detection
        version = adapter.get_version()
        assert version == "5.2.1"

    def test_get_capability(
        self, tmp_project: Path, adapter: OpenRewriteAdapter
    ) -> None:
        """Test capability reporting."""
        cap = adapter.get_capability()
        assert cap.tool_name == "OpenRewriteAdapter"
        assert "java" in cap.languages
        assert RefactorOperation.RENAME in cap.operations
        assert cap.is_available is False  # No pom.xml


class TestOpenRewriteAdapterMoveOperation:
    """Tests for move/package rename operations."""

    @patch("subprocess.run")
    def test_move_package(
        self,
        mock_run: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test package move operation."""
        pom = tmp_path / "pom.xml"
        pom.write_text("<project><plugin>openrewrite</plugin></project>")

        adapter = OpenRewriteAdapter(tmp_path)

        mock_run.return_value = MagicMock(
            returncode=0, stdout="Modified files", stderr=""
        )

        request = RefactorRequest(
            operation=RefactorOperation.MOVE,
            target="com.old.package",
            new_value="com.new.package",
        )

        result = adapter.execute(request, dry_run=True)

        assert result.success is True
        call_args = mock_run.call_args[0][0]
        assert "org.openrewrite.java.ChangePackage" in str(call_args)
