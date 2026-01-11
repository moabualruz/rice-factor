"""Ruby Parser adapter for Ruby refactoring.

Ruby Parser is a Ruby gem that provides AST manipulation for Ruby code.
This adapter uses Ruby CLI commands and the parser gem for AST-based
refactoring operations.

Documentation:
- Ruby Parser: https://github.com/whitequark/parser
- RBS (Ruby Signature): https://github.com/ruby/rbs
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 - Path used at runtime
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
class RubyDependencyRule:
    """Rule for Ruby dependency enforcement.

    Attributes:
        source_module: Module/namespace that should not depend on target.
        target_module: Module/namespace that should not be required by source.
        description: Human-readable description of the rule.
    """

    source_module: str
    target_module: str
    description: str = ""


@dataclass
class RubyDependencyViolation:
    """A dependency violation found during analysis.

    Attributes:
        file_path: Path to the file with the violation.
        line: Line number of the violation.
        require_statement: The require statement that violates the rule.
        source_class: Class/module doing the requiring.
        target_module: Module being required.
    """

    file_path: str
    line: int
    require_statement: str
    source_class: str
    target_module: str


class RubyParserAdapter(RefactorToolPort):
    """Adapter for Ruby Parser (Ruby refactoring).

    This adapter uses the Ruby CLI with the parser gem to perform
    AST-based refactoring for Ruby projects.

    Attributes:
        project_root: Root directory of the project.
    """

    LANGUAGES: ClassVar[list[str]] = ["ruby", "rb"]

    OPERATIONS: ClassVar[list[RefactorOperation]] = [
        RefactorOperation.RENAME,
        RefactorOperation.MOVE,
        RefactorOperation.EXTRACT_INTERFACE,
    ]

    def __init__(self, project_root: Path) -> None:
        """Initialize the adapter.

        Args:
            project_root: Root directory of the Ruby project.
        """
        self.project_root = project_root
        self._ruby_version: str | None = None
        self._has_parser: bool | None = None

    def get_supported_languages(self) -> list[str]:
        """Return supported languages."""
        return self.LANGUAGES

    def get_supported_operations(self) -> list[RefactorOperation]:
        """Return supported refactoring operations."""
        return self.OPERATIONS

    def is_available(self) -> bool:
        """Check if Ruby and parser gem are available.

        Returns:
            True if Ruby is installed and a Ruby project exists.
        """
        # Check for Ruby CLI
        if not self._check_ruby():
            return False

        # Check for Ruby project files
        gemfile = self.project_root / "Gemfile"
        rakefile = self.project_root / "Rakefile"
        rb_files = list(self.project_root.glob("**/*.rb"))

        return gemfile.exists() or rakefile.exists() or bool(rb_files)

    def _check_ruby(self) -> bool:
        """Check if Ruby is installed.

        Returns:
            True if Ruby is available.
        """
        try:
            result = subprocess.run(
                ["ruby", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                self._ruby_version = result.stdout.strip()
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False

    def _check_parser_gem(self) -> bool:
        """Check if the parser gem is installed.

        Returns:
            True if parser gem is available.
        """
        if self._has_parser is not None:
            return self._has_parser

        try:
            result = subprocess.run(
                ["gem", "list", "-i", "parser"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self._has_parser = (
                result.returncode == 0 and result.stdout.strip().lower() == "true"
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._has_parser = False

        return self._has_parser

    def get_version(self) -> str | None:
        """Get Ruby version.

        Returns:
            Version string if available.
        """
        if self._ruby_version is None:
            self._check_ruby()
        return self._ruby_version

    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult:
        """Execute refactoring operation.

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
                errors=["Ruby is not available"],
                tool_used="RubyParser",
                dry_run=dry_run,
            )

        if request.operation == RefactorOperation.RENAME:
            return self._execute_rename(request, dry_run)
        elif request.operation == RefactorOperation.MOVE:
            return self._execute_move(request, dry_run)
        elif request.operation == RefactorOperation.EXTRACT_INTERFACE:
            return self._execute_extract_interface(request, dry_run)

        return RefactorResult(
            success=False,
            changes=[],
            errors=[f"Unsupported operation: {request.operation}"],
            tool_used="RubyParser",
            dry_run=dry_run,
        )

    def _execute_rename(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Execute rename operation using text-based refactoring.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        if not request.new_value:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["new_value required for rename operation"],
                tool_used="RubyParser",
                dry_run=dry_run,
            )

        return self._rename_manual(request, dry_run)

    def _rename_manual(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Manual text-based rename.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        changes: list[RefactorChange] = []
        old_name = request.target
        new_name = request.new_value or ""

        # Find all Ruby files
        rb_files = list(self.project_root.rglob("*.rb"))

        for rb_file in rb_files:
            try:
                content = rb_file.read_text(encoding="utf-8")
                if old_name in content:
                    new_content = content.replace(old_name, new_name)

                    if not dry_run:
                        rb_file.write_text(new_content, encoding="utf-8")

                    changes.append(
                        RefactorChange(
                            file_path=str(rb_file.relative_to(self.project_root)),
                            original_content=content,
                            new_content=new_content,
                            description=f"Renamed '{old_name}' to '{new_name}'",
                        )
                    )
            except OSError:
                continue

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="RubyParser",
            dry_run=dry_run,
            warnings=["Used text-based rename"],
        )

    def _execute_move(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Execute move/module change operation.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with changes.
        """
        if not request.new_value:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["new_value (target module) required for move"],
                tool_used="RubyParser",
                dry_run=dry_run,
            )

        old_module = request.target
        new_module = request.new_value

        changes: list[RefactorChange] = []
        rb_files = list(self.project_root.rglob("*.rb"))

        for rb_file in rb_files:
            try:
                content = rb_file.read_text(encoding="utf-8")

                # Change module declaration
                new_content = re.sub(
                    rf"module\s+{re.escape(old_module)}(\s*$|\s+)",
                    rf"module {new_module}\1",
                    content,
                    flags=re.MULTILINE,
                )

                # Change class definitions within module
                new_content = re.sub(
                    rf"class\s+{re.escape(old_module)}::",
                    rf"class {new_module}::",
                    new_content,
                )

                # Change require statements
                # Ruby: require 'old_module/submodule'
                old_require = old_module.lower().replace("::", "/")
                new_require = new_module.lower().replace("::", "/")
                new_content = re.sub(
                    rf"require\s+['\"]({re.escape(old_require)})",
                    f"require '{new_require}",
                    new_content,
                )
                # Capture old/new in closure to avoid B023
                old_req, new_req = old_require, new_require
                new_content = re.sub(
                    rf"require_relative\s+['\"].*{re.escape(old_require)}",
                    lambda m, old=old_req, new=new_req: m.group(0).replace(old, new),
                    new_content,
                )

                # Change qualified references (OldModule::ClassName)
                new_content = re.sub(
                    rf"\b{re.escape(old_module)}::",
                    rf"{new_module}::",
                    new_content,
                )

                if new_content != content:
                    if not dry_run:
                        rb_file.write_text(new_content, encoding="utf-8")

                    changes.append(
                        RefactorChange(
                            file_path=str(rb_file.relative_to(self.project_root)),
                            original_content=content,
                            new_content=new_content,
                            description=f"Changed module from '{old_module}' to '{new_module}'",
                        )
                    )
            except OSError:
                continue

        return RefactorResult(
            success=True,
            changes=changes,
            errors=[],
            tool_used="RubyParser",
            dry_run=dry_run,
        )

    def _execute_extract_interface(
        self, request: RefactorRequest, dry_run: bool
    ) -> RefactorResult:
        """Execute extract interface (module) operation.

        Args:
            request: The refactoring request.
            dry_run: If True, only preview changes.

        Returns:
            RefactorResult with generated module.
        """
        if not request.file_path:
            return RefactorResult(
                success=False,
                changes=[],
                errors=["file_path required for extract_interface"],
                tool_used="RubyParser",
                dry_run=dry_run,
            )

        file_path = self.project_root / request.file_path
        if not file_path.exists():
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"File not found: {file_path}"],
                tool_used="RubyParser",
                dry_run=dry_run,
            )

        return self.extract_interface(
            file_path=file_path,
            class_name=request.target,
            interface_name=request.new_value or f"{request.target}Interface",
        )

    def rollback(self, _result: RefactorResult) -> bool:
        """Rollback changes using git.

        Args:
            _result: Result from previous execute() call.

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
    # M14 Enhanced Methods: extract_interface and enforce_dependency
    # ========================================================================

    def extract_interface(
        self,
        file_path: Path,
        class_name: str,
        interface_name: str,
        methods: Sequence[str] | None = None,
    ) -> RefactorResult:
        """Extract a module (interface) from a Ruby class.

        In Ruby, interfaces are typically represented as modules with
        method signatures. This can generate either:
        1. A Ruby module with NotImplementedError stubs
        2. An RBS (Ruby Signature) type file

        Args:
            file_path: Path to the file containing the class.
            class_name: Name of the concrete class.
            interface_name: Name for the generated module.
            methods: Optional list of method names to include.

        Returns:
            RefactorResult with the generated module code.
        """
        try:
            if not file_path.is_absolute():
                file_path = self.project_root / file_path

            if not file_path.exists():
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"File not found: {file_path}"],
                    tool_used="RubyParser",
                    dry_run=True,
                )

            content = file_path.read_text(encoding="utf-8")

            method_sigs = self._extract_ruby_methods(content, class_name, methods)

            if not method_sigs:
                return RefactorResult(
                    success=False,
                    changes=[],
                    errors=[f"No public methods found in class '{class_name}'"],
                    tool_used="RubyParser",
                    dry_run=True,
                )

            # Generate both Ruby module and RBS
            module_code = self._generate_ruby_module(interface_name, method_sigs)
            rbs_code = self._generate_rbs_interface(interface_name, method_sigs)

            changes = [
                RefactorChange(
                    file_path=str(file_path.relative_to(self.project_root)),
                    original_content="",
                    new_content=module_code,
                    description=f"Generated module '{interface_name}' from class '{class_name}'",
                ),
                RefactorChange(
                    file_path=f"sig/{interface_name.lower()}.rbs",
                    original_content="",
                    new_content=rbs_code,
                    description=f"Generated RBS interface '{interface_name}'",
                ),
            ]

            return RefactorResult(
                success=True,
                changes=changes,
                errors=[],
                tool_used="RubyParser",
                dry_run=True,
                warnings=[
                    "Module and RBS generated but not automatically inserted",
                    "Review and add to appropriate location",
                ],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Extract interface failed: {e}"],
                tool_used="RubyParser",
                dry_run=True,
            )

    def _extract_ruby_methods(
        self,
        content: str,
        class_name: str,
        filter_methods: Sequence[str] | None,
    ) -> list[dict[str, Any]]:
        """Extract method signatures from a Ruby class.

        Args:
            content: Ruby source code.
            class_name: Name of the class to extract from.
            filter_methods: Optional list of method names to include.

        Returns:
            List of method signature dictionaries.
        """
        signatures: list[dict[str, Any]] = []

        # Find the class
        class_pattern = rf"class\s+{re.escape(class_name)}(?:\s*<\s*[\w:]+)?\s*$"
        class_match = re.search(class_pattern, content, re.MULTILINE)
        if not class_match:
            return signatures

        # Extract class body
        class_start = class_match.end()

        # Find the end of class (matching 'end' keyword)
        # This is simplified and may not handle all edge cases
        depth = 1
        class_end = class_start
        lines = content[class_start:].split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Count depth changes
            if re.match(r"(class|module|def|if|unless|case|while|until|for|begin|do)\b", stripped):
                depth += 1
            if stripped == "end" or re.match(r"end\b", stripped):
                depth -= 1
            if depth == 0:
                class_end = class_start + sum(len(ln) + 1 for ln in lines[:i])
                break

        class_body = content[class_start:class_end]

        # Find public methods (default visibility is public in Ruby)
        # Pattern: def method_name(params) or def method_name
        method_pattern = r"def\s+(\w+[?!=]?)(?:\s*\(([^)]*)\))?"

        in_private = False
        in_protected = False

        for line in class_body.split("\n"):
            stripped = line.strip()

            # Track visibility
            if stripped == "private" or stripped.startswith("private "):
                in_private = True
                in_protected = False
            elif stripped == "protected" or stripped.startswith("protected "):
                in_protected = True
                in_private = False
            elif stripped == "public" or stripped.startswith("public "):
                in_private = False
                in_protected = False

            # Skip non-public methods
            if in_private or in_protected:
                continue

            match = re.match(method_pattern, stripped)
            if match:
                method_name = match.group(1)
                params = match.group(2) or ""

                # Skip initialize (constructor)
                if method_name == "initialize":
                    continue

                # Filter if specified
                if filter_methods and method_name not in filter_methods:
                    continue

                signatures.append(
                    {
                        "name": method_name,
                        "params": params,
                    }
                )

        return signatures

    def _generate_ruby_module(
        self,
        interface_name: str,
        method_sigs: list[dict[str, Any]],
    ) -> str:
        """Generate a Ruby module definition.

        Args:
            interface_name: Name for the module.
            method_sigs: List of method signature dictionaries.

        Returns:
            Ruby code for the module.
        """
        lines = [
            "# frozen_string_literal: true",
            "",
            f"# Interface module for {interface_name}",
            f"module {interface_name}",
        ]

        for sig in method_sigs:
            params = sig["params"]
            if params:
                lines.append(f"  def {sig['name']}({params})")
            else:
                lines.append(f"  def {sig['name']}")
            lines.append("    raise NotImplementedError")
            lines.append("  end")
            lines.append("")

        lines.append("end")

        return "\n".join(lines)

    def _generate_rbs_interface(
        self,
        interface_name: str,
        method_sigs: list[dict[str, Any]],
    ) -> str:
        """Generate an RBS (Ruby Signature) interface definition.

        Args:
            interface_name: Name for the interface.
            method_sigs: List of method signature dictionaries.

        Returns:
            RBS code for the interface.
        """
        lines = [
            f"# Interface type for {interface_name}",
            f"interface _{interface_name}",
        ]

        for sig in method_sigs:
            # Convert Ruby params to RBS syntax (simplified)
            params = self._convert_params_to_rbs(sig["params"])
            lines.append(f"  def {sig['name']}: {params} -> untyped")

        lines.append("end")

        return "\n".join(lines)

    def _convert_params_to_rbs(self, ruby_params: str) -> str:
        """Convert Ruby parameters to RBS syntax.

        Args:
            ruby_params: Ruby parameter string.

        Returns:
            RBS parameter syntax.
        """
        if not ruby_params:
            return "()"

        # Split parameters
        params = [p.strip() for p in ruby_params.split(",")]
        rbs_params = []

        for param in params:
            # Handle default values
            if "=" in param:
                name = param.split("=")[0].strip()
                rbs_params.append(f"?untyped {name}")
            # Handle double splat (keyword args) - check before single splat
            elif param.startswith("**"):
                name = param[2:]
                rbs_params.append(f"**untyped {name}")
            # Handle splat
            elif param.startswith("*"):
                name = param[1:]
                rbs_params.append(f"*untyped {name}")
            # Handle block
            elif param.startswith("&"):
                # Blocks are handled separately in RBS
                continue
            else:
                rbs_params.append(f"untyped {param}")

        return f"({', '.join(rbs_params)})"

    def enforce_dependency(
        self,
        rule: RubyDependencyRule,
        fix: bool = False,
    ) -> RefactorResult:
        """Check and report dependency violations in Ruby code.

        Analyzes require statements to find violations of dependency rules.

        Args:
            rule: The dependency rule to enforce.
            fix: If True, attempt to remove violating requires.

        Returns:
            RefactorResult with violations found.
        """
        try:
            violations = self._find_ruby_dependency_violations(rule)

            if not violations:
                return RefactorResult(
                    success=True,
                    changes=[],
                    errors=[],
                    tool_used="RubyParser",
                    dry_run=not fix,
                )

            changes: list[RefactorChange] = []
            errors: list[str] = []

            for violation in violations:
                if fix:
                    result = self._remove_ruby_require(violation)
                    if result.success:
                        changes.extend(result.changes)
                    else:
                        errors.extend(result.errors)
                else:
                    changes.append(
                        RefactorChange(
                            file_path=violation.file_path,
                            original_content=violation.require_statement,
                            new_content="",
                            description=(
                                f"Dependency violation: {violation.source_class} "
                                f"requires {violation.target_module} at line {violation.line}"
                            ),
                        )
                    )

            return RefactorResult(
                success=len(errors) == 0,
                changes=changes,
                errors=errors,
                tool_used="RubyParser",
                dry_run=not fix,
                warnings=[f"Found {len(violations)} dependency violation(s)"],
            )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Enforce dependency failed: {e}"],
                tool_used="RubyParser",
                dry_run=not fix,
            )

    def _find_ruby_dependency_violations(
        self,
        rule: RubyDependencyRule,
    ) -> list[RubyDependencyViolation]:
        """Find all violations of a dependency rule in Ruby source files.

        Args:
            rule: The dependency rule to check.

        Returns:
            List of dependency violations.
        """
        violations: list[RubyDependencyViolation] = []

        # Convert module to path format for matching
        source_path = rule.source_module.lower().replace("::", "/")
        target_path = rule.target_module.lower().replace("::", "/")

        # Find all Ruby files
        rb_files = list(self.project_root.rglob("*.rb"))

        for rb_file in rb_files:
            try:
                content = rb_file.read_text(encoding="utf-8")
                rel_path = str(rb_file.relative_to(self.project_root))

                # Check if file is in source module (by path or module declaration)
                in_source = (
                    source_path in rel_path.lower()
                    or f"module {rule.source_module}" in content
                    or f"class {rule.source_module}" in content
                )

                if not in_source:
                    continue

                file_violations = self._check_ruby_file_violations(
                    rb_file, content, rule, target_path
                )
                violations.extend(file_violations)

            except OSError:
                continue

        return violations

    def _check_ruby_file_violations(
        self,
        file_path: Path,
        content: str,
        rule: RubyDependencyRule,
        target_path: str,
    ) -> list[RubyDependencyViolation]:
        """Check a single Ruby file for dependency violations.

        Args:
            file_path: Path to the source file.
            content: File content.
            rule: The dependency rule to check.
            target_path: Path format of target module.

        Returns:
            List of violations in this file.
        """
        violations: list[RubyDependencyViolation] = []
        lines = content.split("\n")

        source_class = file_path.stem.title().replace("_", "")

        for i, line in enumerate(lines, 1):
            # Check for require statements
            # Ruby: require 'forbidden/module'
            # Ruby: require_relative '../forbidden/module'
            require_match = re.match(r"require(?:_relative)?\s+['\"]([^'\"]+)['\"]", line)
            if require_match:
                required_path = require_match.group(1)
                # Check if this requires the forbidden module
                if (
                    target_path in required_path
                    or rule.target_module.lower() in required_path
                ):
                    violations.append(
                        RubyDependencyViolation(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line=i,
                            require_statement=line.strip(),
                            source_class=source_class,
                            target_module=required_path,
                        )
                    )

            # Also check for direct module references
            # Ruby: Forbidden::Module::Class.new
            ref_pattern = rf"\b{re.escape(rule.target_module)}::"
            if re.search(ref_pattern, line):
                violations.append(
                    RubyDependencyViolation(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line=i,
                        require_statement=line.strip(),
                        source_class=source_class,
                        target_module=rule.target_module,
                    )
                )

        return violations

    def _remove_ruby_require(
        self, violation: RubyDependencyViolation
    ) -> RefactorResult:
        """Remove a require statement that violates dependency rules.

        Args:
            violation: The violation to fix.

        Returns:
            RefactorResult indicating success/failure.
        """
        try:
            file_path = self.project_root / violation.file_path
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            if 0 < violation.line <= len(lines):
                removed_line = lines[violation.line - 1]

                # Only remove require statements, not module references
                if "require" in removed_line:
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
                                description=f"Removed require at line {violation.line}",
                                line_start=violation.line,
                                line_end=violation.line,
                            )
                        ],
                        errors=[],
                        tool_used="RubyParser",
                        dry_run=False,
                    )
                else:
                    return RefactorResult(
                        success=False,
                        changes=[],
                        errors=[
                            f"Cannot auto-fix module reference at line {violation.line}"
                        ],
                        tool_used="RubyParser",
                        dry_run=False,
                    )

        except Exception as e:
            return RefactorResult(
                success=False,
                changes=[],
                errors=[f"Failed to remove require: {e}"],
                tool_used="RubyParser",
                dry_run=False,
            )

        return RefactorResult(
            success=False,
            changes=[],
            errors=["Could not find line to remove"],
            tool_used="RubyParser",
            dry_run=False,
        )
