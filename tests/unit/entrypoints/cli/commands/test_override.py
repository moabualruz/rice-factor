"""Unit tests for override command."""

from pathlib import Path

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestOverrideHelp:
    """Tests for override command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["override", "--help"])
        assert result.exit_code == 0
        assert "override" in result.stdout.lower()

    def test_help_shows_subcommands(self) -> None:
        """--help should show available subcommands."""
        result = runner.invoke(app, ["override", "--help"])
        assert result.exit_code == 0
        assert "create" in result.stdout.lower()
        assert "list" in result.stdout.lower()
        assert "reconcile" in result.stdout.lower()


class TestOverrideCreateHelp:
    """Tests for override create help."""

    def test_create_help_shows_description(self) -> None:
        """--help should show create description."""
        result = runner.invoke(app, ["override", "create", "--help"])
        assert result.exit_code == 0
        assert "override" in result.stdout.lower()

    def test_create_help_shows_reason_option(self) -> None:
        """--help should show --reason option."""
        result = runner.invoke(app, ["override", "create", "--help"])
        assert result.exit_code == 0
        assert "--reason" in result.stdout

    def test_create_help_shows_yes_option(self) -> None:
        """--help should show --yes option."""
        result = runner.invoke(app, ["override", "create", "--help"])
        assert result.exit_code == 0
        assert "--yes" in result.stdout


class TestOverrideCreateRequiresInit:
    """Tests for override create phase requirements."""

    def test_override_create_requires_init(self, tmp_path: Path) -> None:
        """override create should fail if project not initialized."""
        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestOverrideCreateValidation:
    """Tests for override create input validation."""

    def test_invalid_target_fails(self, tmp_path: Path) -> None:
        """Invalid target should fail with error."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "invalid_target",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 1
        assert "invalid" in result.stdout.lower()

    def test_phase_target_valid(self, tmp_path: Path) -> None:
        """phase target should be valid."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0

    def test_approval_target_valid(self, tmp_path: Path) -> None:
        """approval target should be valid."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "approval",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0

    def test_validation_target_valid(self, tmp_path: Path) -> None:
        """validation target should be valid."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "validation",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0


class TestOverrideCreateWarning:
    """Tests for override create warning display."""

    def test_shows_warning_panel(self, tmp_path: Path) -> None:
        """override create should show warning panel."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing override",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "warning" in result.stdout.lower()

    def test_shows_target_in_warning(self, tmp_path: Path) -> None:
        """Warning should show target."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "phase" in result.stdout.lower()

    def test_shows_reason_in_warning(self, tmp_path: Path) -> None:
        """Warning should show reason."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "My custom reason",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "My custom reason" in result.stdout


class TestOverrideCreateSuccess:
    """Tests for successful override creation."""

    def test_shows_success_message(self, tmp_path: Path) -> None:
        """Successful override should show success message."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "override recorded" in result.stdout.lower()

    def test_shows_override_id(self, tmp_path: Path) -> None:
        """Success message should include override ID."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        # ID is shown (UUID format, at least 8 characters)
        assert "recorded:" in result.stdout.lower()

    def test_saves_override_file(self, tmp_path: Path) -> None:
        """Override should be saved to file."""
        (tmp_path / ".project").mkdir()

        runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )

        overrides_file = tmp_path / "audit" / "overrides.json"
        assert overrides_file.exists()


class TestOverrideCreateConfirmation:
    """Tests for override confirmation prompt."""

    def test_cancels_without_yes_and_wrong_input(self, tmp_path: Path) -> None:
        """Should cancel when confirmation is wrong."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing",
                "--path",
                str(tmp_path),
            ],
            input="wrong\n",
        )
        # Cancelled, no error exit
        assert "cancelled" in result.stdout.lower()

    def test_proceeds_with_override_confirmation(self, tmp_path: Path) -> None:
        """Should proceed when OVERRIDE is typed."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Testing",
                "--path",
                str(tmp_path),
            ],
            input="OVERRIDE\n",
        )
        assert result.exit_code == 0
        assert "override recorded" in result.stdout.lower()


class TestOverrideListHelp:
    """Tests for override list help."""

    def test_list_help_shows_description(self) -> None:
        """--help should show list description."""
        result = runner.invoke(app, ["override", "list", "--help"])
        assert result.exit_code == 0
        assert "pending" in result.stdout.lower() or "list" in result.stdout.lower()

    def test_list_help_shows_all_option(self) -> None:
        """--help should show --all option."""
        result = runner.invoke(app, ["override", "list", "--help"])
        assert result.exit_code == 0
        assert "--all" in result.stdout


class TestOverrideListRequiresInit:
    """Tests for override list phase requirements."""

    def test_list_requires_init(self, tmp_path: Path) -> None:
        """override list should fail if project not initialized."""
        result = runner.invoke(
            app, ["override", "list", "--path", str(tmp_path)]
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestOverrideListEmpty:
    """Tests for override list when empty."""

    def test_shows_no_pending_when_empty(self, tmp_path: Path) -> None:
        """Should show no pending overrides message."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["override", "list", "--path", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "no pending" in result.stdout.lower()

    def test_all_shows_no_overrides_when_empty(self, tmp_path: Path) -> None:
        """--all should show no overrides message."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app, ["override", "list", "--all", "--path", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "no overrides" in result.stdout.lower()


class TestOverrideListWithOverrides:
    """Tests for override list with existing overrides."""

    def test_shows_pending_overrides(self, tmp_path: Path) -> None:
        """Should show pending overrides in table."""
        (tmp_path / ".project").mkdir()

        # Create an override
        runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Test override",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )

        result = runner.invoke(
            app, ["override", "list", "--path", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "phase" in result.stdout.lower()
        assert "pending" in result.stdout.lower()

    def test_shows_override_count(self, tmp_path: Path) -> None:
        """Should show count of pending overrides."""
        (tmp_path / ".project").mkdir()

        # Create overrides
        runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Test 1",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        runner.invoke(
            app,
            [
                "override",
                "create",
                "approval",
                "--reason",
                "Test 2",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )

        result = runner.invoke(
            app, ["override", "list", "--path", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "2" in result.stdout


class TestOverrideReconcileHelp:
    """Tests for override reconcile help."""

    def test_reconcile_help_shows_description(self) -> None:
        """--help should show reconcile description."""
        result = runner.invoke(app, ["override", "reconcile", "--help"])
        assert result.exit_code == 0
        assert "reconcile" in result.stdout.lower()


class TestOverrideReconcileRequiresInit:
    """Tests for override reconcile phase requirements."""

    def test_reconcile_requires_init(self, tmp_path: Path) -> None:
        """override reconcile should fail if project not initialized."""
        result = runner.invoke(
            app,
            ["override", "reconcile", "abc123", "--path", str(tmp_path)],
        )
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestOverrideReconcileNotFound:
    """Tests for override reconcile when not found."""

    def test_fails_for_unknown_id(self, tmp_path: Path) -> None:
        """Should fail when override not found."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(
            app,
            ["override", "reconcile", "unknown", "--path", str(tmp_path)],
        )
        assert result.exit_code == 1
        assert "no override found" in result.stdout.lower()


class TestOverrideReconcileSuccess:
    """Tests for successful override reconciliation."""

    def test_reconciles_override(self, tmp_path: Path) -> None:
        """Should successfully reconcile override."""
        (tmp_path / ".project").mkdir()

        # Create an override
        create_result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Test",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        # Extract partial ID from output (first 8 chars)
        # Output format: "✓ Override recorded: <uuid>"
        lines = create_result.stdout.split("\n")
        id_line = next(line for line in lines if "recorded:" in line.lower())
        # Get the ID part after "recorded:"
        override_id = id_line.split(":")[-1].strip()[:8]

        result = runner.invoke(
            app,
            ["override", "reconcile", override_id, "--path", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "reconciled" in result.stdout.lower()

    def test_already_reconciled_shows_message(self, tmp_path: Path) -> None:
        """Should show message for already reconciled override."""
        (tmp_path / ".project").mkdir()

        # Create and reconcile
        create_result = runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Test",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )
        lines = create_result.stdout.split("\n")
        id_line = next(line for line in lines if "recorded:" in line.lower())
        override_id = id_line.split(":")[-1].strip()[:8]

        # Reconcile first time
        runner.invoke(
            app,
            ["override", "reconcile", override_id, "--path", str(tmp_path)],
        )

        # Try to reconcile again
        result = runner.invoke(
            app,
            ["override", "reconcile", override_id, "--path", str(tmp_path)],
        )
        assert "already reconciled" in result.stdout.lower()


class TestOverrideReconcileAmbiguous:
    """Tests for ambiguous override ID."""

    def test_fails_for_short_nonmatching_id(self, tmp_path: Path) -> None:
        """Should fail when no overrides match partial ID."""
        (tmp_path / ".project").mkdir()

        # Create an override
        runner.invoke(
            app,
            [
                "override",
                "create",
                "phase",
                "--reason",
                "Test",
                "--yes",
                "--path",
                str(tmp_path),
            ],
        )

        # Use an ID that won't match (zzz prefix unlikely)
        result = runner.invoke(
            app,
            ["override", "reconcile", "zzz", "--path", str(tmp_path)],
        )
        # No match
        assert result.exit_code == 1
        assert "no override found" in result.stdout.lower()
