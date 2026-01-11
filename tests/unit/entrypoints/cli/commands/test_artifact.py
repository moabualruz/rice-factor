"""Unit tests for artifact commands."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestArtifactCommandHelp:
    """Tests for artifact command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["artifact", "--help"])
        assert result.exit_code == 0
        assert "lifecycle" in result.stdout.lower()

    def test_help_shows_age_command(self) -> None:
        """--help should list age command."""
        result = runner.invoke(app, ["artifact", "--help"])
        assert result.exit_code == 0
        assert "age" in result.stdout

    def test_help_shows_extend_command(self) -> None:
        """--help should list extend command."""
        result = runner.invoke(app, ["artifact", "--help"])
        assert result.exit_code == 0
        assert "extend" in result.stdout

    def test_help_shows_review_command(self) -> None:
        """--help should list review command."""
        result = runner.invoke(app, ["artifact", "--help"])
        assert result.exit_code == 0
        assert "review" in result.stdout


class TestArtifactAgeCommand:
    """Tests for artifact age command."""

    def test_age_help_shows_options(self) -> None:
        """age --help should show options."""
        result = runner.invoke(app, ["artifact", "age", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout
        assert "--type" in result.stdout
        assert "--json" in result.stdout

    def test_age_help_shows_exit_codes(self) -> None:
        """age --help should document exit codes."""
        result = runner.invoke(app, ["artifact", "age", "--help"])
        assert result.exit_code == 0
        assert "Exit codes" in result.stdout

    def test_age_no_artifacts_dir(self, tmp_path: Path) -> None:
        """age should handle missing artifacts directory."""
        # No artifacts dir
        result = runner.invoke(app, ["artifact", "age", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "No artifacts" in result.stdout

    def test_age_empty_artifacts(self, tmp_path: Path) -> None:
        """age should handle empty artifacts directory."""
        (tmp_path / "artifacts").mkdir()

        result = runner.invoke(app, ["artifact", "age", "--path", str(tmp_path)])
        assert result.exit_code == 0

    def test_age_shows_artifacts(self, tmp_path: Path) -> None:
        """age should list artifacts with ages."""
        # Create artifacts directory structure
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        # Create a test artifact
        artifact = {
            "id": "test-artifact-001",
            "artifact_type": "ProjectPlan",
            "status": "draft",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
            "payload": {},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact))

        result = runner.invoke(app, ["artifact", "age", "--path", str(tmp_path)])

        assert "ProjectPlan" in result.stdout
        assert "test-artifact" in result.stdout

    def test_age_json_output(self, tmp_path: Path) -> None:
        """age --json should output valid JSON."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact = {
            "id": "json-test-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact))

        result = runner.invoke(app, ["artifact", "age", "--path", str(tmp_path), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "artifacts" in data
        assert "summary" in data
        assert len(data["artifacts"]) == 1

    def test_age_exit_code_1_when_review_needed(self, tmp_path: Path) -> None:
        """age should exit 1 when artifacts need review (3+ months old)."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact = {
            "id": "old-artifact-001",
            "artifact_type": "ProjectPlan",
            "status": "draft",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat(),
            "payload": {},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact))

        result = runner.invoke(app, ["artifact", "age", "--path", str(tmp_path)])

        assert result.exit_code == 1

    def test_age_exit_code_2_when_overdue(self, tmp_path: Path) -> None:
        """age should exit 2 when artifacts are overdue (6+ months old)."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact = {
            "id": "very-old-001",
            "artifact_type": "ProjectPlan",
            "status": "draft",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat(),
            "payload": {},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact))

        result = runner.invoke(app, ["artifact", "age", "--path", str(tmp_path)])

        assert result.exit_code == 2

    def test_age_type_filter(self, tmp_path: Path) -> None:
        """age --type should filter by artifact type."""
        artifacts_dir = tmp_path / "artifacts"
        (artifacts_dir / "project_plans").mkdir(parents=True)
        (artifacts_dir / "test_plans").mkdir(parents=True)

        project = {
            "id": "project-001",
            "artifact_type": "ProjectPlan",
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        test = {
            "id": "test-001",
            "artifact_type": "TestPlan",
            "status": "locked",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        (artifacts_dir / "project_plans" / "p.json").write_text(json.dumps(project))
        (artifacts_dir / "test_plans" / "t.json").write_text(json.dumps(test))

        result = runner.invoke(
            app, ["artifact", "age", "--path", str(tmp_path), "--type", "ProjectPlan", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data["artifacts"]) == 1
        assert data["artifacts"][0]["artifact_type"] == "ProjectPlan"


class TestArtifactExtendCommand:
    """Tests for artifact extend command."""

    def test_extend_help_shows_options(self) -> None:
        """extend --help should show options."""
        result = runner.invoke(app, ["artifact", "extend", "--help"])
        assert result.exit_code == 0
        assert "--reason" in result.stdout
        assert "--months" in result.stdout
        assert "ARTIFACT_ID" in result.stdout

    def test_extend_requires_reason(self, tmp_path: Path) -> None:
        """extend should require --reason flag."""
        result = runner.invoke(
            app, ["artifact", "extend", "some-id", "--path", str(tmp_path)]
        )
        # Should fail due to missing required option
        assert result.exit_code != 0

    def test_extend_artifact_not_found(self, tmp_path: Path) -> None:
        """extend should error when artifact not found."""
        (tmp_path / "artifacts").mkdir()

        result = runner.invoke(
            app,
            [
                "artifact",
                "extend",
                "nonexistent",
                "--reason",
                "Testing",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_extend_cannot_extend_locked(self, tmp_path: Path) -> None:
        """extend should reject LOCKED artifacts."""
        artifacts_dir = tmp_path / "artifacts" / "test_plans"
        artifacts_dir.mkdir(parents=True)

        artifact = {
            "id": "locked-001",
            "artifact_type": "TestPlan",
            "status": "locked",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact))

        result = runner.invoke(
            app,
            [
                "artifact",
                "extend",
                "locked-001",
                "--reason",
                "Test extension",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 1
        assert "LOCKED" in result.stdout

    def test_extend_updates_artifact(self, tmp_path: Path) -> None:
        """extend should update last_reviewed_at and review_notes."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact_path = artifacts_dir / "test.json"
        artifact = {
            "id": "extend-test-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        artifact_path.write_text(json.dumps(artifact))

        result = runner.invoke(
            app,
            [
                "artifact",
                "extend",
                "extend-test-001",
                "--reason",
                "Still accurate",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "extended" in result.stdout.lower()

        # Verify the file was updated
        updated = json.loads(artifact_path.read_text())
        assert updated.get("last_reviewed_at") is not None
        assert "Still accurate" in updated.get("review_notes", "")

    def test_extend_with_months_option(self, tmp_path: Path) -> None:
        """extend --months should use specified period."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact = {
            "id": "months-test-001",
            "artifact_type": "ProjectPlan",
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact))

        result = runner.invoke(
            app,
            [
                "artifact",
                "extend",
                "months-test-001",
                "--reason",
                "Extended test",
                "--months",
                "6",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "6 months" in result.stdout


class TestArtifactReviewCommand:
    """Tests for artifact review command."""

    def test_review_help_shows_options(self) -> None:
        """review --help should show options."""
        result = runner.invoke(app, ["artifact", "review", "--help"])
        assert result.exit_code == 0
        assert "--notes" in result.stdout
        assert "ARTIFACT_ID" in result.stdout

    def test_review_artifact_not_found(self, tmp_path: Path) -> None:
        """review should error when artifact not found."""
        (tmp_path / "artifacts").mkdir()

        result = runner.invoke(
            app,
            [
                "artifact",
                "review",
                "nonexistent",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_review_cannot_review_locked(self, tmp_path: Path) -> None:
        """review should reject LOCKED artifacts."""
        artifacts_dir = tmp_path / "artifacts" / "test_plans"
        artifacts_dir.mkdir(parents=True)

        artifact = {
            "id": "locked-001",
            "artifact_type": "TestPlan",
            "status": "locked",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        (artifacts_dir / "test.json").write_text(json.dumps(artifact))

        result = runner.invoke(
            app,
            [
                "artifact",
                "review",
                "locked-001",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 1
        assert "LOCKED" in result.stdout or "immutable" in result.stdout.lower()

    def test_review_updates_timestamp(self, tmp_path: Path) -> None:
        """review should update last_reviewed_at timestamp."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact_path = artifacts_dir / "test.json"
        artifact = {
            "id": "review-test-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        artifact_path.write_text(json.dumps(artifact))

        result = runner.invoke(
            app,
            [
                "artifact",
                "review",
                "review-test-001",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "reviewed" in result.stdout.lower()

        # Verify the file was updated
        updated = json.loads(artifact_path.read_text())
        assert updated.get("last_reviewed_at") is not None
        assert updated.get("updated_at") is not None

    def test_review_with_notes(self, tmp_path: Path) -> None:
        """review --notes should save review notes."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        artifact_path = artifacts_dir / "test.json"
        artifact = {
            "id": "notes-test-001",
            "artifact_type": "ProjectPlan",
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": {},
        }
        artifact_path.write_text(json.dumps(artifact))

        result = runner.invoke(
            app,
            [
                "artifact",
                "review",
                "notes-test-001",
                "--notes",
                "Looks good, no changes needed",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "Looks good" in result.stdout

        # Verify the notes were saved
        updated = json.loads(artifact_path.read_text())
        assert "Looks good" in updated.get("review_notes", "")

    def test_review_resets_age_timer(self, tmp_path: Path) -> None:
        """review should reset the age timer by updating last_reviewed_at."""
        artifacts_dir = tmp_path / "artifacts" / "project_plans"
        artifacts_dir.mkdir(parents=True)

        # Create an old artifact
        old_date = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        artifact_path = artifacts_dir / "test.json"
        artifact = {
            "id": "timer-test-001",
            "artifact_type": "ProjectPlan",
            "status": "approved",
            "created_at": old_date,
            "payload": {},
        }
        artifact_path.write_text(json.dumps(artifact))

        result = runner.invoke(
            app,
            [
                "artifact",
                "review",
                "timer-test-001",
                "--path",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "timer reset" in result.stdout.lower() or "reviewed" in result.stdout.lower()
