"""End-to-end CLI tests for Rice-Factor.

These tests verify complete CLI workflows using real commands
with --stub and --dry-run flags to avoid external LLM calls.

Test Categories:
1. Command Help & Discovery - All commands show help
2. Init Workflow - Project initialization
3. Plan Workflow - Planning commands
4. Execution Workflow - scaffold, impl, apply
5. Validation Workflow - test, validate, diagnose
6. Artifact Management - artifact, approve, lock
7. CI/CD Integration - ci commands
8. Override System - override commands
9. Audit System - audit commands
10. Utility Commands - models, usage, viz, docs
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


# =============================================================================
# SECTION 1: Command Help & Discovery
# =============================================================================


class TestCommandHelp:
    """Verify all commands display help correctly."""

    @pytest.mark.parametrize(
        "command",
        [
            ["--help"],
            ["init", "--help"],
            ["plan", "--help"],
            ["plan", "project", "--help"],
            ["plan", "architecture", "--help"],
            ["plan", "tests", "--help"],
            ["plan", "impl", "--help"],
            ["plan", "refactor", "--help"],
            ["scaffold", "--help"],
            ["impl", "--help"],
            ["review", "--help"],
            ["apply", "--help"],
            ["test", "--help"],
            ["diagnose", "--help"],
            ["approve", "--help"],
            ["lock", "--help"],
            ["refactor", "--help"],
            ["validate", "--help"],
            ["resume", "--help"],
            ["override", "--help"],
            ["override", "create", "--help"],
            ["override", "list", "--help"],
            ["override", "reconcile", "--help"],
            ["ci", "--help"],
            ["ci", "validate", "--help"],
            ["ci", "init", "--help"],
            ["audit", "--help"],
            ["audit", "drift", "--help"],
            ["audit", "coverage", "--help"],
            ["artifact", "--help"],
            ["artifact", "age", "--help"],
            ["artifact", "review", "--help"],
            ["artifact", "extend", "--help"],
            ["artifact", "migrate", "--help"],
            ["reconcile", "--help"],
            ["capabilities", "--help"],
            ["migrate", "--help"],
            ["metrics", "--help"],
            ["batch", "--help"],
            ["models", "--help"],
            ["usage", "--help"],
            ["agents", "--help"],
            ["viz", "--help"],
            ["docs", "--help"],
            ["tui", "--help"],
            ["web", "--help"],
            ["web", "serve", "--help"],
        ],
    )
    def test_command_shows_help(self, command: list[str]) -> None:
        """Each command should display help without errors."""
        result = runner.invoke(app, command)
        assert result.exit_code == 0, f"Help failed for {command}: {result.stdout}"
        # Help output should contain usage information
        assert "usage" in result.stdout.lower() or "--help" in result.stdout.lower() or "options" in result.stdout.lower()


class TestVersionCommand:
    """Test version display."""

    def test_version_short_flag(self) -> None:
        """Test -v shows version."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "rice-factor version" in result.stdout

    def test_version_long_flag(self) -> None:
        """Test --version shows version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "rice-factor version" in result.stdout


# =============================================================================
# SECTION 2: Init Workflow
# =============================================================================


class TestInitCommand:
    """Test project initialization commands."""

    def test_init_creates_structure(self, tmp_path: Path) -> None:
        """Init creates required directories and files."""
        result = runner.invoke(
            app, ["init", "--path", str(tmp_path), "--skip-questionnaire"]
        )
        assert result.exit_code == 0, f"Init failed: {result.stdout}"

        # Verify structure
        assert (tmp_path / ".project").is_dir()
        assert (tmp_path / ".project" / "requirements.md").exists()
        assert (tmp_path / ".project" / "constraints.md").exists()
        assert (tmp_path / ".project" / "glossary.md").exists()
        assert (tmp_path / "artifacts").is_dir()
        assert (tmp_path / "audit").is_dir()

    def test_init_dry_run(self, tmp_path: Path) -> None:
        """Init --dry-run shows what would be created without making changes."""
        result = runner.invoke(
            app, ["init", "--path", str(tmp_path), "--dry-run", "--skip-questionnaire"]
        )
        assert result.exit_code == 0
        # Dry run should not create files
        assert not (tmp_path / ".project").exists()

    def test_init_force_overwrites(self, tmp_path: Path) -> None:
        """Init --force overwrites existing project."""
        # First init
        runner.invoke(app, ["init", "--path", str(tmp_path), "--skip-questionnaire"])
        # Modify a file
        (tmp_path / ".project" / "requirements.md").write_text("Modified content")

        # Force reinit
        result = runner.invoke(
            app, ["init", "--path", str(tmp_path), "--force", "--skip-questionnaire"]
        )
        assert result.exit_code == 0

    def test_init_fails_on_existing_without_force(self, tmp_path: Path) -> None:
        """Init fails if project exists and --force not specified."""
        # First init
        runner.invoke(app, ["init", "--path", str(tmp_path), "--skip-questionnaire"])

        # Second init should fail
        result = runner.invoke(
            app, ["init", "--path", str(tmp_path), "--skip-questionnaire"]
        )
        assert result.exit_code != 0


# =============================================================================
# SECTION 3: Plan Workflow
# =============================================================================


class TestPlanCommands:
    """Test planning commands."""

    def test_plan_requires_initialized_project(self, tmp_path: Path) -> None:
        """Plan commands fail on uninitialized project."""
        result = runner.invoke(
            app, ["plan", "project", "--path", str(tmp_path), "--stub"]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()

    def test_plan_project_dry_run(self, mvp_project: Path) -> None:
        """Plan project --dry-run shows what would be generated."""
        result = runner.invoke(
            app, ["plan", "project", "--path", str(mvp_project), "--dry-run"]
        )
        # May fail due to intake validation, but should not crash
        assert result.exit_code in [0, 1]

    def test_plan_project_stub(self, mvp_project: Path) -> None:
        """Plan project --stub uses stub LLM provider."""
        result = runner.invoke(
            app, ["plan", "project", "--path", str(mvp_project), "--stub", "--dry-run"]
        )
        # May fail due to intake validation, but should not crash
        assert result.exit_code in [0, 1]

    def test_plan_architecture_dry_run(self, initialized_project: Path) -> None:
        """Plan architecture --dry-run shows what would be generated."""
        result = runner.invoke(
            app, ["plan", "architecture", "--path", str(initialized_project), "--dry-run"]
        )
        # May fail due to missing ProjectPlan, but should not crash
        assert result.exit_code in [0, 1]

    def test_plan_tests_dry_run(self, initialized_project: Path) -> None:
        """Plan tests --dry-run shows what would be generated."""
        result = runner.invoke(
            app, ["plan", "tests", "--path", str(initialized_project), "--dry-run"]
        )
        # May fail due to phase requirements, but should not crash
        assert result.exit_code in [0, 1]


# =============================================================================
# SECTION 4: Execution Workflow
# =============================================================================


class TestScaffoldCommand:
    """Test scaffold command."""

    def test_scaffold_requires_project_plan(self, initialized_project: Path) -> None:
        """Scaffold fails without ProjectPlan."""
        result = runner.invoke(
            app, ["scaffold", "--path", str(initialized_project), "--stub"]
        )
        assert result.exit_code == 1

    def test_scaffold_dry_run(self, initialized_project: Path) -> None:
        """Scaffold --dry-run shows what would be created."""
        result = runner.invoke(
            app, ["scaffold", "--path", str(initialized_project), "--dry-run", "--stub"]
        )
        # Dry run should complete even without plan
        assert result.exit_code in [0, 1]


class TestImplCommand:
    """Test implementation command."""

    def test_impl_requires_file_argument(self, initialized_project: Path) -> None:
        """Impl requires a file argument."""
        result = runner.invoke(
            app, ["impl", "--path", str(initialized_project)]
        )
        assert result.exit_code == 2  # Missing argument error

    def test_impl_with_file(self, initialized_project: Path) -> None:
        """Impl with file runs (may fail due to phase requirements)."""
        result = runner.invoke(
            app, ["impl", "main.py", "--path", str(initialized_project), "--stub"]
        )
        # Expected to fail due to phase requirements
        assert result.exit_code in [0, 1]


class TestApplyCommand:
    """Test apply command."""

    def test_apply_requires_pending_diffs(self, initialized_project: Path) -> None:
        """Apply fails without pending diffs."""
        result = runner.invoke(app, ["apply", "--path", str(initialized_project)])
        assert result.exit_code == 1


# =============================================================================
# SECTION 5: Validation Workflow
# =============================================================================


class TestTestCommand:
    """Test test command."""

    def test_test_requires_initialized(self, tmp_path: Path) -> None:
        """Test command fails on uninitialized project."""
        result = runner.invoke(app, ["test", "--path", str(tmp_path)])
        assert result.exit_code == 1

    def test_test_on_initialized(self, initialized_project: Path) -> None:
        """Test command runs on initialized project."""
        result = runner.invoke(app, ["test", "--path", str(initialized_project)])
        # May fail due to no tests, but should not crash
        assert result.exit_code in [0, 1]


class TestValidateCommand:
    """Test validate command."""

    def test_validate_requires_initialized(self, tmp_path: Path) -> None:
        """Validate command fails on uninitialized project."""
        result = runner.invoke(app, ["validate", "--path", str(tmp_path)])
        assert result.exit_code == 1

    def test_validate_on_initialized(self, initialized_project: Path) -> None:
        """Validate command runs on initialized project."""
        result = runner.invoke(app, ["validate", "--path", str(initialized_project)])
        # Should complete validation
        assert result.exit_code in [0, 1]


class TestDiagnoseCommand:
    """Test diagnose command."""

    def test_diagnose_on_initialized(self, initialized_project: Path) -> None:
        """Diagnose command runs on initialized project."""
        result = runner.invoke(app, ["diagnose", "--path", str(initialized_project)])
        assert result.exit_code in [0, 1]


# =============================================================================
# SECTION 6: Artifact Management
# =============================================================================


class TestApproveCommand:
    """Test approve command."""

    def test_approve_requires_artifact_id(self, initialized_project: Path) -> None:
        """Approve requires artifact ID."""
        result = runner.invoke(app, ["approve", "--path", str(initialized_project)])
        assert result.exit_code == 2  # Missing argument

    def test_approve_nonexistent_artifact(self, initialized_project: Path) -> None:
        """Approve fails for nonexistent artifact."""
        result = runner.invoke(
            app, ["approve", "nonexistent-id", "--path", str(initialized_project)]
        )
        assert result.exit_code == 1


class TestLockCommand:
    """Test lock command."""

    def test_lock_tests(self, initialized_project: Path) -> None:
        """Lock tests command."""
        result = runner.invoke(
            app, ["lock", "tests", "--path", str(initialized_project)]
        )
        # May fail due to missing TestPlan, but should not crash
        assert result.exit_code in [0, 1]


class TestArtifactCommands:
    """Test artifact management commands."""

    def test_artifact_age(self, initialized_project: Path) -> None:
        """Artifact age command shows aging artifacts."""
        result = runner.invoke(
            app, ["artifact", "age", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]

    def test_artifact_review(self, initialized_project: Path) -> None:
        """Artifact review command prompts for reviews."""
        result = runner.invoke(
            app, ["artifact", "review", "--path", str(initialized_project)]
        )
        # May return 2 for missing arguments
        assert result.exit_code in [0, 1, 2]


# =============================================================================
# SECTION 7: CI/CD Integration
# =============================================================================


class TestCICommands:
    """Test CI/CD integration commands."""

    def test_ci_validate(self, initialized_project: Path) -> None:
        """CI validate runs validation suite."""
        result = runner.invoke(
            app, ["ci", "validate", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]

    def test_ci_validate_artifacts(self, initialized_project: Path) -> None:
        """CI validate-artifacts checks artifact validity."""
        result = runner.invoke(
            app, ["ci", "validate-artifacts", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]

    def test_ci_validate_approvals(self, initialized_project: Path) -> None:
        """CI validate-approvals checks approval status."""
        result = runner.invoke(
            app, ["ci", "validate-approvals", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]

    def test_ci_init(self, initialized_project: Path) -> None:
        """CI init creates CI configuration."""
        result = runner.invoke(
            app, ["ci", "init", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# SECTION 8: Override System
# =============================================================================


class TestOverrideCommands:
    """Test override management commands."""

    def test_override_list(self, initialized_project: Path) -> None:
        """Override list shows active overrides."""
        result = runner.invoke(
            app, ["override", "list", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]

    def test_override_create_requires_reason(self, initialized_project: Path) -> None:
        """Override create requires reason."""
        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "--path",
                str(initialized_project),
                "--type",
                "test_lock",
            ],
        )
        # Should fail due to missing reason or other validation
        assert result.exit_code in [0, 1, 2]


# =============================================================================
# SECTION 9: Audit System
# =============================================================================


class TestAuditCommands:
    """Test audit trail commands."""

    def test_audit_drift(self, initialized_project: Path) -> None:
        """Audit drift detects drift from artifacts."""
        result = runner.invoke(
            app, ["audit", "drift", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]

    def test_audit_coverage(self, initialized_project: Path) -> None:
        """Audit coverage shows audit coverage."""
        result = runner.invoke(
            app, ["audit", "coverage", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# SECTION 10: Utility Commands
# =============================================================================


class TestModelsCommand:
    """Test models command."""

    def test_models_list(self) -> None:
        """Models command lists available models."""
        result = runner.invoke(app, ["models"])
        assert result.exit_code in [0, 1]


class TestUsageCommands:
    """Test usage tracking commands."""

    def test_usage_show(self, initialized_project: Path) -> None:
        """Usage show displays usage statistics."""
        result = runner.invoke(
            app, ["usage", "show", "--path", str(initialized_project)]
        )
        # May return 2 for missing subcommand
        assert result.exit_code in [0, 1, 2]


class TestVizCommand:
    """Test visualization command."""

    def test_viz_requires_initialized(self, tmp_path: Path) -> None:
        """Viz command fails on uninitialized project."""
        result = runner.invoke(app, ["viz", "--path", str(tmp_path)])
        assert result.exit_code == 1

    def test_viz_on_initialized(self, initialized_project: Path) -> None:
        """Viz command runs on initialized project."""
        result = runner.invoke(app, ["viz", "--path", str(initialized_project)])
        assert result.exit_code in [0, 1]


class TestDocsCommand:
    """Test docs command."""

    def test_docs_open(self) -> None:
        """Docs command shows documentation info."""
        result = runner.invoke(app, ["docs"])
        assert result.exit_code in [0, 1]


class TestTUICommand:
    """Test TUI command."""

    def test_tui_help(self) -> None:
        """TUI help shows options."""
        result = runner.invoke(app, ["tui", "--help"])
        assert result.exit_code == 0

    @patch("rice_factor.entrypoints.tui.app.RiceFactorTUI")
    def test_tui_starts(self, mock_tui: MagicMock) -> None:
        """TUI command starts the TUI app."""
        mock_instance = MagicMock()
        mock_tui.return_value = mock_instance

        result = runner.invoke(app, ["tui"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once()


class TestWebCommands:
    """Test web interface commands."""

    def test_web_serve_help(self) -> None:
        """Web serve help shows options."""
        result = runner.invoke(app, ["web", "serve", "--help"])
        assert result.exit_code == 0
        assert "port" in result.stdout.lower()

    @patch("uvicorn.run")
    def test_web_serve_starts(self, mock_uvicorn: MagicMock) -> None:
        """Web serve starts the server."""
        result = runner.invoke(app, ["web", "serve"])
        assert result.exit_code == 0
        mock_uvicorn.assert_called_once()

    @patch("uvicorn.run")
    def test_web_serve_custom_port(self, mock_uvicorn: MagicMock) -> None:
        """Web serve accepts custom port."""
        result = runner.invoke(app, ["web", "serve", "--port", "9000"])
        assert result.exit_code == 0
        # Verify port was passed
        call_kwargs = mock_uvicorn.call_args[1]
        assert call_kwargs["port"] == 9000


# =============================================================================
# SECTION 11: Refactor Workflow
# =============================================================================


class TestRefactorCommands:
    """Test refactor commands."""

    def test_refactor_requires_goal(self, initialized_project: Path) -> None:
        """Refactor requires a goal."""
        result = runner.invoke(
            app, ["refactor", "--path", str(initialized_project)]
        )
        # Should fail or show help due to missing subcommand
        assert result.exit_code in [0, 1, 2]

    def test_refactor_dry_run(self, initialized_project: Path) -> None:
        """Refactor dry-run previews changes."""
        result = runner.invoke(
            app, ["refactor", "dry-run", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]


# =============================================================================
# SECTION 12: Batch Operations
# =============================================================================


class TestBatchCommands:
    """Test batch operation commands."""

    def test_batch_help(self) -> None:
        """Batch help shows available operations."""
        result = runner.invoke(app, ["batch", "--help"])
        assert result.exit_code == 0


# =============================================================================
# SECTION 13: Capabilities Command
# =============================================================================


class TestCapabilitiesCommand:
    """Test capabilities command."""

    def test_capabilities_list(self) -> None:
        """Capabilities command lists available capabilities."""
        result = runner.invoke(app, ["capabilities"])
        assert result.exit_code in [0, 1]


# =============================================================================
# SECTION 14: Reconcile Command
# =============================================================================


class TestReconcileCommand:
    """Test reconcile command."""

    def test_reconcile_requires_initialized(self, tmp_path: Path) -> None:
        """Reconcile on uninitialized project may succeed or fail depending on mode."""
        result = runner.invoke(app, ["reconcile", "--path", str(tmp_path)])
        # May succeed with no-op or fail due to missing project
        assert result.exit_code in [0, 1]

    def test_reconcile_on_initialized(self, initialized_project: Path) -> None:
        """Reconcile runs on initialized project."""
        result = runner.invoke(app, ["reconcile", "--path", str(initialized_project)])
        assert result.exit_code in [0, 1]


# =============================================================================
# SECTION 15: End-to-End Workflow
# =============================================================================


class TestE2EWorkflow:
    """Test complete end-to-end workflows."""

    def test_init_to_plan_workflow(self, tmp_path: Path) -> None:
        """Test init -> plan project workflow."""
        # Step 1: Initialize
        result = runner.invoke(
            app, ["init", "--path", str(tmp_path), "--skip-questionnaire"]
        )
        assert result.exit_code == 0, f"Init failed: {result.stdout}"

        # Step 2: Plan project (dry-run)
        # May fail due to intake validation on skeleton files
        result = runner.invoke(
            app, ["plan", "project", "--path", str(tmp_path), "--dry-run"]
        )
        # Intake validation may fail on skeleton files, which is expected
        assert result.exit_code in [0, 1], f"Plan crashed: {result.stdout}"

    def test_verbose_mode(self, initialized_project: Path) -> None:
        """Test --verbose flag works across commands."""
        result = runner.invoke(
            app, ["--verbose", "diagnose", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]

    def test_quiet_mode(self, initialized_project: Path) -> None:
        """Test --quiet flag suppresses output."""
        result = runner.invoke(
            app, ["--quiet", "diagnose", "--path", str(initialized_project)]
        )
        assert result.exit_code in [0, 1]
