"""OpenRewrite adapter for JVM refactoring.

OpenRewrite provides AST-based refactoring for Java, Kotlin, and Groovy
through Maven or Gradle plugins. This adapter wraps OpenRewrite to
provide language-native refactoring capabilities.
"""

import subprocess
from pathlib import Path
from typing import ClassVar

from rice_factor.domain.ports.refactor import (
    RefactorChange,
    RefactorOperation,
    RefactorRequest,
    RefactorResult,
    RefactorToolPort,
)


class OpenRewriteAdapter(RefactorToolPort):
    """Adapter for OpenRewrite (JVM refactoring).

    OpenRewrite uses "recipes" to perform refactoring operations.
    This adapter maps RefactorOperation enums to OpenRewrite recipes
    and executes them via Maven or Gradle.

    Attributes:
        project_root: Root directory of the project.
        build_tool: Detected build tool ("maven" or "gradle").
    """

    LANGUAGES: ClassVar[list[str]] = ["java", "kotlin", "groovy"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.MOVE,
        RefactorOperation.CHANGE_SIGNATURE,
    ]

    # Mapping of operations to OpenRewrite recipes
    RECIPE_MAP: ClassVar[dict[RefactorOperation, str]] = {
        RefactorOperation.RENAME: "org.openrewrite.java.ChangeType",
        RefactorOperation.MOVE: "org.openrewrite.java.ChangePackage",
    }

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the JVM project.
        """
        self.project_root = project_root
        self._build_tool: str | None = None
        self._version: str | None = None

    def get_supported_languages(self) -> list[str]:
        """Return supported JVM languages."""
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return supported refactoring operations."""
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if OpenRewrite is available in the project.

        Looks for Maven or Gradle build files with OpenRewrite plugin
        configured.

        Returns:
            True if OpenRewrite plugin is detected.
        """
        # Check Maven
        pom = self.project_root / "pom.xml"
        if pom.exists():
            try:
                content = pom.read_text(encoding="utf-8")
                if "openrewrite" in content.lower():
                    self._build_tool = "maven"
                    return True
            except OSError:
                pass

        # Check Gradle (Groovy DSL)
        gradle = self.project_root / "build.gradle"
        if gradle.exists():
            try:
                content = gradle.read_text(encoding="utf-8")
                if "openrewrite" in content.lower():
                    self._build_tool = "gradle"
                    return True
            except OSError:
                pass

        # Check Gradle (Kotlin DSL)
        gradle_kts = self.project_root / "build.gradle.kts"
        if gradle_kts.exists():
            try:
                content = gradle_kts.read_text(encoding="utf-8")
                if "openrewrite" in content.lower():
                    self._build_tool = "gradle"
                    return True
            except OSError:
                pass

        return False

    def get_version(self) -> str | None:
        """Get OpenRewrite plugin version from build file.

        Returns:
            Version string if found, None otherwise.
        """
        if self._version:
            return self._version

        if self._build_tool == "maven":
            self._version = self._get_maven_version()
        elif self._build_tool == "gradle":
            self._version = self._get_gradle_version()

        return self._version

    def _get_maven_version(self) -> str | None:
        """Extract OpenRewrite version from pom.xml."""
        pom = self.project_root / "pom.xml"
        if not pom.exists():
            return None

        try:
            content = pom.read_text(encoding="utf-8")
            # Simple extraction - look for rewrite-maven-plugin version
            import re

            match = re.search(
                r"<artifactId>rewrite-maven-plugin</artifactId>\s*"
                r"<version>([^<]+)</version>",
                content,
            )
            if match:
                return match.group(1)
        except OSError:
            pass
        return None

    def _get_gradle_version(self) -> str | None:
        """Extract OpenRewrite version from build.gradle."""
        for filename in ["build.gradle", "build.gradle.kts"]:
            gradle = self.project_root / filename
            if gradle.exists():
                try:
                    content = gradle.read_text(encoding="utf-8")
                    import re

                    # Look for org.openrewrite.rewrite plugin version
                    match = re.search(
                        r'id\s*[("\']+org\.openrewrite\.rewrite["\')]+\s*'
                        r'version\s*[("\']+([^"\']+)["\')]+',
                        content,
                    )
                    if match:
                        return match.group(1)
                except OSError:
                    pass
        return None

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring via OpenRewrite.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes and status.
        """
        if not self.is_available():
            return RefactorResult(
                success=False,
                changes=[],
                errors=["OpenRewrite is not available in this project"],
                tool_used="OpenRewrite",
                dry_run=dry_run,
            )

        recipe = self._get_recipe(request)
        if not recipe:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"No recipe found for operation: {request.operation}"],
                tool_used="OpenRewrite",
                dry_run=dry_run,
            )

        cmd = self._build_command(recipe, request, dry_run)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
        except subprocess.TimeoutExpired:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["OpenRewrite command timed out"],
                tool_used="OpenRewrite",
                dry_run=dry_run,
            )
        except FileNotFoundError as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Build tool not found: {e}"],
                tool_used="OpenRewrite",
                dry_run=dry_run,
            )

        if result.returncode != 0:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[result.stderr or result.stdout or "Unknown error"],
                tool_used="OpenRewrite",
                dry_run=dry_run,
            )

        changes = self._parse_changes(result.stdout, request)

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="OpenRewrite",
            dry_run=dry_run,
        )

    def _get_recipe(self, request: RefactorRequest) -> str | None:
        """Map operation to OpenRewrite recipe name.

        Args:
            request: The refactoring request.

        Returns:
            Recipe name or None if not supported.
        """
        return self.RECIPE_MAP.get(request.operation)

    def _build_command(
        self,
        recipe: str,
        request: RefactorRequest,
        dry_run: bool,
    ) -> list[str]:
        """Build the Maven or Gradle command for recipe execution.

        Args:
            recipe: OpenRewrite recipe name.
            request: The refactoring request.
            dry_run: Whether this is a dry run.

        Returns:
            Command as list of strings.
        """
        if self._build_tool == "maven":
            return self._build_maven_command(recipe, request, dry_run)
        elif self._build_tool == "gradle":
            return self._build_gradle_command(recipe, request, dry_run)
        else:
            return []

    def _build_maven_command(
        self,
        recipe: str,
        request: RefactorRequest,
        dry_run: bool,
    ) -> list[str]:
        """Build Maven command for OpenRewrite."""
        cmd = [
            "mvn",
            "-B",  # Batch mode
            "rewrite:run" if not dry_run else "rewrite:dryRun",
            f"-Drewrite.activeRecipes={recipe}",
        ]

        # Add recipe options based on operation
        if request.operation == RefactorOperation.RENAME and request.new_value:
            cmd.append(f"-Drewrite.options.oldFullyQualifiedTypeName={request.target}")
            cmd.append(f"-Drewrite.options.newFullyQualifiedTypeName={request.new_value}")
        elif request.operation == RefactorOperation.MOVE and request.new_value:
            cmd.append(f"-Drewrite.options.oldPackageName={request.target}")
            cmd.append(f"-Drewrite.options.newPackageName={request.new_value}")

        return cmd

    def _build_gradle_command(
        self,
        recipe: str,
        _request: RefactorRequest,
        dry_run: bool,
    ) -> list[str]:
        """Build Gradle command for OpenRewrite.

        Args:
            recipe: OpenRewrite recipe name.
            _request: The refactoring request (unused for Gradle currently).
            dry_run: Whether this is a dry run.

        Returns:
            Command as list of strings.
        """
        task = "rewriteRun" if not dry_run else "rewriteDryRun"
        cmd = [
            "./gradlew" if (self.project_root / "gradlew").exists() else "gradle",
            task,
            f"-Drewrite.activeRecipe={recipe}",
        ]

        return cmd

    def _parse_changes(
        self,
        output: str,
        request: RefactorRequest,
    ) -> list[RefactorChange]:
        """Parse OpenRewrite output to extract changes.

        Args:
            output: Command stdout.
            request: Original request for context.

        Returns:
            List of RefactorChange objects.
        """
        changes: list[RefactorChange] = []

        # OpenRewrite outputs changed files in various formats
        # This is a simplified parser - real implementation would need
        # to handle different output formats from Maven vs Gradle
        for line in output.split("\n"):
            if "modified" in line.lower() or "changed" in line.lower():
                # Extract file path from line
                parts = line.strip().split()
                for part in parts:
                    if part.endswith(".java") or part.endswith(".kt"):
                        changes.append(
                            RefactorChange(
                                file_path=part,
                                original_content="",  # Would need diff
                                new_content="",
                                description=f"Modified by {request.operation.value}",
                            )
                        )
                        break

        return changes

    def rollback(self, _result: RefactorResult) -> bool:
        """Rollback changes using git.

        Args:
            _result: Result from previous execute() call (unused, git restores all).

        Returns:
            True if rollback succeeded.
        """
        try:
            subprocess.run(
                ["git", "checkout", "."],
                cwd=self.project_root,
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
