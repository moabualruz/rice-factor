"""Safety analyzer for refactoring operations.

This module provides the SafetyAnalyzer that performs pre-execution impact
analysis and risk assessment for refactoring operations.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class RiskLevel(Enum):
    """Risk level of a refactoring operation."""

    LOW = "low"  # Safe to proceed
    MEDIUM = "medium"  # Proceed with caution
    HIGH = "high"  # Review carefully
    CRITICAL = "critical"  # Manual review required


class ImpactType(Enum):
    """Type of impact from a refactoring."""

    BREAKING_CHANGE = "breaking_change"  # API breakage
    BEHAVIORAL_CHANGE = "behavioral_change"  # Logic change
    STRUCTURAL_CHANGE = "structural_change"  # Code structure
    DEPENDENCY_CHANGE = "dependency_change"  # Import/dependency
    TEST_IMPACT = "test_impact"  # Affects tests
    CONFIG_IMPACT = "config_impact"  # Affects configuration


class WarningType(Enum):
    """Type of warning from analysis."""

    UNUSED_IMPORT = "unused_import"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    PUBLIC_API_CHANGE = "public_api_change"
    TEST_COVERAGE_GAP = "test_coverage_gap"
    COMPLEX_CHANGE = "complex_change"
    MISSING_DOCSTRING = "missing_docstring"
    TYPE_MISMATCH = "type_mismatch"


@dataclass
class FileImpact:
    """Impact on a single file.

    Attributes:
        file_path: Path to affected file.
        impact_type: Type of impact.
        changes_count: Number of changes in file.
        lines_affected: Line numbers affected.
        description: Human-readable description.
    """

    file_path: str
    impact_type: ImpactType
    changes_count: int = 0
    lines_affected: list[int] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "impact_type": self.impact_type.value,
            "changes_count": self.changes_count,
            "lines_affected": self.lines_affected,
            "description": self.description,
        }


@dataclass
class Warning:
    """A warning from safety analysis.

    Attributes:
        type: Warning type.
        message: Warning message.
        file_path: Associated file path.
        line: Line number if applicable.
        suggestion: Suggested fix.
    """

    type: WarningType
    message: str
    file_path: str | None = None
    line: int | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "message": self.message,
            "file_path": self.file_path,
            "line": self.line,
            "suggestion": self.suggestion,
        }


@dataclass
class RiskAssessment:
    """Risk assessment for a refactoring.

    Attributes:
        overall_risk: Overall risk level.
        risk_factors: List of contributing factors.
        files_at_risk: Number of files at risk.
        tests_affected: Number of tests affected.
        public_api_changes: Number of public API changes.
    """

    overall_risk: RiskLevel
    risk_factors: list[str] = field(default_factory=list)
    files_at_risk: int = 0
    tests_affected: int = 0
    public_api_changes: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_risk": self.overall_risk.value,
            "risk_factors": self.risk_factors,
            "files_at_risk": self.files_at_risk,
            "tests_affected": self.tests_affected,
            "public_api_changes": self.public_api_changes,
        }


@dataclass
class SafetyReport:
    """Full safety analysis report.

    Attributes:
        is_safe: Whether refactoring is safe to proceed.
        risk_assessment: Risk assessment.
        file_impacts: List of file impacts.
        warnings: List of warnings.
        suggestions: List of suggestions.
        analyzed_at: When analysis was performed.
    """

    is_safe: bool
    risk_assessment: RiskAssessment
    file_impacts: list[FileImpact] = field(default_factory=list)
    warnings: list[Warning] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    analyzed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_safe": self.is_safe,
            "risk_assessment": self.risk_assessment.to_dict(),
            "file_impacts": [f.to_dict() for f in self.file_impacts],
            "warnings": [w.to_dict() for w in self.warnings],
            "suggestions": self.suggestions,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }


@dataclass
class RefactoringPlan:
    """A plan for refactoring to analyze.

    Attributes:
        name: Plan name.
        operation: Operation type (rename, move, extract, etc.).
        target_files: Files to modify.
        symbol_name: Symbol being refactored.
        new_name: New name (for rename operations).
        content_changes: Dict of file path to new content.
    """

    name: str
    operation: str
    target_files: list[Path] = field(default_factory=list)
    symbol_name: str | None = None
    new_name: str | None = None
    content_changes: dict[str, str] = field(default_factory=dict)


@dataclass
class SafetyAnalyzer:
    """Service for analyzing safety of refactoring operations.

    Performs impact analysis and risk assessment before executing
    refactoring operations.

    Attributes:
        repo_root: Root directory of the repository.
        test_patterns: Patterns for identifying test files.
        public_patterns: Patterns for identifying public APIs.
    """

    repo_root: Path
    test_patterns: list[str] = field(
        default_factory=lambda: ["**/test_*.py", "**/tests/*.py", "**/*_test.py"]
    )
    public_patterns: list[str] = field(
        default_factory=lambda: ["**/__init__.py", "**/api.py", "**/public.py"]
    )

    def analyze(self, plan: RefactoringPlan) -> SafetyReport:
        """Analyze a refactoring plan for safety.

        Args:
            plan: Refactoring plan to analyze.

        Returns:
            SafetyReport with analysis results.
        """
        file_impacts: list[FileImpact] = []
        warnings: list[Warning] = []
        suggestions: list[str] = []

        # Analyze each target file
        for file_path in plan.target_files:
            if file_path.exists():
                impacts = self._analyze_file_impact(file_path, plan)
                file_impacts.extend(impacts)

        # Analyze content changes
        for file_path_str, new_content in plan.content_changes.items():
            file_path = Path(file_path_str)
            if file_path.exists():
                change_warnings = self._analyze_content_change(
                    file_path, new_content, plan
                )
                warnings.extend(change_warnings)

        # Calculate risk assessment
        risk_assessment = self._calculate_risk(file_impacts, warnings, plan)

        # Generate suggestions
        suggestions = self._generate_suggestions(
            file_impacts, warnings, risk_assessment
        )

        # Determine if safe to proceed
        is_safe = risk_assessment.overall_risk in (RiskLevel.LOW, RiskLevel.MEDIUM)

        return SafetyReport(
            is_safe=is_safe,
            risk_assessment=risk_assessment,
            file_impacts=file_impacts,
            warnings=warnings,
            suggestions=suggestions,
            analyzed_at=datetime.now(UTC),
        )

    def _analyze_file_impact(
        self,
        file_path: Path,
        plan: RefactoringPlan,
    ) -> list[FileImpact]:
        """Analyze impact on a single file.

        Args:
            file_path: Path to file.
            plan: Refactoring plan.

        Returns:
            List of FileImpact objects.
        """
        impacts: list[FileImpact] = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError:
            return impacts

        # Determine impact type
        is_test = self._is_test_file(file_path)
        is_public = self._is_public_api(file_path)

        if is_test:
            impact_type = ImpactType.TEST_IMPACT
        elif is_public:
            impact_type = ImpactType.BREAKING_CHANGE
        else:
            impact_type = ImpactType.STRUCTURAL_CHANGE

        # Count changes
        changes_count = 0
        lines_affected: list[int] = []

        if plan.symbol_name:
            # Find all occurrences of the symbol
            pattern = r"\b" + re.escape(plan.symbol_name) + r"\b"
            for i, line in enumerate(content.split("\n"), 1):
                if re.search(pattern, line):
                    changes_count += 1
                    lines_affected.append(i)

        if changes_count > 0:
            impacts.append(
                FileImpact(
                    file_path=str(file_path),
                    impact_type=impact_type,
                    changes_count=changes_count,
                    lines_affected=lines_affected,
                    description=f"{plan.operation} affects {changes_count} locations",
                )
            )

        return impacts

    def _analyze_content_change(
        self,
        file_path: Path,
        new_content: str,
        plan: RefactoringPlan,
    ) -> list[Warning]:
        """Analyze a content change for warnings.

        Args:
            file_path: Path to file.
            new_content: New content.
            plan: Refactoring plan.

        Returns:
            List of Warning objects.
        """
        warnings: list[Warning] = []

        try:
            original_content = file_path.read_text(encoding="utf-8")
        except OSError:
            return warnings

        # Check for potential issues in new content
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            warnings.append(
                Warning(
                    type=WarningType.COMPLEX_CHANGE,
                    message=f"New content has syntax error: {e}",
                    file_path=str(file_path),
                    suggestion="Fix syntax error before applying",
                )
            )

        # Check for public API changes
        if self._is_public_api(file_path):
            original_exports = self._get_exports(original_content)
            new_exports = self._get_exports(new_content)

            removed = original_exports - new_exports
            for export in removed:
                warnings.append(
                    Warning(
                        type=WarningType.PUBLIC_API_CHANGE,
                        message=f"Public API '{export}' removed",
                        file_path=str(file_path),
                        suggestion="Ensure removal is intentional",
                    )
                )

        # Check for missing docstrings on new functions
        try:
            new_tree = ast.parse(new_content)
            for node in ast.walk(new_tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        if not node.name.startswith("_"):
                            warnings.append(
                                Warning(
                                    type=WarningType.MISSING_DOCSTRING,
                                    message=f"Public {type(node).__name__} '{node.name}' missing docstring",
                                    file_path=str(file_path),
                                    line=node.lineno,
                                    suggestion="Add docstring for documentation",
                                )
                            )
        except SyntaxError:
            pass

        return warnings

    def _get_exports(self, content: str) -> set[str]:
        """Get exported names from module content.

        Args:
            content: Python source code.

        Returns:
            Set of exported names.
        """
        exports: set[str] = set()

        try:
            tree = ast.parse(content)

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):
                        exports.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith("_"):
                        exports.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if not target.id.startswith("_"):
                                exports.add(target.id)

        except SyntaxError:
            pass

        return exports

    def _calculate_risk(
        self,
        file_impacts: list[FileImpact],
        warnings: list[Warning],
        plan: RefactoringPlan,
    ) -> RiskAssessment:
        """Calculate overall risk assessment.

        Args:
            file_impacts: List of file impacts.
            warnings: List of warnings.
            plan: Refactoring plan.

        Returns:
            RiskAssessment.
        """
        risk_factors: list[str] = []
        files_at_risk = len(file_impacts)
        tests_affected = sum(
            1 for f in file_impacts if f.impact_type == ImpactType.TEST_IMPACT
        )
        public_api_changes = sum(
            1 for f in file_impacts if f.impact_type == ImpactType.BREAKING_CHANGE
        )

        # Calculate risk level based on factors
        risk_score = 0

        # File count factor
        if files_at_risk > 20:
            risk_score += 3
            risk_factors.append(f"Large number of files affected: {files_at_risk}")
        elif files_at_risk > 10:
            risk_score += 2
            risk_factors.append(f"Moderate number of files affected: {files_at_risk}")
        elif files_at_risk > 5:
            risk_score += 1

        # Public API factor
        if public_api_changes > 5:
            risk_score += 3
            risk_factors.append(
                f"Multiple public API changes: {public_api_changes}"
            )
        elif public_api_changes > 0:
            risk_score += 2
            risk_factors.append(f"Public API affected: {public_api_changes} files")

        # Test impact factor
        if tests_affected > 10:
            risk_score += 2
            risk_factors.append(f"Many tests affected: {tests_affected}")
        elif tests_affected > 0:
            risk_score += 1
            risk_factors.append(f"Tests affected: {tests_affected}")

        # Warning factor
        critical_warnings = sum(
            1
            for w in warnings
            if w.type
            in (WarningType.PUBLIC_API_CHANGE, WarningType.CIRCULAR_DEPENDENCY)
        )
        if critical_warnings > 0:
            risk_score += 2
            risk_factors.append(f"Critical warnings: {critical_warnings}")

        # Determine overall risk level
        if risk_score >= 6:
            overall_risk = RiskLevel.CRITICAL
        elif risk_score >= 4:
            overall_risk = RiskLevel.HIGH
        elif risk_score >= 2:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        return RiskAssessment(
            overall_risk=overall_risk,
            risk_factors=risk_factors,
            files_at_risk=files_at_risk,
            tests_affected=tests_affected,
            public_api_changes=public_api_changes,
        )

    def _generate_suggestions(
        self,
        file_impacts: list[FileImpact],
        warnings: list[Warning],
        risk_assessment: RiskAssessment,
    ) -> list[str]:
        """Generate suggestions based on analysis.

        Args:
            file_impacts: List of file impacts.
            warnings: List of warnings.
            risk_assessment: Risk assessment.

        Returns:
            List of suggestion strings.
        """
        suggestions: list[str] = []

        if risk_assessment.overall_risk == RiskLevel.CRITICAL:
            suggestions.append("Consider breaking this refactoring into smaller steps")
            suggestions.append("Ensure comprehensive test coverage before proceeding")

        if risk_assessment.public_api_changes > 0:
            suggestions.append("Update documentation for public API changes")
            suggestions.append("Consider deprecation warnings before removal")

        if risk_assessment.tests_affected > 0:
            suggestions.append("Run affected tests after refactoring")
            suggestions.append("Review test assertions for correctness")

        # Add suggestions from warnings
        for warning in warnings:
            if warning.suggestion and warning.suggestion not in suggestions:
                suggestions.append(warning.suggestion)

        return suggestions

    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file.

        Args:
            file_path: Path to file.

        Returns:
            True if test file.
        """
        name = file_path.name
        path_str = str(file_path)

        return (
            name.startswith("test_")
            or name.endswith("_test.py")
            or "/tests/" in path_str
            or "\\tests\\" in path_str
        )

    def _is_public_api(self, file_path: Path) -> bool:
        """Check if file is part of public API.

        Args:
            file_path: Path to file.

        Returns:
            True if public API file.
        """
        name = file_path.name
        return name == "__init__.py" or name == "api.py" or name == "public.py"

    def check_symbol_usage(
        self,
        symbol: str,
        directory: Path | None = None,
    ) -> list[FileImpact]:
        """Check where a symbol is used across the codebase.

        Args:
            symbol: Symbol name to search for.
            directory: Directory to search (defaults to repo_root).

        Returns:
            List of FileImpact objects.
        """
        if directory is None:
            directory = self.repo_root

        impacts: list[FileImpact] = []
        pattern = r"\b" + re.escape(symbol) + r"\b"

        for file_path in directory.rglob("*.py"):
            try:
                content = file_path.read_text(encoding="utf-8")
            except OSError:
                continue

            lines_affected: list[int] = []
            for i, line in enumerate(content.split("\n"), 1):
                if re.search(pattern, line):
                    lines_affected.append(i)

            if lines_affected:
                is_test = self._is_test_file(file_path)
                impacts.append(
                    FileImpact(
                        file_path=str(file_path),
                        impact_type=(
                            ImpactType.TEST_IMPACT
                            if is_test
                            else ImpactType.DEPENDENCY_CHANGE
                        ),
                        changes_count=len(lines_affected),
                        lines_affected=lines_affected,
                        description=f"Symbol '{symbol}' found in {len(lines_affected)} locations",
                    )
                )

        return impacts

    def estimate_complexity(
        self,
        plan: RefactoringPlan,
    ) -> dict[str, Any]:
        """Estimate complexity of a refactoring.

        Args:
            plan: Refactoring plan.

        Returns:
            Complexity estimate dict.
        """
        total_files = len(plan.target_files)
        total_changes = 0
        lines_of_code = 0

        for file_path in plan.target_files:
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    lines_of_code += len(content.split("\n"))

                    if plan.symbol_name:
                        pattern = r"\b" + re.escape(plan.symbol_name) + r"\b"
                        total_changes += len(re.findall(pattern, content))
                except OSError:
                    pass

        # Classify complexity
        if total_changes > 100 or total_files > 20:
            complexity = "high"
        elif total_changes > 30 or total_files > 10:
            complexity = "medium"
        else:
            complexity = "low"

        return {
            "complexity": complexity,
            "total_files": total_files,
            "total_changes": total_changes,
            "lines_of_code": lines_of_code,
        }

    def validate_refactoring_result(
        self,
        original_files: dict[str, str],
        modified_files: dict[str, str],
    ) -> list[Warning]:
        """Validate refactoring results.

        Args:
            original_files: Dict of file path to original content.
            modified_files: Dict of file path to modified content.

        Returns:
            List of warnings.
        """
        warnings: list[Warning] = []

        for file_path, new_content in modified_files.items():
            # Check syntax
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                warnings.append(
                    Warning(
                        type=WarningType.COMPLEX_CHANGE,
                        message=f"Syntax error in result: {e}",
                        file_path=file_path,
                    )
                )
                continue

            # Check for removed functionality
            if file_path in original_files:
                original_exports = self._get_exports(original_files[file_path])
                new_exports = self._get_exports(new_content)

                removed = original_exports - new_exports
                for export in removed:
                    warnings.append(
                        Warning(
                            type=WarningType.PUBLIC_API_CHANGE,
                            message=f"Export '{export}' was removed",
                            file_path=file_path,
                        )
                    )

        return warnings
