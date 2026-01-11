"""Unit tests for ArchitectureChecker."""

import json
from pathlib import Path

import pytest

from rice_factor.adapters.ci.architecture_checker import (
    ArchitectureChecker,
    DEFAULT_LAYER_MAPPINGS,
)
from rice_factor.domain.artifacts.payloads.architecture_plan import DependencyRule
from rice_factor.domain.ci.failure_codes import CIFailureCode


class TestLayerDetection:
    """Tests for layer detection logic."""

    def test_detects_domain_layer(self) -> None:
        """Should detect domain layer from path."""
        checker = ArchitectureChecker()
        assert checker._get_layer("src/domain/models.py") == "domain"

    def test_detects_infrastructure_layer(self) -> None:
        """Should detect infrastructure layer from path."""
        checker = ArchitectureChecker()
        assert checker._get_layer("src/adapters/database.py") == "infrastructure"

    def test_detects_application_layer(self) -> None:
        """Should detect application layer from path."""
        checker = ArchitectureChecker()
        assert checker._get_layer("src/services/user_service.py") == "application"

    def test_detects_entrypoints_layer(self) -> None:
        """Should detect entrypoints layer from path."""
        checker = ArchitectureChecker()
        assert checker._get_layer("src/cli/main.py") == "entrypoints"

    def test_returns_none_for_unknown_path(self) -> None:
        """Should return None for paths not in any layer."""
        checker = ArchitectureChecker()
        assert checker._get_layer("setup.py") is None

    def test_custom_layer_mappings(self) -> None:
        """Should use custom layer mappings."""
        custom_mappings = {
            "core": ["core/", "kernel/"],
            "shell": ["shell/", "ui/"],
        }
        checker = ArchitectureChecker(layer_mappings=custom_mappings)
        assert checker._get_layer("src/core/logic.py") == "core"
        assert checker._get_layer("src/shell/presenter.py") == "shell"


class TestImportLayerDetection:
    """Tests for determining import layer."""

    def test_detects_domain_import(self) -> None:
        """Should detect domain layer from import."""
        checker = ArchitectureChecker()
        assert checker._get_layer_from_import("myapp.domain.models") == "domain"

    def test_detects_infrastructure_import(self) -> None:
        """Should detect infrastructure from adapters import."""
        checker = ArchitectureChecker()
        assert checker._get_layer_from_import("myapp.adapters.db") == "infrastructure"

    def test_returns_none_for_external_import(self) -> None:
        """Should return None for external library imports."""
        checker = ArchitectureChecker()
        assert checker._get_layer_from_import("pydantic") is None


class TestRuleViolation:
    """Tests for rule violation checking."""

    def test_domain_importing_infrastructure_violates(self) -> None:
        """Domain importing infrastructure should violate rule."""
        checker = ArchitectureChecker()
        result = checker._violates_rule(
            source_layer="domain",
            import_layer="infrastructure",
            rule=DependencyRule.DOMAIN_CANNOT_IMPORT_INFRASTRUCTURE,
        )
        assert result is True

    def test_domain_importing_domain_allowed(self) -> None:
        """Domain importing domain should not violate rule."""
        checker = ArchitectureChecker()
        result = checker._violates_rule(
            source_layer="domain",
            import_layer="domain",
            rule=DependencyRule.DOMAIN_CANNOT_IMPORT_INFRASTRUCTURE,
        )
        assert result is False

    def test_application_importing_domain_allowed(self) -> None:
        """Application importing domain should be allowed."""
        checker = ArchitectureChecker()
        result = checker._violates_rule(
            source_layer="application",
            import_layer="domain",
            rule=DependencyRule.APPLICATION_DEPENDS_ON_DOMAIN,
        )
        assert result is False

    def test_application_importing_infrastructure_violates(self) -> None:
        """Application importing infrastructure should violate rule."""
        checker = ArchitectureChecker()
        result = checker._violates_rule(
            source_layer="application",
            import_layer="infrastructure",
            rule=DependencyRule.APPLICATION_DEPENDS_ON_DOMAIN,
        )
        assert result is True

    def test_infrastructure_importing_entrypoints_violates(self) -> None:
        """Infrastructure importing entrypoints should violate rule."""
        checker = ArchitectureChecker()
        result = checker._violates_rule(
            source_layer="infrastructure",
            import_layer="entrypoints",
            rule=DependencyRule.INFRASTRUCTURE_DEPENDS_ON_APPLICATION,
        )
        assert result is True


class TestCheckViolations:
    """Tests for full violation checking."""

    def test_no_violations_without_architecture_plan(
        self, tmp_path: Path
    ) -> None:
        """Should return no violations if no ArchitecturePlan exists."""
        checker = ArchitectureChecker()
        failures = checker.check_violations(tmp_path, {"src/domain/model.py"})
        assert failures == []

    def test_no_violations_with_empty_rules(self, tmp_path: Path) -> None:
        """Should return no violations if architecture plan has no rules."""
        # Create artifacts directory
        arch_dir = tmp_path / "artifacts" / "architecture_plans"
        arch_dir.mkdir(parents=True)

        # Create architecture plan with empty rules
        arch_plan = {
            "artifact_type": "ArchitecturePlan",
            "status": "approved",
            "payload": {
                "layers": ["domain", "application", "infrastructure"],
                "rules": [],
            },
        }
        (arch_dir / "arch-001.json").write_text(json.dumps(arch_plan))

        checker = ArchitectureChecker()
        failures = checker.check_violations(tmp_path, {"src/domain/model.py"})
        assert failures == []

    def test_detects_violation_in_python_file(self, tmp_path: Path) -> None:
        """Should detect architecture violation in Python file."""
        # Create artifacts directory with architecture plan
        arch_dir = tmp_path / "artifacts" / "architecture_plans"
        arch_dir.mkdir(parents=True)

        arch_plan = {
            "artifact_type": "ArchitecturePlan",
            "status": "approved",
            "payload": {
                "layers": ["domain", "infrastructure"],
                "rules": [
                    {"rule": "domain_cannot_import_infrastructure"}
                ],
            },
        }
        (arch_dir / "arch-001.json").write_text(json.dumps(arch_plan))

        # Create domain file that imports from adapters
        domain_dir = tmp_path / "src" / "domain"
        domain_dir.mkdir(parents=True)
        domain_file = domain_dir / "model.py"
        domain_file.write_text(
            "from myapp.adapters.database import Repository\n"
            "\n"
            "class User:\n"
            "    pass\n"
        )

        checker = ArchitectureChecker()
        failures = checker.check_violations(
            tmp_path,
            {"src/domain/model.py"},
        )

        assert len(failures) == 1
        assert failures[0].code == CIFailureCode.ARCHITECTURE_VIOLATION
        assert "domain" in failures[0].message
        assert "infrastructure" in failures[0].message

    def test_skips_non_python_files(self, tmp_path: Path) -> None:
        """Should skip non-Python files."""
        arch_dir = tmp_path / "artifacts" / "architecture_plans"
        arch_dir.mkdir(parents=True)

        arch_plan = {
            "artifact_type": "ArchitecturePlan",
            "status": "approved",
            "payload": {
                "layers": ["domain"],
                "rules": [
                    {"rule": "domain_cannot_import_infrastructure"}
                ],
            },
        }
        (arch_dir / "arch-001.json").write_text(json.dumps(arch_plan))

        checker = ArchitectureChecker()
        failures = checker.check_violations(tmp_path, {"README.md", "setup.cfg"})
        assert failures == []

    def test_skips_draft_architecture_plans(self, tmp_path: Path) -> None:
        """Should skip draft architecture plans."""
        arch_dir = tmp_path / "artifacts" / "architecture_plans"
        arch_dir.mkdir(parents=True)

        arch_plan = {
            "artifact_type": "ArchitecturePlan",
            "status": "draft",  # Not approved
            "payload": {
                "layers": ["domain"],
                "rules": [
                    {"rule": "domain_cannot_import_infrastructure"}
                ],
            },
        }
        (arch_dir / "arch-001.json").write_text(json.dumps(arch_plan))

        # Create violating file
        domain_dir = tmp_path / "src" / "domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "model.py").write_text(
            "from myapp.adapters.db import Repo\n"
        )

        checker = ArchitectureChecker()
        failures = checker.check_violations(tmp_path, {"src/domain/model.py"})
        # No failures because plan is draft
        assert failures == []

    def test_includes_line_number_in_failure(self, tmp_path: Path) -> None:
        """Should include line number in violation failure."""
        arch_dir = tmp_path / "artifacts" / "architecture_plans"
        arch_dir.mkdir(parents=True)

        arch_plan = {
            "artifact_type": "ArchitecturePlan",
            "status": "locked",
            "payload": {
                "layers": ["domain", "infrastructure"],
                "rules": [
                    {"rule": "domain_cannot_import_infrastructure"}
                ],
            },
        }
        (arch_dir / "arch-001.json").write_text(json.dumps(arch_plan))

        domain_dir = tmp_path / "src" / "domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "model.py").write_text(
            "# Comment\n"
            "# Another comment\n"
            "from myapp.adapters.database import Repo\n"  # Line 3
        )

        checker = ArchitectureChecker()
        failures = checker.check_violations(tmp_path, {"src/domain/model.py"})

        assert len(failures) == 1
        assert failures[0].line_number == 3


class TestImportExtraction:
    """Tests for import extraction from AST."""

    def test_extracts_import_statement(self) -> None:
        """Should extract regular import statements."""
        import ast
        checker = ArchitectureChecker()

        source = "import myapp.domain.models"
        tree = ast.parse(source)
        imports = checker._extract_imports(tree)

        assert len(imports) == 1
        assert imports[0]["module"] == "myapp.domain.models"
        assert imports[0]["line"] == 1

    def test_extracts_from_import_statement(self) -> None:
        """Should extract from-import statements."""
        import ast
        checker = ArchitectureChecker()

        source = "from myapp.adapters import database"
        tree = ast.parse(source)
        imports = checker._extract_imports(tree)

        assert len(imports) == 1
        assert imports[0]["module"] == "myapp.adapters"

    def test_extracts_multiple_imports(self) -> None:
        """Should extract all import statements."""
        import ast
        checker = ArchitectureChecker()

        source = """
import os
import myapp.domain.models
from myapp.adapters import repo
from typing import List
"""
        tree = ast.parse(source)
        imports = checker._extract_imports(tree)

        assert len(imports) == 4
