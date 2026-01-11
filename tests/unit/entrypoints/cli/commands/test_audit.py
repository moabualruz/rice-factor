"""Unit tests for audit commands."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest
from typer.testing import CliRunner

from rice_factor.domain.drift.models import (
    DriftConfig,
    DriftReport,
    DriftSeverity,
    DriftSignal,
    DriftSignalType,
)
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestAuditCommandHelp:
    """Tests for audit command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "Audit" in result.stdout or "drift" in result.stdout

    def test_help_shows_drift_command(self) -> None:
        """--help should list drift command."""
        result = runner.invoke(app, ["audit", "--help"])
        assert result.exit_code == 0
        assert "drift" in result.stdout


class TestAuditDriftCommand:
    """Tests for audit drift command."""

    def test_drift_help_shows_options(self) -> None:
        """drift --help should show options."""
        result = runner.invoke(app, ["audit", "drift", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout
        assert "--code-dir" in result.stdout
        assert "--threshold" in result.stdout
        assert "--json" in result.stdout

    def test_drift_help_shows_exit_codes(self) -> None:
        """drift --help should document exit codes."""
        result = runner.invoke(app, ["audit", "drift", "--help"])
        assert result.exit_code == 0
        assert "Exit codes" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_runs_without_error(self, mock_detector_class: MagicMock, tmp_path: Path) -> None:
        """drift should run without error on empty project."""
        # Setup mock
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[],
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        # Create minimal project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "artifacts").mkdir()

        result = runner.invoke(app, ["audit", "drift", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "No drift detected" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_json_output(self, mock_detector_class: MagicMock, tmp_path: Path) -> None:
        """drift --json should output valid JSON."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[],
            threshold=3,
            code_files_scanned=10,
            artifacts_checked=5,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["audit", "drift", "--path", str(tmp_path), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "signals" in data
        assert "threshold" in data
        assert data["code_files_scanned"] == 10

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_exit_code_1_when_drift_below_threshold(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """drift should exit 1 when drift detected but below threshold."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.LOW,
                    path="src/orphan.py",
                    description="Orphan code file",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["audit", "drift", "--path", str(tmp_path)])

        assert result.exit_code == 1
        assert "Drift detected" in result.stdout or "below threshold" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_exit_code_2_when_threshold_exceeded(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """drift should exit 2 when threshold exceeded."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.MEDIUM,
                path=f"src/orphan{i}.py",
                description="Orphan code file",
                detected_at=datetime.now(),
            )
            for i in range(5)
        ]
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=signals,
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["audit", "drift", "--path", str(tmp_path)])

        assert result.exit_code == 2
        assert "RECONCILIATION" in result.stdout.upper()

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_exit_code_2_on_critical_signal(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """drift should exit 2 when critical signal present."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_PLAN,
                    severity=DriftSeverity.CRITICAL,
                    path="artifacts/impl/stale.json",
                    description="Plan targets missing file",
                    detected_at=datetime.now(),
                )
            ],
            threshold=10,  # High threshold, but critical should trigger
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["audit", "drift", "--path", str(tmp_path)])

        assert result.exit_code == 2

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_threshold_option(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """drift --threshold should override default threshold."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.LOW,
                    path="src/orphan.py",
                    description="Orphan code file",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        # With threshold=5, one signal should be below
        result = runner.invoke(app, ["audit", "drift", "--path", str(tmp_path), "--threshold", "5"])

        # threshold=5, signals=1, so exit 1 (below threshold)
        assert result.exit_code == 1

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_code_dir_option(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """drift --code-dir should use specified directory."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(signals=[], threshold=3)
        mock_detector_class.return_value = mock_detector

        (tmp_path / "lib").mkdir()

        result = runner.invoke(
            app, ["audit", "drift", "--path", str(tmp_path), "--code-dir", "lib"]
        )

        assert result.exit_code == 0
        # Verify the detector was created with the correct config (lib source dir)
        mock_detector_class.assert_called_once()
        call_kwargs = mock_detector_class.call_args.kwargs
        assert "lib" in call_kwargs["config"].source_dirs

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_displays_signals_grouped_by_type(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """drift should group signals by type in output."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.LOW,
                    path="src/orphan.py",
                    description="Orphan code file",
                    detected_at=datetime.now(),
                ),
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_PLAN,
                    severity=DriftSeverity.MEDIUM,
                    path="artifacts/impl/stale.json",
                    description="Plan targets missing file",
                    detected_at=datetime.now(),
                ),
            ],
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["audit", "drift", "--path", str(tmp_path)])

        assert result.exit_code == 1
        # Should show both signal types
        assert "Orphan Code" in result.stdout
        assert "Orphan Plan" in result.stdout

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_drift_shows_summary(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """drift should show summary with counts."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[],
            threshold=3,
            code_files_scanned=42,
            artifacts_checked=10,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["audit", "drift", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "42" in result.stdout  # code files scanned
        assert "10" in result.stdout  # artifacts checked


class TestAuditFindProjectRoot:
    """Tests for project root detection in audit commands."""

    @patch("rice_factor.entrypoints.cli.commands.audit.DriftDetectorAdapter")
    def test_finds_project_root_from_subdirectory(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """Should find .project/ in parent directory."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(signals=[], threshold=3)
        mock_detector_class.return_value = mock_detector

        # Create project structure
        (tmp_path / ".project").mkdir()
        (tmp_path / "src").mkdir()
        subdir = tmp_path / "src" / "module"
        subdir.mkdir()

        # Run from subdirectory
        result = runner.invoke(app, ["audit", "drift", "--path", str(subdir)])

        # Should find project root and pass
        assert result.exit_code == 0
