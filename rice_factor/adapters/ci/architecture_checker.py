"""Architecture rule checker for CI validation.

This module implements architecture rule validation that checks for
dependency violations in Python code based on ArchitecturePlan artifacts.
"""

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rice_factor.domain.artifacts.enums import ArtifactStatus
from rice_factor.domain.artifacts.payloads.architecture_plan import DependencyRule
from rice_factor.domain.ci.failure_codes import CIFailureCode
from rice_factor.domain.ci.models import CIFailure


@dataclass
class LayerMapping:
    """Maps layer names to directory patterns."""

    layer_name: str
    patterns: list[str]


# Default layer mappings for common architectures
DEFAULT_LAYER_MAPPINGS: dict[str, list[str]] = {
    "domain": ["domain/", "core/", "entities/", "models/"],
    "application": ["application/", "services/", "use_cases/", "usecases/"],
    "infrastructure": [
        "infrastructure/",
        "adapters/",
        "repositories/",
        "external/",
    ],
    "entrypoints": ["entrypoints/", "api/", "cli/", "web/", "handlers/"],
}

# Layer hierarchy for dependency rules (lower can't import higher)
LAYER_HIERARCHY = {
    "domain": 0,  # Innermost
    "application": 1,
    "infrastructure": 2,
    "entrypoints": 3,  # Outermost
}


class ArchitectureChecker:
    """Checks code for architecture rule violations.

    This checker verifies that imports in Python files comply with
    architectural dependency rules defined in ArchitecturePlan artifacts.
    """

    def __init__(
        self,
        layer_mappings: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize the architecture checker.

        Args:
            layer_mappings: Custom layer-to-pattern mappings. If None,
                uses default mappings.
        """
        self._layer_mappings = layer_mappings or DEFAULT_LAYER_MAPPINGS

    def check_violations(
        self,
        repo_root: Path,
        changed_files: set[str],
    ) -> list[CIFailure]:
        """Check changed files for architecture violations.

        Args:
            repo_root: Path to the repository root.
            changed_files: Set of changed file paths.

        Returns:
            List of CIFailure objects for any violations found.
        """
        failures: list[CIFailure] = []

        # Load architecture rules from artifacts
        rules = self._load_architecture_rules(repo_root)
        if not rules:
            # No architecture rules defined, skip check
            return failures

        # Check each changed Python file
        for file_path in changed_files:
            if not file_path.endswith(".py"):
                continue

            full_path = repo_root / file_path
            if not full_path.exists():
                continue

            file_failures = self._check_file(full_path, file_path, rules)
            failures.extend(file_failures)

        return failures

    def _load_architecture_rules(
        self,
        repo_root: Path,
    ) -> list[DependencyRule]:
        """Load architecture rules from artifacts.

        Args:
            repo_root: Path to the repository root.

        Returns:
            List of dependency rules to enforce.
        """
        rules: list[DependencyRule] = []
        artifacts_dir = repo_root / "artifacts" / "architecture_plans"

        if not artifacts_dir.exists():
            return rules

        for json_file in artifacts_dir.glob("*.json"):
            if json_file.name.endswith(".approval.json"):
                continue

            try:
                with json_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                # Only check approved/locked architecture plans
                status = data.get("status")
                if status not in (
                    ArtifactStatus.APPROVED.value,
                    ArtifactStatus.LOCKED.value,
                ):
                    continue

                payload = data.get("payload", {})
                for rule_data in payload.get("rules", []):
                    rule_value = rule_data.get("rule")
                    try:
                        rules.append(DependencyRule(rule_value))
                    except ValueError:
                        continue

            except (json.JSONDecodeError, OSError):
                continue

        return rules

    def _check_file(
        self,
        full_path: Path,
        relative_path: str,
        rules: list[DependencyRule],
    ) -> list[CIFailure]:
        """Check a single file for violations.

        Args:
            full_path: Absolute path to the file.
            relative_path: Relative path for error reporting.
            rules: Rules to check against.

        Returns:
            List of violations found.
        """
        failures: list[CIFailure] = []

        # Determine the layer of this file
        file_layer = self._get_layer(relative_path)
        if file_layer is None:
            # File not in a recognized layer
            return failures

        # Parse the file to extract imports
        try:
            with full_path.open("r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            return failures

        # Extract all imports
        imports = self._extract_imports(tree)

        # Check each import against rules
        for import_info in imports:
            import_layer = self._get_layer_from_import(import_info["module"])
            if import_layer is None:
                continue

            violation = self._check_import_violation(
                file_layer,
                import_layer,
                rules,
            )
            if violation:
                failures.append(
                    CIFailure(
                        code=CIFailureCode.ARCHITECTURE_VIOLATION,
                        message=(
                            f"Architecture violation in {relative_path}: "
                            f"{file_layer} imports from {import_layer}"
                        ),
                        file_path=Path(relative_path),
                        line_number=import_info["line"],
                        details={
                            "source_layer": file_layer,
                            "import_layer": import_layer,
                            "import_module": import_info["module"],
                            "rule_violated": violation.value,
                        },
                    )
                )

        return failures

    def _get_layer(self, file_path: str) -> str | None:
        """Determine which layer a file belongs to.

        Args:
            file_path: Relative file path.

        Returns:
            Layer name, or None if not in a recognized layer.
        """
        normalized = file_path.replace("\\", "/")

        for layer_name, patterns in self._layer_mappings.items():
            for pattern in patterns:
                if pattern in normalized:
                    return layer_name

        return None

    def _get_layer_from_import(self, module: str) -> str | None:
        """Determine which layer an imported module belongs to.

        Args:
            module: The imported module name.

        Returns:
            Layer name, or None if not in a recognized layer.
        """
        # Convert module to path-like format
        module_path = module.replace(".", "/")

        for layer_name, patterns in self._layer_mappings.items():
            for pattern in patterns:
                pattern_clean = pattern.rstrip("/")
                if pattern_clean in module_path:
                    return layer_name

        return None

    def _extract_imports(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract import information from an AST.

        Args:
            tree: The parsed AST.

        Returns:
            List of import info dicts with 'module' and 'line' keys.
        """
        imports: list[dict[str, Any]] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({"module": alias.name, "line": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append({"module": node.module, "line": node.lineno})

        return imports

    def _check_import_violation(
        self,
        source_layer: str,
        import_layer: str,
        rules: list[DependencyRule],
    ) -> DependencyRule | None:
        """Check if an import violates any rule.

        Args:
            source_layer: Layer of the file doing the import.
            import_layer: Layer being imported.
            rules: Rules to check.

        Returns:
            The violated rule, or None if no violation.
        """
        for rule in rules:
            if self._violates_rule(source_layer, import_layer, rule):
                return rule
        return None

    def _violates_rule(
        self,
        source_layer: str,
        import_layer: str,
        rule: DependencyRule,
    ) -> bool:
        """Check if an import violates a specific rule.

        Args:
            source_layer: Layer of the file doing the import.
            import_layer: Layer being imported.
            rule: Rule to check.

        Returns:
            True if the import violates the rule.
        """
        if rule == DependencyRule.DOMAIN_CANNOT_IMPORT_INFRASTRUCTURE:
            return source_layer == "domain" and import_layer in (
                "infrastructure",
                "adapters",
                "entrypoints",
            )

        if rule == DependencyRule.APPLICATION_DEPENDS_ON_DOMAIN:
            # Application must not import from infrastructure directly
            return source_layer == "application" and import_layer in (
                "infrastructure",
                "entrypoints",
            )

        if rule == DependencyRule.INFRASTRUCTURE_DEPENDS_ON_APPLICATION:
            # Infrastructure must not import from entrypoints
            return source_layer == "infrastructure" and import_layer == "entrypoints"

        return False
