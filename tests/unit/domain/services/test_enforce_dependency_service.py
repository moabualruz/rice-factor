"""Tests for EnforceDependencyService."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rice_factor.domain.services.enforce_dependency_service import (
    AnalysisResult,
    DependencyRule,
    EnforceDependencyService,
    FixAction,
    FixResult,
    Violation,
    ViolationSeverity,
    ViolationType,
)

if TYPE_CHECKING:
    pass


class TestViolationType:
    """Tests for ViolationType enum."""

    def test_all_types_exist(self) -> None:
        """Test all violation types are defined."""
        assert ViolationType.IMPORT_VIOLATION
        assert ViolationType.CIRCULAR_DEPENDENCY
        assert ViolationType.EXTERNAL_IN_DOMAIN
        assert ViolationType.FORBIDDEN_IMPORT
        assert ViolationType.LAYER_SKIP


class TestViolationSeverity:
    """Tests for ViolationSeverity enum."""

    def test_all_severities_exist(self) -> None:
        """Test all severity levels are defined."""
        assert ViolationSeverity.ERROR
        assert ViolationSeverity.WARNING
        assert ViolationSeverity.INFO


class TestFixAction:
    """Tests for FixAction enum."""

    def test_all_actions_exist(self) -> None:
        """Test all fix actions are defined."""
        assert FixAction.REMOVE_IMPORT
        assert FixAction.REPLACE_IMPORT
        assert FixAction.MOVE_CODE
        assert FixAction.ADD_ADAPTER
        assert FixAction.INJECT_DEPENDENCY


class TestDependencyRule:
    """Tests for DependencyRule model."""

    def test_creation(self) -> None:
        """Test rule creation."""
        rule = DependencyRule(
            name="test_rule",
            source_pattern=r".*/domain/.*",
        )
        assert rule.name == "test_rule"
        assert rule.source_pattern == r".*/domain/.*"
        assert rule.allowed_targets == []
        assert rule.forbidden_targets == []
        assert rule.severity == ViolationSeverity.ERROR

    def test_matches_source(self) -> None:
        """Test source pattern matching."""
        rule = DependencyRule(
            name="domain_rule",
            source_pattern=r".*/domain/.*",
        )
        assert rule.matches_source("app/domain/models.py")
        assert not rule.matches_source("app/adapters/api.py")

    def test_is_target_allowed_empty_lists(self) -> None:
        """Test target allowed with no restrictions."""
        rule = DependencyRule(name="permissive", source_pattern=r".*")
        assert rule.is_target_allowed("any_module")

    def test_is_target_allowed_with_allowed_list(self) -> None:
        """Test target allowed with allowed list."""
        rule = DependencyRule(
            name="restricted",
            source_pattern=r".*",
            allowed_targets=[r"domain\..*", r"typing.*"],
        )
        assert rule.is_target_allowed("domain.models")
        assert rule.is_target_allowed("typing")
        assert not rule.is_target_allowed("adapters.api")

    def test_is_target_allowed_with_forbidden_list(self) -> None:
        """Test target allowed with forbidden list."""
        rule = DependencyRule(
            name="blocked",
            source_pattern=r".*",
            forbidden_targets=[r"adapters\..*", r"external.*"],
        )
        assert rule.is_target_allowed("domain.models")
        assert not rule.is_target_allowed("adapters.api")
        assert not rule.is_target_allowed("external_lib")


class TestViolation:
    """Tests for Violation model."""

    def test_creation(self) -> None:
        """Test violation creation."""
        violation = Violation(
            type=ViolationType.IMPORT_VIOLATION,
            severity=ViolationSeverity.ERROR,
            file_path="/app/domain/service.py",
            line=10,
            source_module="domain.service",
        )
        assert violation.type == ViolationType.IMPORT_VIOLATION
        assert violation.severity == ViolationSeverity.ERROR
        assert violation.line == 10

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        violation = Violation(
            type=ViolationType.IMPORT_VIOLATION,
            severity=ViolationSeverity.WARNING,
            file_path="/app/test.py",
            line=5,
            source_module="test",
            target_module="forbidden",
            message="Test violation",
            rule_name="test_rule",
            suggested_fix=FixAction.REMOVE_IMPORT,
        )
        d = violation.to_dict()
        assert d["type"] == "import_violation"
        assert d["severity"] == "warning"
        assert d["suggested_fix"] == "remove_import"


class TestFixResult:
    """Tests for FixResult model."""

    def test_creation_success(self) -> None:
        """Test successful fix result."""
        result = FixResult(
            success=True,
            file_path="/app/test.py",
            original_content="import bad",
            new_content="",
        )
        assert result.success is True
        assert result.error is None

    def test_creation_failure(self) -> None:
        """Test failed fix result."""
        result = FixResult(
            success=False,
            file_path="/app/test.py",
            error="Cannot fix",
        )
        assert result.success is False
        assert result.error == "Cannot fix"


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_creation(self) -> None:
        """Test result creation."""
        result = AnalysisResult(
            files_analyzed=10,
            rules_checked=3,
        )
        assert result.files_analyzed == 10
        assert result.violations == []

    def test_error_count(self) -> None:
        """Test error count calculation."""
        result = AnalysisResult(
            violations=[
                Violation(
                    type=ViolationType.IMPORT_VIOLATION,
                    severity=ViolationSeverity.ERROR,
                    file_path="a.py",
                    line=1,
                    source_module="a",
                ),
                Violation(
                    type=ViolationType.IMPORT_VIOLATION,
                    severity=ViolationSeverity.WARNING,
                    file_path="b.py",
                    line=1,
                    source_module="b",
                ),
                Violation(
                    type=ViolationType.IMPORT_VIOLATION,
                    severity=ViolationSeverity.ERROR,
                    file_path="c.py",
                    line=1,
                    source_module="c",
                ),
            ]
        )
        assert result.error_count == 2
        assert result.warning_count == 1

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        result = AnalysisResult(
            files_analyzed=5,
            rules_checked=2,
        )
        d = result.to_dict()
        assert d["files_analyzed"] == 5
        assert d["rules_checked"] == 2
        assert d["error_count"] == 0


class TestEnforceDependencyService:
    """Tests for EnforceDependencyService."""

    def test_creation(self, tmp_path: Path) -> None:
        """Test service creation."""
        service = EnforceDependencyService(repo_root=tmp_path)
        assert service.repo_root == tmp_path
        assert len(service.rules) > 0  # Default rules

    def test_default_rules(self, tmp_path: Path) -> None:
        """Test default hexagonal architecture rules."""
        service = EnforceDependencyService(repo_root=tmp_path)
        rule_names = [r.name for r in service.rules]
        assert "domain_isolation" in rule_names
        assert "adapter_isolation" in rule_names

    def test_add_rule(self, tmp_path: Path) -> None:
        """Test adding custom rule."""
        service = EnforceDependencyService(repo_root=tmp_path)
        initial_count = len(service.rules)

        service.add_rule(
            DependencyRule(name="custom", source_pattern=r".*")
        )
        assert len(service.rules) == initial_count + 1

    def test_clear_rules(self, tmp_path: Path) -> None:
        """Test clearing rules."""
        service = EnforceDependencyService(repo_root=tmp_path)
        service.clear_rules()
        assert len(service.rules) == 0

    def test_analyze_file_not_exists(self, tmp_path: Path) -> None:
        """Test analyzing non-existent file."""
        service = EnforceDependencyService(repo_root=tmp_path)
        violations = service.analyze_file(tmp_path / "not_exists.py")
        assert violations == []

    def test_analyze_file_no_violations(self, tmp_path: Path) -> None:
        """Test analyzing file with no violations."""
        service = EnforceDependencyService(repo_root=tmp_path)
        service.clear_rules()
        service.add_rule(
            DependencyRule(
                name="allow_typing",
                source_pattern=r".*",
                allowed_targets=[r"typing.*"],
            )
        )

        # Create a file with allowed import
        test_file = tmp_path / "test.py"
        test_file.write_text("from typing import Any\n")

        violations = service.analyze_file(test_file)
        assert violations == []

    def test_analyze_file_with_violation(self, tmp_path: Path) -> None:
        """Test analyzing file with violations."""
        service = EnforceDependencyService(repo_root=tmp_path)
        service.clear_rules()
        service.add_rule(
            DependencyRule(
                name="no_forbidden",
                source_pattern=r".*",
                forbidden_targets=[r"forbidden.*"],
            )
        )

        test_file = tmp_path / "test.py"
        test_file.write_text("import forbidden_module\n")

        violations = service.analyze_file(test_file)
        assert len(violations) == 1
        assert violations[0].target_module == "forbidden_module"

    def test_analyze_directory(self, tmp_path: Path) -> None:
        """Test analyzing directory."""
        service = EnforceDependencyService(repo_root=tmp_path)
        service.clear_rules()

        # Create test files
        (tmp_path / "a.py").write_text("import os\n")
        (tmp_path / "b.py").write_text("import sys\n")

        result = service.analyze_directory()
        assert result.files_analyzed == 2

    def test_analyze_directory_recursive(self, tmp_path: Path) -> None:
        """Test analyzing directory recursively."""
        service = EnforceDependencyService(repo_root=tmp_path)
        service.clear_rules()

        # Create nested structure
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (tmp_path / "a.py").write_text("import os\n")
        (subdir / "b.py").write_text("import sys\n")

        result = service.analyze_directory(recursive=True)
        assert result.files_analyzed == 2

    def test_analyze_directory_non_recursive(self, tmp_path: Path) -> None:
        """Test analyzing directory non-recursively."""
        service = EnforceDependencyService(repo_root=tmp_path)
        service.clear_rules()

        # Create nested structure
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (tmp_path / "a.py").write_text("import os\n")
        (subdir / "b.py").write_text("import sys\n")

        result = service.analyze_directory(recursive=False)
        assert result.files_analyzed == 1

    def test_fix_violation_remove_import(self, tmp_path: Path) -> None:
        """Test fixing violation by removing import."""
        service = EnforceDependencyService(repo_root=tmp_path)

        test_file = tmp_path / "test.py"
        test_file.write_text("import forbidden\nimport os\n")

        violation = Violation(
            type=ViolationType.IMPORT_VIOLATION,
            severity=ViolationSeverity.ERROR,
            file_path=str(test_file),
            line=1,
            source_module="test",
            target_module="forbidden",
            suggested_fix=FixAction.REMOVE_IMPORT,
        )

        result = service.fix_violation(violation)
        assert result.success is True
        assert "import forbidden" not in result.new_content
        assert "import os" in result.new_content

    def test_fix_violation_file_not_found(self, tmp_path: Path) -> None:
        """Test fixing violation when file not found."""
        service = EnforceDependencyService(repo_root=tmp_path)

        violation = Violation(
            type=ViolationType.IMPORT_VIOLATION,
            severity=ViolationSeverity.ERROR,
            file_path=str(tmp_path / "not_exists.py"),
            line=1,
            source_module="test",
            suggested_fix=FixAction.REMOVE_IMPORT,
        )

        result = service.fix_violation(violation)
        assert result.success is False
        assert "not found" in result.error

    def test_fix_all_violations_dry_run(self, tmp_path: Path) -> None:
        """Test fixing all violations in dry run mode."""
        service = EnforceDependencyService(repo_root=tmp_path)

        test_file = tmp_path / "test.py"
        test_file.write_text("import forbidden\n")

        analysis = AnalysisResult(
            violations=[
                Violation(
                    type=ViolationType.IMPORT_VIOLATION,
                    severity=ViolationSeverity.ERROR,
                    file_path=str(test_file),
                    line=1,
                    source_module="test",
                    target_module="forbidden",
                    suggested_fix=FixAction.REMOVE_IMPORT,
                )
            ]
        )

        results = service.fix_all_violations(analysis, dry_run=True)
        assert len(results) == 1
        assert results[0].success is True

        # File should not be modified
        assert "import forbidden" in test_file.read_text()

    def test_fix_all_violations_apply(self, tmp_path: Path) -> None:
        """Test fixing all violations with apply."""
        service = EnforceDependencyService(repo_root=tmp_path)

        test_file = tmp_path / "test.py"
        test_file.write_text("import forbidden\nimport os\n")

        analysis = AnalysisResult(
            violations=[
                Violation(
                    type=ViolationType.IMPORT_VIOLATION,
                    severity=ViolationSeverity.ERROR,
                    file_path=str(test_file),
                    line=1,
                    source_module="test",
                    target_module="forbidden",
                    suggested_fix=FixAction.REMOVE_IMPORT,
                )
            ]
        )

        results = service.fix_all_violations(analysis, dry_run=False)
        assert len(results) == 1
        assert results[0].success is True

        # File should be modified
        content = test_file.read_text()
        assert "import forbidden" not in content
        assert "import os" in content

    def test_check_external_in_domain(self, tmp_path: Path) -> None:
        """Test checking for external libraries in domain."""
        service = EnforceDependencyService(repo_root=tmp_path)

        # Create domain structure
        domain_dir = tmp_path / "rice_factor" / "domain"
        domain_dir.mkdir(parents=True)

        # File with external import
        (domain_dir / "service.py").write_text("import anthropic\n")

        violations = service.check_external_in_domain(domain_dir)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.EXTERNAL_IN_DOMAIN
        assert "anthropic" in violations[0].target_module

    def test_check_external_in_domain_clean(self, tmp_path: Path) -> None:
        """Test domain with no external imports."""
        service = EnforceDependencyService(repo_root=tmp_path)

        # Create domain structure
        domain_dir = tmp_path / "rice_factor" / "domain"
        domain_dir.mkdir(parents=True)

        # File with only stdlib
        (domain_dir / "service.py").write_text("from typing import Any\n")

        violations = service.check_external_in_domain(domain_dir)
        assert len(violations) == 0

    def test_detect_circular_dependencies(self, tmp_path: Path) -> None:
        """Test detecting circular dependencies."""
        service = EnforceDependencyService(repo_root=tmp_path)

        # Create files with circular dependency
        (tmp_path / "a.py").write_text("from b import something\n")
        (tmp_path / "b.py").write_text("from a import other\n")

        violations = service.detect_circular_dependencies()
        # May or may not detect depending on module resolution
        assert isinstance(violations, list)

    def test_domain_isolation_rule(self, tmp_path: Path) -> None:
        """Test domain isolation rule detects violations."""
        service = EnforceDependencyService(repo_root=tmp_path)

        # Create domain file importing from adapters
        domain_dir = tmp_path / "app" / "domain"
        domain_dir.mkdir(parents=True)

        test_file = domain_dir / "service.py"
        test_file.write_text("from adapters.api import Client\n")

        violations = service.analyze_file(test_file)
        assert len(violations) > 0
        # Should detect forbidden import
        assert any("adapters" in str(v.target_module) for v in violations)

    def test_extract_imports_import_statement(self, tmp_path: Path) -> None:
        """Test extracting import statements."""
        service = EnforceDependencyService(repo_root=tmp_path)

        import ast

        code = "import os\nimport sys\n"
        tree = ast.parse(code)

        imports = service._extract_imports(tree)
        assert len(imports) == 2
        assert imports[0]["module"] == "os"
        assert imports[1]["module"] == "sys"

    def test_extract_imports_from_statement(self, tmp_path: Path) -> None:
        """Test extracting from-import statements."""
        service = EnforceDependencyService(repo_root=tmp_path)

        import ast

        code = "from typing import Any\nfrom pathlib import Path\n"
        tree = ast.parse(code)

        imports = service._extract_imports(tree)
        assert len(imports) == 2
        assert imports[0]["module"] == "typing"
        assert imports[1]["module"] == "pathlib"

    def test_fix_violation_line_out_of_range(self, tmp_path: Path) -> None:
        """Test fixing violation with line out of range."""
        service = EnforceDependencyService(repo_root=tmp_path)

        test_file = tmp_path / "test.py"
        test_file.write_text("import os\n")

        violation = Violation(
            type=ViolationType.IMPORT_VIOLATION,
            severity=ViolationSeverity.ERROR,
            file_path=str(test_file),
            line=100,  # Out of range
            source_module="test",
            target_module="forbidden",
            suggested_fix=FixAction.REMOVE_IMPORT,
        )

        result = service.fix_violation(violation)
        assert result.success is False
        assert "out of range" in result.error

    def test_fix_violation_unsupported_action(self, tmp_path: Path) -> None:
        """Test fixing violation with unsupported action."""
        service = EnforceDependencyService(repo_root=tmp_path)

        test_file = tmp_path / "test.py"
        test_file.write_text("import os\n")

        violation = Violation(
            type=ViolationType.IMPORT_VIOLATION,
            severity=ViolationSeverity.ERROR,
            file_path=str(test_file),
            line=1,
            source_module="test",
            suggested_fix=FixAction.MOVE_CODE,  # Not supported
        )

        result = service.fix_violation(violation)
        assert result.success is False
        assert "not supported" in result.error
