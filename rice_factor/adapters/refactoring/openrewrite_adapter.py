"""OpenRewrite adapter for JVM refactoring.

OpenRewrite provides AST-based refactoring for Java, Kotlin, and Groovy
through Maven or Gradle plugins. This adapter wraps OpenRewrite to
provide language-native refactoring capabilities.

Enhanced in M14 to support:
- extract_interface: Extract interface from concrete class
- enforce_dependency: ArchUnit-style dependency enforcement
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 - Path used at runtime via self.project_root operations
from typing import TYPE_CHECKING, Any, ClassVar

from rice_factor.domain.ports.refactor import (
    RefactorChange,
    RefactorOperation,
    RefactorRequest,
    RefactorResult,
    RefactorToolPort,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class JvmDependencyRule:
    """Rule for JVM dependency enforcement.

    Attributes:
        source_package: Package that should not depend on target.
        target_package: Package that should not be imported by source.
        description: Human-readable description of the rule.
    """

    source_package: str
    target_package: str
    description: str = ""


@dataclass
class JvmDependencyViolation:
    """A dependency violation found during analysis.

    Attributes:
        file_path: Path to the file with the violation.
        line: Line number of the violation.
        import_statement: The import statement that violates the rule.
        source_class: Class doing the importing.
        target_class: Class/package being imported.
    """

    file_path: str
    line: int
    import_statement: str
    source_class: str
    target_class: str


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

    # ========================================================================
    # Enhanced M14 Methods: extract_interface and enforce_dependency
    # ========================================================================

    def extract_interface(
        self,
        file_path: Path,
        class_name: str,
        interface_name: str,
        methods: Sequence[str] | None = None,
        language: str = "java",
    ) -> RefactorResult:
        """Extract an interface from a concrete class.

        For Java: Creates a Java interface
        For Kotlin: Creates a Kotlin interface

        Args:
            file_path: Path to the file containing the class.
            class_name: Name of the concrete class.
            interface_name: Name for the generated interface.
            methods: Optional list of method names to include.
                     If None, includes all public methods.
            language: Target language ("java" or "kotlin").

        Returns:
            RefactorResult with the generated interface code.
        """
        try:
            # Resolve file path
            if not file_path.is_absolute():
                file_path = self.project_root / file_path

            if not file_path.exists():
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"File not found: {file_path}"],
                    tool_used="OpenRewrite",
                    dry_run=True,
                )

            content = file_path.read_text(encoding="utf-8")

            # Detect language from file extension if not specified
            if file_path.suffix == ".kt":
                language = "kotlin"
            elif file_path.suffix == ".java":
                language = "java"

            # Parse and extract methods
            if language == "kotlin":
                method_sigs = self._extract_kotlin_methods(content, class_name, methods)
                interface_code = self._generate_kotlin_interface(
                    interface_name, method_sigs, content
                )
            else:
                method_sigs = self._extract_java_methods(content, class_name, methods)
                interface_code = self._generate_java_interface(
                    interface_name, method_sigs, content
                )

            if not method_sigs:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"No public methods found in class '{class_name}'"],
                    tool_used="OpenRewrite",
                    dry_run=True,
                )

            # Create the change
            change = RefactorChange(
                file_path=str(file_path.relative_to(self.project_root)),
                original_content="",
                new_content=interface_code,
                description=f"Generated interface '{interface_name}' from class '{class_name}'",
            )

            return RefactorResult(
                success=True,
                changes=[change],
                errors=[],
                tool_used="OpenRewrite",
                dry_run=True,
                warnings=[
                    "Interface generated but not automatically inserted into file",
                    "Review and add to appropriate location",
                ],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Extract interface failed: {e}"],
                tool_used="OpenRewrite",
                dry_run=True,
            )

    def _extract_java_methods(
        self,
        content: str,
        class_name: str,
        filter_methods: Sequence[str] | None,
    ) -> list[dict[str, Any]]:
        """Extract method signatures from a Java class.

        Args:
            content: Java source code.
            class_name: Name of the class to extract from.
            filter_methods: Optional list of method names to include.

        Returns:
            List of method signature dictionaries.
        """
        signatures: list[dict[str, str]] = []

        # Find the class
        class_pattern = rf"class\s+{re.escape(class_name)}\s*(?:extends|implements|{{)"
        class_match = re.search(class_pattern, content)
        if not class_match:
            return signatures

        # Find methods (simplified regex - real implementation would use a parser)
        # Pattern: public [modifiers] ReturnType methodName(params) [throws...]
        method_pattern = (
            r"public\s+(?:(?:static|final|synchronized)\s+)*"
            r"(\w+(?:<[^>]+>)?)\s+"  # Return type
            r"(\w+)\s*"  # Method name
            r"\(([^)]*)\)"  # Parameters
        )

        for match in re.finditer(method_pattern, content[class_match.start() :]):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3).strip()

            # Skip constructors and private methods
            if method_name == class_name:
                continue

            # Filter if specified
            if filter_methods and method_name not in filter_methods:
                continue

            signatures.append(
                {
                    "name": method_name,
                    "return_type": return_type,
                    "params": params,
                }
            )

        return signatures

    def _extract_kotlin_methods(
        self,
        content: str,
        class_name: str,
        filter_methods: Sequence[str] | None,
    ) -> list[dict[str, Any]]:
        """Extract method signatures from a Kotlin class.

        Args:
            content: Kotlin source code.
            class_name: Name of the class to extract from.
            filter_methods: Optional list of method names to include.

        Returns:
            List of method signature dictionaries.
        """
        signatures: list[dict[str, Any]] = []

        # Find the class
        class_pattern = rf"class\s+{re.escape(class_name)}\s*(?:\(|:|\{{)"
        class_match = re.search(class_pattern, content)
        if not class_match:
            return signatures

        # Find methods (Kotlin syntax)
        # Pattern: [modifiers] fun methodName(params): ReturnType
        method_pattern = (
            r"(?:open\s+|public\s+)*fun\s+"
            r"(\w+)\s*"  # Method name
            r"\(([^)]*)\)"  # Parameters
            r"(?:\s*:\s*(\w+(?:<[^>]+>)?\??))?"  # Return type (optional, with nullable ?)
        )

        for match in re.finditer(method_pattern, content[class_match.start() :]):
            method_name = match.group(1)
            params = match.group(2).strip()
            return_type = match.group(3) or "Unit"

            # Filter if specified
            if filter_methods and method_name not in filter_methods:
                continue

            # Skip private methods
            if f"private fun {method_name}" in content:
                continue

            signatures.append(
                {
                    "name": method_name,
                    "return_type": return_type,
                    "params": params,
                    "is_suspend": "suspend fun " + method_name in content,
                }
            )

        return signatures

    def _generate_java_interface(
        self,
        interface_name: str,
        method_sigs: list[dict[str, Any]],
        original_content: str,
    ) -> str:
        """Generate a Java interface definition.

        Args:
            interface_name: Name for the interface.
            method_sigs: List of method signature dictionaries.
            original_content: Original source for package detection.

        Returns:
            Java code for the interface.
        """
        lines = []

        # Extract package from original file
        package_match = re.search(r"package\s+([\w.]+);", original_content)
        if package_match:
            lines.append(f"package {package_match.group(1)};")
            lines.append("")

        lines.append(f"public interface {interface_name} {{")
        lines.append("")

        for sig in method_sigs:
            params = sig["params"]
            lines.append(f"    {sig['return_type']} {sig['name']}({params});")
            lines.append("")

        lines.append("}")

        return "\n".join(lines)

    def _generate_kotlin_interface(
        self,
        interface_name: str,
        method_sigs: list[dict[str, Any]],
        original_content: str,
    ) -> str:
        """Generate a Kotlin interface definition.

        Args:
            interface_name: Name for the interface.
            method_sigs: List of method signature dictionaries.
            original_content: Original source for package detection.

        Returns:
            Kotlin code for the interface.
        """
        lines = []

        # Extract package from original file
        package_match = re.search(r"package\s+([\w.]+)", original_content)
        if package_match:
            lines.append(f"package {package_match.group(1)}")
            lines.append("")

        lines.append(f"interface {interface_name} {{")
        lines.append("")

        for sig in method_sigs:
            params = sig["params"]
            return_type = sig["return_type"]
            suspend = "suspend " if sig.get("is_suspend") else ""

            if return_type == "Unit":
                lines.append(f"    {suspend}fun {sig['name']}({params})")
            else:
                lines.append(f"    {suspend}fun {sig['name']}({params}): {return_type}")
            lines.append("")

        lines.append("}")

        return "\n".join(lines)

    def enforce_dependency(
        self,
        rule: JvmDependencyRule,
        fix: bool = False,
    ) -> RefactorResult:
        """Check and report dependency violations.

        Analyzes import statements to find violations of dependency rules.
        Uses ArchUnit-style checking for JVM projects.

        Args:
            rule: The dependency rule to enforce.
            fix: If True, attempt to remove violating imports.
                 Note: Actual removal may break compilation.

        Returns:
            RefactorResult with violations found.
        """
        try:
            violations = self._find_jvm_dependency_violations(rule)

            if not violations:
                return RefactorResult(
                    success=True,
                    changes=[],
                    errors=[],
                    tool_used="OpenRewrite",
                    dry_run=not fix,
                )

            changes: list[RefactorChange] = []
            errors: list[str] = []

            for violation in violations:
                if fix:
                    # Try to remove the violating import
                    result = self._remove_jvm_import(violation)
                    if result.success:
                        changes.extend(result.changes)
                    else:
                        errors.extend(result.errors)
                else:
                    # Just report the violation
                    changes.append(
                        RefactorChange(
                            file_path=violation.file_path,
                            original_content=violation.import_statement,
                            new_content="",
                            description=(
                                f"Dependency violation: {violation.source_class} "
                                f"imports {violation.target_class} at line {violation.line}"
                            ),
                        )
                    )

            return RefactorResult(
                success=len(errors) == 0,
                changes=changes,
                errors=errors,
                tool_used="OpenRewrite",
                dry_run=not fix,
                warnings=[f"Found {len(violations)} dependency violation(s)"],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Enforce dependency failed: {e}"],
                tool_used="OpenRewrite",
                dry_run=not fix,
            )

    def _find_jvm_dependency_violations(
        self,
        rule: JvmDependencyRule,
    ) -> list[JvmDependencyViolation]:
        """Find all violations of a dependency rule in JVM source files.

        Args:
            rule: The dependency rule to check.

        Returns:
            List of dependency violations.
        """
        violations: list[JvmDependencyViolation] = []

        # Convert package to path
        source_path = self.project_root / "src" / "main"

        # Search for Java and Kotlin files in source package
        source_package_path = rule.source_package.replace(".", "/")

        for src_dir in ["java", "kotlin"]:
            search_path = source_path / src_dir / source_package_path
            if not search_path.exists():
                continue

            # Find all source files
            for ext in ["*.java", "*.kt"]:
                for source_file in search_path.rglob(ext):
                    file_violations = self._check_file_for_violations(
                        source_file, rule
                    )
                    violations.extend(file_violations)

        return violations

    def _check_file_for_violations(
        self,
        file_path: Path,
        rule: JvmDependencyRule,
    ) -> list[JvmDependencyViolation]:
        """Check a single file for dependency violations.

        Args:
            file_path: Path to the source file.
            rule: The dependency rule to check.

        Returns:
            List of violations in this file.
        """
        violations: list[JvmDependencyViolation] = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Extract class name from file
            source_class = file_path.stem

            for i, line in enumerate(lines, 1):
                # Check for imports that violate the rule
                # Java: import com.example.forbidden.SomeClass;
                # Kotlin: import com.example.forbidden.SomeClass
                import_match = re.match(r"import\s+([\w.]+)(?:\s*;)?", line)
                if import_match:
                    imported = import_match.group(1)
                    if imported.startswith(rule.target_package):
                        violations.append(
                            JvmDependencyViolation(
                                file_path=str(
                                    file_path.relative_to(self.project_root)
                                ),
                                line=i,
                                import_statement=line.strip(),
                                source_class=source_class,
                                target_class=imported,
                            )
                        )

        except OSError:
            pass

        return violations

    def _remove_jvm_import(
        self, violation: JvmDependencyViolation
    ) -> RefactorResult:
        """Remove an import statement that violates dependency rules.

        Args:
            violation: The violation to fix.

        Returns:
            RefactorResult indicating success/failure.
        """
        try:
            file_path = self.project_root / violation.file_path
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            # Remove the import line
            if 0 < violation.line <= len(lines):
                removed_line = lines[violation.line - 1]
                lines[violation.line - 1] = ""

                new_content = "\n".join(lines)
                file_path.write_text(new_content, encoding="utf-8")

                return RefactorResult(
                    success=True,
                    changes=[
                        RefactorChange(
                            file_path=violation.file_path,
                            original_content=removed_line,
                            new_content="",
                            description=f"Removed import at line {violation.line}",
                            line_start=violation.line,
                            line_end=violation.line,
                        )
                    ],
                    errors=[],
                    tool_used="OpenRewrite",
                    dry_run=False,
                )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Failed to remove import: {e}"],
                tool_used="OpenRewrite",
                dry_run=False,
            )

        return RefactorResult(
            success=False,
            changes=[],
            errors=["Could not find line to remove"],
            tool_used="OpenRewrite",
            dry_run=False,
        )

    def extract_interface_via_recipe(
        self,
        class_fqn: str,
        interface_name: str,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Extract interface using OpenRewrite recipe (if available).

        This method uses OpenRewrite's built-in ExtractInterface recipe
        when available. Falls back to local extraction if not.

        Args:
            class_fqn: Fully qualified class name.
            interface_name: Name for the generated interface.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with the extraction outcome.
        """
        if not self.is_available():
            return RefactorResult(
                success=False,
                changes=[],
                errors=["OpenRewrite is not available in this project"],
                tool_used="OpenRewrite",
                dry_run=dry_run,
            )

        # Use the refactoring recipe
        recipe = "org.openrewrite.java.ExtractInterface"

        if self._build_tool == "maven":
            cmd = [
                "mvn",
                "-B",
                "rewrite:run" if not dry_run else "rewrite:dryRun",
                f"-Drewrite.activeRecipes={recipe}",
                f"-Drewrite.options.fullyQualifiedClassName={class_fqn}",
                f"-Drewrite.options.interfaceName={interface_name}",
            ]
        else:
            cmd = [
                "./gradlew" if (self.project_root / "gradlew").exists() else "gradle",
                "rewriteRun" if not dry_run else "rewriteDryRun",
                f"-Drewrite.activeRecipe={recipe}",
            ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
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
            # Fall back to local extraction
            return RefactorResult(
                success=False,
                changes=[],
                errors=[
                    f"Recipe execution failed: {result.stderr or result.stdout}",
                    "Consider using extract_interface() for local extraction",
                ],
                tool_used="OpenRewrite",
                dry_run=dry_run,
            )

        return RefactorResult(
            success=True,
            changes=[],
            errors=[],
            tool_used="OpenRewrite",
            dry_run=dry_run,
        )
