"""Unit tests for OverrideService."""

import json
from pathlib import Path
from uuid import UUID, uuid4

from rice_factor.domain.services.override_service import Override, OverrideService


class TestOverrideDataclass:
    """Tests for Override dataclass."""

    def test_create_with_required_fields(self) -> None:
        """Override should be creatable with required fields."""
        override = Override(
            id=uuid4(),
            target="phase",
            reason="Testing",
        )
        assert override.target == "phase"
        assert override.reason == "Testing"

    def test_default_context_is_empty_dict(self) -> None:
        """Default context should be empty dict."""
        override = Override(
            id=uuid4(),
            target="phase",
            reason="Testing",
        )
        assert override.context == {}

    def test_default_reconciled_is_false(self) -> None:
        """Default reconciled should be False."""
        override = Override(
            id=uuid4(),
            target="phase",
            reason="Testing",
        )
        assert override.reconciled is False

    def test_default_reconciled_at_is_none(self) -> None:
        """Default reconciled_at should be None."""
        override = Override(
            id=uuid4(),
            target="phase",
            reason="Testing",
        )
        assert override.reconciled_at is None

    def test_timestamp_is_set_automatically(self) -> None:
        """Timestamp should be set automatically."""
        override = Override(
            id=uuid4(),
            target="phase",
            reason="Testing",
        )
        assert override.timestamp is not None

    def test_context_can_be_provided(self) -> None:
        """Context can be provided explicitly."""
        override = Override(
            id=uuid4(),
            target="phase",
            reason="Testing",
            context={"command": "test"},
        )
        assert override.context == {"command": "test"}


class TestOverrideServiceInit:
    """Tests for OverrideService initialization."""

    def test_init_with_project_path(self, tmp_path: Path) -> None:
        """Service should initialize with project path."""
        service = OverrideService(project_path=tmp_path)
        assert service.project_path == tmp_path

    def test_overrides_file_path(self, tmp_path: Path) -> None:
        """Overrides file should be in audit directory."""
        service = OverrideService(project_path=tmp_path)
        assert service.overrides_file == tmp_path / "audit" / "overrides.json"

    def test_loads_empty_when_no_file(self, tmp_path: Path) -> None:
        """Service should start empty when no file exists."""
        service = OverrideService(project_path=tmp_path)
        assert service.get_all_overrides() == []


class TestOverrideServiceRecordOverride:
    """Tests for OverrideService.record_override()."""

    def test_record_override_returns_override(self, tmp_path: Path) -> None:
        """record_override should return Override object."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        assert isinstance(override, Override)

    def test_record_override_sets_target(self, tmp_path: Path) -> None:
        """record_override should set target."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        assert override.target == "phase"

    def test_record_override_sets_reason(self, tmp_path: Path) -> None:
        """record_override should set reason."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Emergency fix")
        assert override.reason == "Emergency fix"

    def test_record_override_sets_context(self, tmp_path: Path) -> None:
        """record_override should set context when provided."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(
            target="phase",
            reason="Testing",
            context={"command": "manual"},
        )
        assert override.context == {"command": "manual"}

    def test_record_override_generates_uuid(self, tmp_path: Path) -> None:
        """record_override should generate unique UUID."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        assert isinstance(override.id, UUID)

    def test_record_override_persists_to_file(self, tmp_path: Path) -> None:
        """record_override should persist to file."""
        service = OverrideService(project_path=tmp_path)
        service.record_override(target="phase", reason="Testing")
        assert service.overrides_file.exists()

    def test_record_override_creates_audit_dir(self, tmp_path: Path) -> None:
        """record_override should create audit directory."""
        service = OverrideService(project_path=tmp_path)
        service.record_override(target="phase", reason="Testing")
        assert (tmp_path / "audit").exists()


class TestOverrideServiceGetPendingOverrides:
    """Tests for OverrideService.get_pending_overrides()."""

    def test_returns_empty_when_no_overrides(self, tmp_path: Path) -> None:
        """get_pending_overrides should return empty list when none exist."""
        service = OverrideService(project_path=tmp_path)
        assert service.get_pending_overrides() == []

    def test_returns_unreconciled_overrides(self, tmp_path: Path) -> None:
        """get_pending_overrides should return unreconciled overrides."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        pending = service.get_pending_overrides()
        assert len(pending) == 1
        assert pending[0].id == override.id

    def test_excludes_reconciled_overrides(self, tmp_path: Path) -> None:
        """get_pending_overrides should exclude reconciled overrides."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        service.mark_reconciled(override.id)
        assert service.get_pending_overrides() == []


class TestOverrideServiceGetAllOverrides:
    """Tests for OverrideService.get_all_overrides()."""

    def test_returns_empty_when_no_overrides(self, tmp_path: Path) -> None:
        """get_all_overrides should return empty list when none exist."""
        service = OverrideService(project_path=tmp_path)
        assert service.get_all_overrides() == []

    def test_returns_all_overrides(self, tmp_path: Path) -> None:
        """get_all_overrides should return all overrides."""
        service = OverrideService(project_path=tmp_path)
        service.record_override(target="phase", reason="Testing 1")
        service.record_override(target="approval", reason="Testing 2")
        assert len(service.get_all_overrides()) == 2

    def test_includes_reconciled_overrides(self, tmp_path: Path) -> None:
        """get_all_overrides should include reconciled overrides."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        service.mark_reconciled(override.id)
        all_overrides = service.get_all_overrides()
        assert len(all_overrides) == 1
        assert all_overrides[0].reconciled is True


class TestOverrideServiceMarkReconciled:
    """Tests for OverrideService.mark_reconciled()."""

    def test_mark_reconciled_returns_true(self, tmp_path: Path) -> None:
        """mark_reconciled should return True when successful."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        result = service.mark_reconciled(override.id)
        assert result is True

    def test_mark_reconciled_sets_reconciled_flag(self, tmp_path: Path) -> None:
        """mark_reconciled should set reconciled flag."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        service.mark_reconciled(override.id)
        updated = service.get_override(override.id)
        assert updated is not None
        assert updated.reconciled is True

    def test_mark_reconciled_sets_reconciled_at(self, tmp_path: Path) -> None:
        """mark_reconciled should set reconciled_at timestamp."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        service.mark_reconciled(override.id)
        updated = service.get_override(override.id)
        assert updated is not None
        assert updated.reconciled_at is not None

    def test_mark_reconciled_returns_false_for_unknown_id(self, tmp_path: Path) -> None:
        """mark_reconciled should return False for unknown ID."""
        service = OverrideService(project_path=tmp_path)
        result = service.mark_reconciled(uuid4())
        assert result is False

    def test_mark_reconciled_persists_to_file(self, tmp_path: Path) -> None:
        """mark_reconciled should persist changes to file."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        service.mark_reconciled(override.id)

        # Reload from file
        service2 = OverrideService(project_path=tmp_path)
        updated = service2.get_override(override.id)
        assert updated is not None
        assert updated.reconciled is True


class TestOverrideServiceGetOverride:
    """Tests for OverrideService.get_override()."""

    def test_get_override_returns_override(self, tmp_path: Path) -> None:
        """get_override should return override by ID."""
        service = OverrideService(project_path=tmp_path)
        override = service.record_override(target="phase", reason="Testing")
        result = service.get_override(override.id)
        assert result is not None
        assert result.id == override.id

    def test_get_override_returns_none_for_unknown_id(self, tmp_path: Path) -> None:
        """get_override should return None for unknown ID."""
        service = OverrideService(project_path=tmp_path)
        result = service.get_override(uuid4())
        assert result is None


class TestOverrideServicePersistence:
    """Tests for OverrideService persistence."""

    def test_overrides_persist_across_instances(self, tmp_path: Path) -> None:
        """Overrides should persist across service instances."""
        service1 = OverrideService(project_path=tmp_path)
        override = service1.record_override(target="phase", reason="Testing")

        service2 = OverrideService(project_path=tmp_path)
        result = service2.get_override(override.id)
        assert result is not None
        assert result.target == "phase"
        assert result.reason == "Testing"

    def test_invalid_json_file_handled(self, tmp_path: Path) -> None:
        """Invalid JSON file should be handled gracefully."""
        audit_dir = tmp_path / "audit"
        audit_dir.mkdir(parents=True)
        (audit_dir / "overrides.json").write_text("invalid json")

        service = OverrideService(project_path=tmp_path)
        assert service.get_all_overrides() == []

    def test_json_file_format(self, tmp_path: Path) -> None:
        """JSON file should have correct format."""
        service = OverrideService(project_path=tmp_path)
        service.record_override(
            target="phase",
            reason="Testing",
            context={"key": "value"},
        )

        content = json.loads(service.overrides_file.read_text())
        assert "overrides" in content
        assert len(content["overrides"]) == 1
        override_data = content["overrides"][0]
        assert "id" in override_data
        assert override_data["target"] == "phase"
        assert override_data["reason"] == "Testing"
        assert override_data["context"] == {"key": "value"}
        assert "timestamp" in override_data
        assert "reconciled" in override_data


class TestOverrideServiceMultipleOverrides:
    """Tests for handling multiple overrides."""

    def test_multiple_overrides_have_unique_ids(self, tmp_path: Path) -> None:
        """Multiple overrides should have unique IDs."""
        service = OverrideService(project_path=tmp_path)
        o1 = service.record_override(target="phase", reason="Testing 1")
        o2 = service.record_override(target="approval", reason="Testing 2")
        assert o1.id != o2.id

    def test_pending_count_tracks_unreconciled(self, tmp_path: Path) -> None:
        """Pending count should track unreconciled overrides."""
        service = OverrideService(project_path=tmp_path)
        o1 = service.record_override(target="phase", reason="Testing 1")
        service.record_override(target="approval", reason="Testing 2")

        assert len(service.get_pending_overrides()) == 2

        service.mark_reconciled(o1.id)
        assert len(service.get_pending_overrides()) == 1

    def test_different_targets_stored_separately(self, tmp_path: Path) -> None:
        """Different targets should be stored correctly."""
        service = OverrideService(project_path=tmp_path)
        service.record_override(target="phase", reason="Phase override")
        service.record_override(target="approval", reason="Approval override")
        service.record_override(target="validation", reason="Validation override")

        all_overrides = service.get_all_overrides()
        targets = {o.target for o in all_overrides}
        assert targets == {"phase", "approval", "validation"}
