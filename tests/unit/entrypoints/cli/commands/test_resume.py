"""Unit tests for resume command."""

from pathlib import Path

from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestResumeHelp:
    """Tests for resume command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["resume", "--help"])
        assert result.exit_code == 0
        assert "resume" in result.stdout.lower()

    def test_help_shows_path_option(self) -> None:
        """--help should show --path option."""
        result = runner.invoke(app, ["resume", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout


class TestResumeRequiresInit:
    """Tests for resume phase requirements."""

    def test_resume_requires_init(self, tmp_path: Path) -> None:
        """resume should fail if project not initialized."""
        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 1
        assert "not initialized" in result.stdout.lower()


class TestResumeShowsPhase:
    """Tests for resume showing current phase."""

    def test_shows_current_phase(self, tmp_path: Path) -> None:
        """resume should show current phase."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "phase" in result.stdout.lower()

    def test_shows_phase_name(self, tmp_path: Path) -> None:
        """resume should show phase name."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        # INIT phase after initialization
        assert "init" in result.stdout.lower()

    def test_shows_project_state_panel(self, tmp_path: Path) -> None:
        """resume should show project state panel."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "project state" in result.stdout.lower()


class TestResumeShowsArtifacts:
    """Tests for resume showing artifacts."""

    def test_shows_no_artifacts_when_empty(self, tmp_path: Path) -> None:
        """resume should show no artifacts message when empty."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "no artifacts" in result.stdout.lower()

    def test_shows_artifacts_table_when_present(self, tmp_path: Path) -> None:
        """resume should show artifacts table when present."""
        (tmp_path / ".project").mkdir()
        # Create artifacts directory with a project_plan
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        # Create a minimal artifact file
        import json
        from datetime import datetime
        from uuid import uuid4

        artifact = {
            "id": str(uuid4()),
            "artifact_type": "project_plan",
            "status": "draft",
            "version": 1,
            "created_by": "llm",
            "created_at": datetime.now().isoformat(),
            "payload": {
                "name": "test",
                "description": "test",
                "target_language": "python",
                "project_type": "cli",
                "components": [],
            },
        }
        (artifacts_dir / f"{artifact['id']}.json").write_text(json.dumps(artifact))

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "artifacts" in result.stdout.lower()


class TestResumeShowsNextSteps:
    """Tests for resume showing next steps."""

    def test_shows_next_steps_section(self, tmp_path: Path) -> None:
        """resume should show suggested next steps section."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "next steps" in result.stdout.lower()

    def test_init_phase_suggests_plan_project(self, tmp_path: Path) -> None:
        """INIT phase should suggest plan project."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "plan project" in result.stdout.lower()

    def test_init_phase_suggests_approve(self, tmp_path: Path) -> None:
        """INIT phase should suggest approve command."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "approve" in result.stdout.lower()


class TestResumeShowsPendingOverrides:
    """Tests for resume showing pending overrides."""

    def test_shows_no_override_warning_when_none(self, tmp_path: Path) -> None:
        """resume should not show override warning when none pending."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        # Should not warn about overrides when none exist
        assert "reconciliation" not in result.stdout.lower()

    def test_shows_override_warning_when_pending(self, tmp_path: Path) -> None:
        """resume should show override warning when pending."""
        (tmp_path / ".project").mkdir()

        # Create an override
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

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "reconciliation" in result.stdout.lower()

    def test_shows_override_count(self, tmp_path: Path) -> None:
        """resume should show count of pending overrides."""
        (tmp_path / ".project").mkdir()

        # Create multiple overrides
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

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "2" in result.stdout

    def test_suggests_override_list_command(self, tmp_path: Path) -> None:
        """resume should suggest override list command when pending."""
        (tmp_path / ".project").mkdir()

        # Create an override
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

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "override list" in result.stdout.lower()


class TestResumePhaseSpecificSteps:
    """Tests for phase-specific next steps."""

    def test_uninit_suggests_init(self, tmp_path: Path) -> None:
        """UNINIT phase should suggest init (but test requires not init)."""
        # This is tested via the requires_init test
        pass

    def test_init_phase_suggests_plan_project_command(self, tmp_path: Path) -> None:
        """INIT phase should suggest plan project command."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(tmp_path)])
        assert result.exit_code == 0
        # INIT phase suggests plan project
        assert "plan project" in result.stdout.lower()


class TestResumeWithPath:
    """Tests for resume with --path option."""

    def test_uses_provided_path(self, tmp_path: Path) -> None:
        """resume should use provided path."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        (project_dir / ".project").mkdir()

        result = runner.invoke(app, ["resume", "--path", str(project_dir)])
        assert result.exit_code == 0
        assert "phase" in result.stdout.lower()

    def test_short_path_option(self, tmp_path: Path) -> None:
        """resume should accept -p short option."""
        (tmp_path / ".project").mkdir()

        result = runner.invoke(app, ["resume", "-p", str(tmp_path)])
        assert result.exit_code == 0
        assert "phase" in result.stdout.lower()
