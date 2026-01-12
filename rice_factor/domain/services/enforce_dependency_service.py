"""Enforce dependency service for architectural violation detection and fixing.

This module provides the EnforceDependencyService that detects and fixes
architectural dependency violations across codebases.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ViolationType(Enum):
    """Type of dependency violation."""

    IMPORT_VIOLATION = "import_violation"  # Wrong layer importing
    CIRCULAR_DEPENDENCY = "circular_dependency"  # Circular imports
    EXTERNAL_IN_DOMAIN = "external_in_domain"  # External lib in domain
    FORBIDDEN_IMPORT = "forbidden_import"  # Explicitly banned import
    LAYER_SKIP = "layer_skip"  # Skipping architectural layers


class ViolationSeverity(Enum):
    """Severity level of violation."""

    ERROR = "error"  # Must fix
    WARNING = "warning"  # Should fix
    INFO = "info"  # Informational


class FixAction(Enum):
    """Type of fix action to apply."""

    REMOVE_IMPORT = "remove_import"
    REPLACE_IMPORT = "replace_import"
    MOVE_CODE = "move_code"
    ADD_ADAPTER = "add_adapter"
    INJECT_DEPENDENCY = "inject_dependency"


@dataclass
class DependencyRule:
    """A rule defining allowed dependencies.

    Attributes:
        name: Rule name.
        source_pattern: Pattern for source modules.
        allowed_targets: Allowed target patterns.
        forbidden_targets: Forbidden target patterns.
        severity: Violation severity.
    """

    name: str
    source_pattern: str
    allowed_targets: list[str] = field(default_factory=list)
    forbidden_targets: list[str] = field(default_factory=list)
    severity: ViolationSeverity = ViolationSeverity.ERROR

    def matches_source(self, module_path: str) -> bool:
        """Check if module matches source pattern."""
        return bool(re.match(self.source_pattern, module_path))

    def is_target_allowed(self, target: str) -> bool:
        """Check if target import is allowed."""
        # Check forbidden first
        for pattern in self.forbidden_targets:
            if re.match(pattern, target):
                return False

        # If allowed list is empty, everything not forbidden is allowed
        if not self.allowed_targets:
            return True

        # Check if target matches any allowed pattern
        for pattern in self.allowed_targets:
            if re.match(pattern, target):
                return True

        return False


@dataclass
class Violation:
    """A detected dependency violation.

    Attributes:
        type: Type of violation.
        severity: Severity level.
        file_path: Path to file with violation.
        line: Line number.
        source_module: Source module.
        target_module: Target module (if applicable).
        message: Human-readable message.
        rule_name: Name of violated rule.
        suggested_fix: Suggested fix action.
    """

    type: ViolationType
    severity: ViolationSeverity
    file_path: str
    line: int
    source_module: str
    target_module: str | None = None
    message: str = ""
    rule_name: str | None = None
    suggested_fix: FixAction | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line": self.line,
            "source_module": self.source_module,
            "target_module": self.target_module,
            "message": self.message,
            "rule_name": self.rule_name,
            "suggested_fix": self.suggested_fix.value if self.suggested_fix else None,
        }


@dataclass
class FixResult:
    """Result of applying a fix.

    Attributes:
        success: Whether fix was applied.
        file_path: Path to modified file.
        original_content: Original file content.
        new_content: New file content.
        violation: The fixed violation.
        error: Error message if failed.
    """

    success: bool
    file_path: str
    original_content: str | None = None
    new_content: str | None = None
    violation: Violation | None = None
    error: str | None = None


@dataclass
class AnalysisResult:
    """Result of dependency analysis.

    Attributes:
        violations: List of detected violations.
        files_analyzed: Number of files analyzed.
        rules_checked: Number of rules checked.
        analyzed_at: When analysis was performed.
    """

    violations: list[Violation] = field(default_factory=list)
    files_analyzed: int = 0
    rules_checked: int = 0
    analyzed_at: datetime | None = None

    @property
    def error_count(self) -> int:
        """Count of error-severity violations."""
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-severity violations."""
        return sum(
            1 for v in self.violations if v.severity == ViolationSeverity.WARNING
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violations": [v.to_dict() for v in self.violations],
            "files_analyzed": self.files_analyzed,
            "rules_checked": self.rules_checked,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }


@dataclass
class EnforceDependencyService:
    """Service for detecting and fixing architectural dependency violations.

    Supports hexagonal architecture rules and custom dependency policies.

    Attributes:
        repo_root: Root directory of the repository.
        rules: List of dependency rules to enforce.
    """

    repo_root: Path
    rules: list[DependencyRule] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize with default rules if none provided."""
        if not self.rules:
            self.rules = self._get_default_rules()

    def _get_default_rules(self) -> list[DependencyRule]:
        """Get default hexagonal architecture rules."""
        return [
            # Domain layer should not import from adapters or entrypoints
            DependencyRule(
                name="domain_isolation",
                source_pattern=r".*/domain/.*",
                forbidden_targets=[
                    r".*adapters.*",
                    r".*entrypoints.*",
                    # External libraries forbidden in domain
                    r"anthropic.*",
                    r"openai.*",
                    r"typer.*",
                    r"rich.*",
                    r"httpx.*",
                    r"aiohttp.*",
                ],
                severity=ViolationSeverity.ERROR,
            ),
            # Adapters should not import from entrypoints
            DependencyRule(
                name="adapter_isolation",
                source_pattern=r".*/adapters/.*",
                forbidden_targets=[
                    r".*entrypoints.*",
                ],
                severity=ViolationSeverity.ERROR,
            ),
            # Entrypoints can import from anywhere (most permissive layer)
            DependencyRule(
                name="entrypoint_permissive",
                source_pattern=r".*/entrypoints/.*",
                allowed_targets=[r".*"],  # Allow all
                severity=ViolationSeverity.INFO,
            ),
        ]

    def add_rule(self, rule: DependencyRule) -> None:
        """Add a custom dependency rule.

        Args:
            rule: Rule to add.
        """
        self.rules.append(rule)

    def clear_rules(self) -> None:
        """Clear all rules."""
        self.rules.clear()

    def analyze_file(self, file_path: Path) -> list[Violation]:
        """Analyze a single file for violations.

        Args:
            file_path: Path to file.

        Returns:
            List of violations found.
        """
        violations: list[Violation] = []

        if not file_path.exists() or file_path.suffix != ".py":
            return violations

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except (SyntaxError, OSError):
            return violations

        # Get relative path for pattern matching
        try:
            rel_path = str(file_path.relative_to(self.repo_root))
        except ValueError:
            rel_path = str(file_path)

        # Normalize path separators
        rel_path = rel_path.replace("\\", "/")

        # Find all imports
        imports = self._extract_imports(tree)

        # Check each import against rules
        for import_info in imports:
            target = import_info["module"]
            line = import_info["line"]

            for rule in self.rules:
                if rule.matches_source(rel_path):
                    if not rule.is_target_allowed(target):
                        violations.append(
                            Violation(
                                type=ViolationType.IMPORT_VIOLATION,
                                severity=rule.severity,
                                file_path=str(file_path),
                                line=line,
                                source_module=rel_path,
                                target_module=target,
                                message=f"Import '{target}' violates rule '{rule.name}'",
                                rule_name=rule.name,
                                suggested_fix=FixAction.REMOVE_IMPORT,
                            )
                        )

        return violations

    def _extract_imports(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract import statements from AST.

        Args:
            tree: AST tree.

        Returns:
            List of import info dicts.
        """
        imports: list[dict[str, Any]] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "module": alias.name,
                            "line": node.lineno,
                            "type": "import",
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(
                        {
                            "module": node.module,
                            "line": node.lineno,
                            "type": "from",
                        }
                    )

        return imports

    def analyze_directory(
        self,
        directory: Path | None = None,
        recursive: bool = True,
    ) -> AnalysisResult:
        """Analyze a directory for violations.

        Args:
            directory: Directory to analyze (defaults to repo_root).
            recursive: Whether to analyze recursively.

        Returns:
            AnalysisResult with all violations.
        """
        if directory is None:
            directory = self.repo_root

        violations: list[Violation] = []
        files_analyzed = 0

        if recursive:
            py_files = list(directory.rglob("*.py"))
        else:
            py_files = list(directory.glob("*.py"))

        for file_path in py_files:
            file_violations = self.analyze_file(file_path)
            violations.extend(file_violations)
            files_analyzed += 1

        return AnalysisResult(
            violations=violations,
            files_analyzed=files_analyzed,
            rules_checked=len(self.rules),
            analyzed_at=datetime.now(UTC),
        )

    def detect_circular_dependencies(
        self,
        directory: Path | None = None,
    ) -> list[Violation]:
        """Detect circular dependencies in imports.

        Args:
            directory: Directory to analyze.

        Returns:
            List of circular dependency violations.
        """
        if directory is None:
            directory = self.repo_root

        violations: list[Violation] = []
        # Build dependency graph
        graph: dict[str, set[str]] = {}

        for file_path in directory.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
            except (SyntaxError, OSError):
                continue

            try:
                module_name = str(file_path.relative_to(self.repo_root))
            except ValueError:
                module_name = str(file_path)

            module_name = module_name.replace("\\", "/").replace("/", ".").rstrip(".py")

            imports = self._extract_imports(tree)
            graph[module_name] = {imp["module"] for imp in imports}

        # Find cycles using DFS
        cycles = self._find_cycles(graph)

        for cycle in cycles:
            violations.append(
                Violation(
                    type=ViolationType.CIRCULAR_DEPENDENCY,
                    severity=ViolationSeverity.WARNING,
                    file_path=str(directory),
                    line=0,
                    source_module=cycle[0],
                    target_module=cycle[-1],
                    message=f"Circular dependency: {' -> '.join(cycle)}",
                    suggested_fix=FixAction.MOVE_CODE,
                )
            )

        return violations

    def _find_cycles(self, graph: dict[str, set[str]]) -> list[list[str]]:
        """Find cycles in dependency graph.

        Args:
            graph: Dependency graph.

        Returns:
            List of cycles (each is a list of module names).
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor in graph:  # Only check internal modules
                    if neighbor not in visited:
                        dfs(neighbor)
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        cycles.append(path[cycle_start:] + [neighbor])

            path.pop()
            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def fix_violation(self, violation: Violation) -> FixResult:
        """Attempt to fix a violation.

        Args:
            violation: Violation to fix.

        Returns:
            FixResult with fix details.
        """
        file_path = Path(violation.file_path)

        if not file_path.exists():
            return FixResult(
                success=False,
                file_path=str(file_path),
                error=f"File not found: {file_path}",
            )

        if violation.suggested_fix == FixAction.REMOVE_IMPORT:
            return self._fix_remove_import(file_path, violation)

        return FixResult(
            success=False,
            file_path=str(file_path),
            violation=violation,
            error=f"Auto-fix not supported for {violation.suggested_fix}",
        )

    def _fix_remove_import(
        self,
        file_path: Path,
        violation: Violation,
    ) -> FixResult:
        """Remove an import statement.

        Args:
            file_path: Path to file.
            violation: Violation to fix.

        Returns:
            FixResult.
        """
        original_content = file_path.read_text(encoding="utf-8")
        lines = original_content.split("\n")

        if violation.line > len(lines):
            return FixResult(
                success=False,
                file_path=str(file_path),
                original_content=original_content,
                violation=violation,
                error=f"Line {violation.line} out of range",
            )

        # Remove the import line
        line_idx = violation.line - 1
        removed_line = lines[line_idx]

        # Verify this line contains the import
        if (
            violation.target_module
            and violation.target_module not in removed_line
        ):
            return FixResult(
                success=False,
                file_path=str(file_path),
                original_content=original_content,
                violation=violation,
                error=f"Import '{violation.target_module}' not found on line {violation.line}",
            )

        # Remove the line
        new_lines = lines[:line_idx] + lines[line_idx + 1:]
        new_content = "\n".join(new_lines)

        return FixResult(
            success=True,
            file_path=str(file_path),
            original_content=original_content,
            new_content=new_content,
            violation=violation,
        )

    def fix_all_violations(
        self,
        result: AnalysisResult,
        dry_run: bool = True,
    ) -> list[FixResult]:
        """Attempt to fix all violations.

        Args:
            result: Analysis result with violations.
            dry_run: If True, don't actually modify files.

        Returns:
            List of FixResults.
        """
        fix_results: list[FixResult] = []

        for violation in result.violations:
            fix_result = self.fix_violation(violation)
            fix_results.append(fix_result)

            if fix_result.success and not dry_run and fix_result.new_content:
                Path(fix_result.file_path).write_text(
                    fix_result.new_content,
                    encoding="utf-8",
                )

        return fix_results

    def check_external_in_domain(
        self,
        domain_dir: Path | None = None,
    ) -> list[Violation]:
        """Check for external library imports in domain layer.

        Args:
            domain_dir: Path to domain directory.

        Returns:
            List of violations.
        """
        if domain_dir is None:
            domain_dir = self.repo_root / "rice_factor" / "domain"

        # Common external libraries that shouldn't be in domain
        external_libs = {
            "anthropic",
            "openai",
            "typer",
            "rich",
            "httpx",
            "aiohttp",
            "requests",
            "flask",
            "fastapi",
            "django",
            "sqlalchemy",
            "redis",
        }

        violations: list[Violation] = []

        for file_path in domain_dir.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)
            except (SyntaxError, OSError):
                continue

            imports = self._extract_imports(tree)

            for imp in imports:
                module = imp["module"].split(".")[0]  # Get top-level module
                if module in external_libs:
                    violations.append(
                        Violation(
                            type=ViolationType.EXTERNAL_IN_DOMAIN,
                            severity=ViolationSeverity.ERROR,
                            file_path=str(file_path),
                            line=imp["line"],
                            source_module=str(file_path),
                            target_module=imp["module"],
                            message=f"External library '{module}' imported in domain layer",
                            rule_name="no_external_in_domain",
                            suggested_fix=FixAction.ADD_ADAPTER,
                        )
                    )

        return violations
