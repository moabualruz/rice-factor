"""Tests for SafetyAnalyzer."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rice_factor.domain.services.safety_analyzer import (
    FileImpact,
    ImpactType,
    RefactoringPlan,
    RiskAssessment,
    RiskLevel,
    SafetyAnalyzer,
    SafetyReport,
    Warning,
    WarningType,
)

if TYPE_CHECKING:
    pass


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_all_levels_exist(self) -> None:
        """Test all risk levels are defined."""
        assert RiskLevel.LOW
        assert RiskLevel.MEDIUM
        assert RiskLevel.HIGH
        assert RiskLevel.CRITICAL


class TestImpactType:
    """Tests for ImpactType enum."""

    def test_all_types_exist(self) -> None:
        """Test all impact types are defined."""
        assert ImpactType.BREAKING_CHANGE
        assert ImpactType.BEHAVIORAL_CHANGE
        assert ImpactType.STRUCTURAL_CHANGE
        assert ImpactType.DEPENDENCY_CHANGE
        assert ImpactType.TEST_IMPACT
        assert ImpactType.CONFIG_IMPACT


class TestWarningType:
    """Tests for WarningType enum."""

    def test_all_types_exist(self) -> None:
        """Test all warning types are defined."""
        assert WarningType.UNUSED_IMPORT
        assert WarningType.CIRCULAR_DEPENDENCY
        assert WarningType.PUBLIC_API_CHANGE
        assert WarningType.TEST_COVERAGE_GAP
        assert WarningType.COMPLEX_CHANGE
        assert WarningType.MISSING_DOCSTRING
        assert WarningType.TYPE_MISMATCH


class TestFileImpact:
    """Tests for FileImpact model."""

    def test_creation(self) -> None:
        """Test impact creation."""
        impact = FileImpact(
            file_path="/test/file.py",
            impact_type=ImpactType.STRUCTURAL_CHANGE,
        )
        assert impact.file_path == "/test/file.py"
        assert impact.impact_type == ImpactType.STRUCTURAL_CHANGE

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        impact = FileImpact(
            file_path="/test/file.py",
            impact_type=ImpactType.TEST_IMPACT,
            changes_count=5,
            lines_affected=[1, 2, 3],
            description="Test impact",
        )
        d = impact.to_dict()
        assert d["file_path"] == "/test/file.py"
        assert d["impact_type"] == "test_impact"
        assert d["changes_count"] == 5


class TestWarning:
    """Tests for Warning model."""

    def test_creation(self) -> None:
        """Test warning creation."""
        warning = Warning(
            type=WarningType.PUBLIC_API_CHANGE,
            message="API change detected",
        )
        assert warning.type == WarningType.PUBLIC_API_CHANGE
        assert warning.message == "API change detected"

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        warning = Warning(
            type=WarningType.MISSING_DOCSTRING,
            message="Missing docstring",
            file_path="/test.py",
            line=10,
            suggestion="Add docstring",
        )
        d = warning.to_dict()
        assert d["type"] == "missing_docstring"
        assert d["suggestion"] == "Add docstring"


class TestRiskAssessment:
    """Tests for RiskAssessment model."""

    def test_creation(self) -> None:
        """Test assessment creation."""
        assessment = RiskAssessment(
            overall_risk=RiskLevel.MEDIUM,
            risk_factors=["Test factor"],
        )
        assert assessment.overall_risk == RiskLevel.MEDIUM

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        assessment = RiskAssessment(
            overall_risk=RiskLevel.HIGH,
            files_at_risk=10,
            tests_affected=5,
        )
        d = assessment.to_dict()
        assert d["overall_risk"] == "high"
        assert d["files_at_risk"] == 10


class TestSafetyReport:
    """Tests for SafetyReport model."""

    def test_creation(self) -> None:
        """Test report creation."""
        report = SafetyReport(
            is_safe=True,
            risk_assessment=RiskAssessment(overall_risk=RiskLevel.LOW),
        )
        assert report.is_safe is True

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        report = SafetyReport(
            is_safe=False,
            risk_assessment=RiskAssessment(overall_risk=RiskLevel.CRITICAL),
            suggestions=["Review carefully"],
        )
        d = report.to_dict()
        assert d["is_safe"] is False
        assert "Review carefully" in d["suggestions"]


class TestRefactoringPlan:
    """Tests for RefactoringPlan model."""

    def test_creation(self) -> None:
        """Test plan creation."""
        plan = RefactoringPlan(
            name="rename_function",
            operation="rename",
            symbol_name="old_name",
            new_name="new_name",
        )
        assert plan.name == "rename_function"
        assert plan.operation == "rename"


class TestSafetyAnalyzer:
    """Tests for SafetyAnalyzer."""

    def test_creation(self, tmp_path: Path) -> None:
        """Test analyzer creation."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)
        assert analyzer.repo_root == tmp_path
        assert len(analyzer.test_patterns) > 0

    def test_analyze_empty_plan(self, tmp_path: Path) -> None:
        """Test analyzing empty plan."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)
        plan = RefactoringPlan(name="empty", operation="none")

        report = analyzer.analyze(plan)

        assert report.is_safe is True
        assert report.risk_assessment.overall_risk == RiskLevel.LOW

    def test_analyze_with_symbol(self, tmp_path: Path) -> None:
        """Test analyzing plan with symbol."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        # Create test file
        test_file = tmp_path / "module.py"
        test_file.write_text("def old_func():\n    pass\n\nold_func()\n")

        plan = RefactoringPlan(
            name="rename",
            operation="rename",
            target_files=[test_file],
            symbol_name="old_func",
            new_name="new_func",
        )

        report = analyzer.analyze(plan)

        assert len(report.file_impacts) > 0
        assert report.file_impacts[0].changes_count == 2

    def test_analyze_test_file_impact(self, tmp_path: Path) -> None:
        """Test that test files are identified correctly."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        # Create test file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def test_func():\n    old_func()\n")

        plan = RefactoringPlan(
            name="rename",
            operation="rename",
            target_files=[test_file],
            symbol_name="old_func",
        )

        report = analyzer.analyze(plan)

        # Should be identified as test impact
        test_impacts = [
            i for i in report.file_impacts if i.impact_type == ImpactType.TEST_IMPACT
        ]
        assert len(test_impacts) > 0

    def test_analyze_public_api_impact(self, tmp_path: Path) -> None:
        """Test that public API files are identified correctly."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        # Create __init__.py
        init_file = tmp_path / "__init__.py"
        init_file.write_text("from .module import old_func\n")

        plan = RefactoringPlan(
            name="rename",
            operation="rename",
            target_files=[init_file],
            symbol_name="old_func",
        )

        report = analyzer.analyze(plan)

        # Should be identified as breaking change
        breaking = [
            i for i in report.file_impacts if i.impact_type == ImpactType.BREAKING_CHANGE
        ]
        assert len(breaking) > 0

    def test_analyze_content_change_syntax_error(self, tmp_path: Path) -> None:
        """Test analyzing content with syntax error."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        test_file = tmp_path / "module.py"
        test_file.write_text("x = 1\n")

        plan = RefactoringPlan(
            name="modify",
            operation="modify",
            target_files=[test_file],
            content_changes={str(test_file): "x = ((\n"},  # Syntax error
        )

        report = analyzer.analyze(plan)

        # Should have warning about syntax error
        syntax_warnings = [
            w for w in report.warnings if w.type == WarningType.COMPLEX_CHANGE
        ]
        assert len(syntax_warnings) > 0

    def test_risk_calculation_low(self, tmp_path: Path) -> None:
        """Test low risk calculation."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        # Create single small file
        test_file = tmp_path / "module.py"
        test_file.write_text("x = 1\n")

        plan = RefactoringPlan(
            name="small",
            operation="modify",
            target_files=[test_file],
            symbol_name="x",
        )

        report = analyzer.analyze(plan)

        assert report.risk_assessment.overall_risk == RiskLevel.LOW

    def test_risk_calculation_high(self, tmp_path: Path) -> None:
        """Test high risk calculation."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        # Create many files including public API
        files = []
        for i in range(15):
            f = tmp_path / f"module{i}.py"
            f.write_text(f"old_name = {i}\n")
            files.append(f)

        # Add some __init__.py files
        for i in range(3):
            subdir = tmp_path / f"pkg{i}"
            subdir.mkdir()
            init = subdir / "__init__.py"
            init.write_text("from .mod import old_name\n")
            files.append(init)

        plan = RefactoringPlan(
            name="large_rename",
            operation="rename",
            target_files=files,
            symbol_name="old_name",
        )

        report = analyzer.analyze(plan)

        assert report.risk_assessment.overall_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_is_test_file(self, tmp_path: Path) -> None:
        """Test test file detection."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        assert analyzer._is_test_file(Path("test_module.py"))
        assert analyzer._is_test_file(Path("module_test.py"))
        # Create actual path in tests directory to handle both Windows/Unix
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "module.py"
        assert analyzer._is_test_file(test_file)
        assert not analyzer._is_test_file(Path("module.py"))

    def test_is_public_api(self, tmp_path: Path) -> None:
        """Test public API detection."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        assert analyzer._is_public_api(Path("__init__.py"))
        assert analyzer._is_public_api(Path("api.py"))
        assert analyzer._is_public_api(Path("public.py"))
        assert not analyzer._is_public_api(Path("private.py"))

    def test_check_symbol_usage(self, tmp_path: Path) -> None:
        """Test checking symbol usage."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        # Create files using the symbol
        (tmp_path / "a.py").write_text("from module import my_func\nmy_func()\n")
        (tmp_path / "b.py").write_text("# Does not use it\n")
        (tmp_path / "c.py").write_text("my_func = 1\n")

        impacts = analyzer.check_symbol_usage("my_func")

        assert len(impacts) == 2  # a.py and c.py
        total_changes = sum(i.changes_count for i in impacts)
        assert total_changes == 3  # 2 in a.py, 1 in c.py

    def test_estimate_complexity_low(self, tmp_path: Path) -> None:
        """Test low complexity estimation."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        test_file = tmp_path / "module.py"
        test_file.write_text("x = 1\nx = 2\n")

        plan = RefactoringPlan(
            name="small",
            operation="rename",
            target_files=[test_file],
            symbol_name="x",
        )

        estimate = analyzer.estimate_complexity(plan)

        assert estimate["complexity"] == "low"
        assert estimate["total_files"] == 1
        assert estimate["total_changes"] == 2

    def test_estimate_complexity_high(self, tmp_path: Path) -> None:
        """Test high complexity estimation."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        # Create many files with many changes
        files = []
        for i in range(25):
            f = tmp_path / f"module{i}.py"
            f.write_text("old_name\n" * 10)
            files.append(f)

        plan = RefactoringPlan(
            name="large",
            operation="rename",
            target_files=files,
            symbol_name="old_name",
        )

        estimate = analyzer.estimate_complexity(plan)

        assert estimate["complexity"] == "high"
        assert estimate["total_files"] == 25

    def test_validate_refactoring_result_valid(self, tmp_path: Path) -> None:
        """Test validating valid refactoring result."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        original = {"file.py": "def old_func(): pass\n"}
        modified = {"file.py": "def new_func(): pass\n"}

        warnings = analyzer.validate_refactoring_result(original, modified)

        # Should have warning about removed export
        api_warnings = [
            w for w in warnings if w.type == WarningType.PUBLIC_API_CHANGE
        ]
        assert len(api_warnings) == 1
        assert "old_func" in api_warnings[0].message

    def test_validate_refactoring_result_syntax_error(self, tmp_path: Path) -> None:
        """Test validating result with syntax error."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        modified = {"file.py": "def broken(:\n"}

        warnings = analyzer.validate_refactoring_result({}, modified)

        syntax_warnings = [
            w for w in warnings if w.type == WarningType.COMPLEX_CHANGE
        ]
        assert len(syntax_warnings) == 1

    def test_generate_suggestions(self, tmp_path: Path) -> None:
        """Test suggestion generation."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        # Create files for high risk scenario
        files = []
        for i in range(15):
            f = tmp_path / f"module{i}.py"
            f.write_text("old_name = 1\n")
            files.append(f)

        # Add init files for public API
        init = tmp_path / "__init__.py"
        init.write_text("old_name = 1\n")
        files.append(init)

        plan = RefactoringPlan(
            name="rename",
            operation="rename",
            target_files=files,
            symbol_name="old_name",
        )

        report = analyzer.analyze(plan)

        # Should have suggestions
        assert len(report.suggestions) > 0

    def test_get_exports(self, tmp_path: Path) -> None:
        """Test getting exports from content."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        content = """
def public_func():
    pass

def _private_func():
    pass

class PublicClass:
    pass

class _PrivateClass:
    pass

PUBLIC_VAR = 1
_private_var = 2
"""
        exports = analyzer._get_exports(content)

        assert "public_func" in exports
        assert "_private_func" not in exports
        assert "PublicClass" in exports
        assert "_PrivateClass" not in exports
        assert "PUBLIC_VAR" in exports
        assert "_private_var" not in exports

    def test_analyze_missing_docstring_warning(self, tmp_path: Path) -> None:
        """Test warning for missing docstring."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        test_file = tmp_path / "module.py"
        test_file.write_text("def old_func(): pass\n")

        plan = RefactoringPlan(
            name="modify",
            operation="modify",
            target_files=[test_file],
            content_changes={str(test_file): "def public_func():\n    pass\n"},
        )

        report = analyzer.analyze(plan)

        docstring_warnings = [
            w for w in report.warnings if w.type == WarningType.MISSING_DOCSTRING
        ]
        assert len(docstring_warnings) > 0

    def test_analyze_nonexistent_file(self, tmp_path: Path) -> None:
        """Test analyzing nonexistent file."""
        analyzer = SafetyAnalyzer(repo_root=tmp_path)

        plan = RefactoringPlan(
            name="nonexistent",
            operation="rename",
            target_files=[tmp_path / "nonexistent.py"],
            symbol_name="x",
        )

        report = analyzer.analyze(plan)

        # Should not crash, just have no impacts
        assert report.is_safe is True
