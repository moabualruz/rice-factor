"""Unit tests for reconcile command."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from rice_factor.domain.artifacts.payloads.reconciliation_plan import (
    ReconciliationAction,
    ReconciliationStep,
)
from rice_factor.domain.artifacts.payloads import ReconciliationPlanPayload
from rice_factor.domain.drift.models import (
    DriftReport,
    DriftSeverity,
    DriftSignal,
    DriftSignalType,
)
from rice_factor.entrypoints.cli.main import app

runner = CliRunner()


class TestReconcileCommandHelp:
    """Tests for reconcile command help."""

    def test_help_shows_description(self) -> None:
        """--help should show command description."""
        result = runner.invoke(app, ["reconcile", "--help"])
        assert result.exit_code == 0
        assert "reconciliation" in result.stdout.lower()

    def test_help_shows_options(self) -> None:
        """--help should show all options."""
        result = runner.invoke(app, ["reconcile", "--help"])
        assert result.exit_code == 0
        assert "--path" in result.stdout
        assert "--code-dir" in result.stdout
        assert "--threshold" in result.stdout
        assert "--no-freeze" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--json" in result.stdout


class TestReconcileNoDrift:
    """Tests for reconcile when no drift detected."""

    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_no_drift_exits_successfully(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """reconcile should exit 0 when no drift detected."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[],
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["reconcile", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "no drift" in result.stdout.lower() or "no reconciliation" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_no_drift_json_output(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """reconcile --json should output status when no drift."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[],
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["reconcile", "--path", str(tmp_path), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "no_drift"


class TestReconcileBelowThreshold:
    """Tests for reconcile when drift below threshold."""

    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_below_threshold_shows_warning(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """reconcile should warn when drift below threshold."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.LOW,
                    path="src/orphan.py",
                    description="Orphan code",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["reconcile", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "below" in result.stdout.lower() or "threshold" in result.stdout.lower()

    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_below_threshold_json_output(
        self, mock_detector_class: MagicMock, tmp_path: Path
    ) -> None:
        """reconcile --json should output status when below threshold."""
        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=[
                DriftSignal(
                    signal_type=DriftSignalType.ORPHAN_CODE,
                    severity=DriftSeverity.LOW,
                    path="src/orphan.py",
                    description="Orphan code",
                    detected_at=datetime.now(),
                )
            ],
            threshold=3,
        )
        mock_detector_class.return_value = mock_detector

        (tmp_path / "src").mkdir()

        result = runner.invoke(app, ["reconcile", "--path", str(tmp_path), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "below_threshold"


class TestReconcileGeneratesPlan:
    """Tests for reconcile when plan is generated."""

    @patch("rice_factor.entrypoints.cli.commands.reconcile.FilesystemStorageAdapter")
    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_generates_plan_when_threshold_exceeded(
        self,
        mock_detector_class: MagicMock,
        mock_storage_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """reconcile should generate plan when threshold exceeded."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.MEDIUM,
                path=f"src/orphan{i}.py",
                description="Orphan code",
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

        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        (tmp_path / "src").mkdir()
        (tmp_path / "artifacts").mkdir()

        result = runner.invoke(app, ["reconcile", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert "saved" in result.stdout.lower() or "plan" in result.stdout.lower()
        mock_storage.save.assert_called_once()

    @patch("rice_factor.entrypoints.cli.commands.reconcile.FilesystemStorageAdapter")
    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_dry_run_does_not_save(
        self,
        mock_detector_class: MagicMock,
        mock_storage_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """reconcile --dry-run should not save the plan."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_PLAN,
                severity=DriftSeverity.CRITICAL,
                path="artifacts/stale.json",
                description="Stale plan",
                detected_at=datetime.now(),
            )
        ]

        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=signals,
            threshold=1,
        )
        mock_detector_class.return_value = mock_detector

        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        (tmp_path / "src").mkdir()
        (tmp_path / "artifacts").mkdir()

        result = runner.invoke(app, ["reconcile", "--path", str(tmp_path), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout
        mock_storage.save.assert_not_called()

    @patch("rice_factor.entrypoints.cli.commands.reconcile.FilesystemStorageAdapter")
    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_json_output_includes_steps(
        self,
        mock_detector_class: MagicMock,
        mock_storage_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """reconcile --json should include plan steps."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.HIGH,
                path="src/orphan.py",
                description="Orphan code",
                detected_at=datetime.now(),
            )
        ]

        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=signals,
            threshold=1,
        )
        mock_detector_class.return_value = mock_detector

        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        (tmp_path / "src").mkdir()
        (tmp_path / "artifacts").mkdir()

        result = runner.invoke(app, ["reconcile", "--path", str(tmp_path), "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "plan_generated"
        assert "steps" in data
        assert len(data["steps"]) == 1

    @patch("rice_factor.entrypoints.cli.commands.reconcile.FilesystemStorageAdapter")
    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_no_freeze_option_works(
        self,
        mock_detector_class: MagicMock,
        mock_storage_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """reconcile --no-freeze should set freeze_new_work=False."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.CRITICAL,
                path="src/orphan.py",
                description="Orphan code",
                detected_at=datetime.now(),
            )
        ]

        mock_detector = MagicMock()
        mock_detector.full_analysis.return_value = DriftReport(
            signals=signals,
            threshold=1,
        )
        mock_detector_class.return_value = mock_detector

        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        (tmp_path / "src").mkdir()
        (tmp_path / "artifacts").mkdir()

        result = runner.invoke(
            app, ["reconcile", "--path", str(tmp_path), "--json", "--no-freeze"]
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["freeze_new_work"] is False


class TestReconcileThresholdOption:
    """Tests for reconcile --threshold option."""

    @patch("rice_factor.entrypoints.cli.commands.reconcile.FilesystemStorageAdapter")
    @patch("rice_factor.entrypoints.cli.commands.reconcile.DriftDetectorAdapter")
    def test_threshold_option_overrides_default(
        self,
        mock_detector_class: MagicMock,
        mock_storage_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """reconcile --threshold should override default threshold."""
        signals = [
            DriftSignal(
                signal_type=DriftSignalType.ORPHAN_CODE,
                severity=DriftSeverity.LOW,
                path="src/orphan.py",
                description="Orphan code",
                detected_at=datetime.now(),
            )
        ]

        mock_detector = MagicMock()
        # The DriftDetectorAdapter receives threshold from config,
        # so the returned report will have threshold=1 when --threshold 1 is passed
        mock_detector.full_analysis.return_value = DriftReport(
            signals=signals,
            threshold=1,  # Matches the --threshold argument
        )
        mock_detector_class.return_value = mock_detector

        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        (tmp_path / "src").mkdir()
        (tmp_path / "artifacts").mkdir()

        # With threshold=1, one signal should trigger reconciliation (1 >= 1)
        result = runner.invoke(
            app, ["reconcile", "--path", str(tmp_path), "--threshold", "1", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "plan_generated"
