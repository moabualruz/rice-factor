"""Unit tests for DiffService."""

from pathlib import Path
from uuid import uuid4

from rice_factor.domain.services.diff_service import (
    Diff,
    DiffService,
    DiffStatus,
)


class TestDiffServiceInit:
    """Tests for DiffService initialization."""

    def test_can_instantiate(self, tmp_path: Path) -> None:
        """DiffService should be instantiable."""
        service = DiffService(project_root=tmp_path)
        assert service is not None

    def test_project_root_property(self, tmp_path: Path) -> None:
        """DiffService should expose project_root property."""
        service = DiffService(project_root=tmp_path)
        assert service.project_root == tmp_path

    def test_diffs_dir_property(self, tmp_path: Path) -> None:
        """DiffService should expose diffs_dir property."""
        service = DiffService(project_root=tmp_path)
        assert service.diffs_dir == tmp_path / "audit" / "diffs"


class TestGenerateDiff:
    """Tests for generate_diff method."""

    def test_returns_diff(self, tmp_path: Path) -> None:
        """generate_diff should return a Diff object."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        assert isinstance(diff, Diff)

    def test_sets_target_file(self, tmp_path: Path) -> None:
        """generate_diff should set target_file."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("src/utils.py")
        assert diff.target_file == "src/utils.py"

    def test_sets_pending_status(self, tmp_path: Path) -> None:
        """generate_diff should set status to PENDING."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        assert diff.status == DiffStatus.PENDING

    def test_generates_content(self, tmp_path: Path) -> None:
        """generate_diff should generate diff content."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        assert diff.content
        assert "main.py" in diff.content

    def test_sets_plan_id(self, tmp_path: Path) -> None:
        """generate_diff should set plan_id if provided."""
        service = DiffService(project_root=tmp_path)
        plan_id = uuid4()
        diff = service.generate_diff("main.py", plan_id=plan_id)
        assert diff.plan_id == plan_id


class TestSaveDiff:
    """Tests for save_diff method."""

    def test_creates_file(self, tmp_path: Path) -> None:
        """save_diff should create a file."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        diff_path = service.save_diff(diff)
        assert diff_path.exists()

    def test_returns_path(self, tmp_path: Path) -> None:
        """save_diff should return the file path."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        diff_path = service.save_diff(diff)
        assert diff_path.is_file()
        assert diff_path.suffix == ".diff"

    def test_creates_diffs_directory(self, tmp_path: Path) -> None:
        """save_diff should create the diffs directory."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)
        assert service.diffs_dir.exists()

    def test_updates_index(self, tmp_path: Path) -> None:
        """save_diff should update the index file."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)
        index_path = service.diffs_dir / "_index.json"
        assert index_path.exists()


class TestLoadPendingDiff:
    """Tests for load_pending_diff method."""

    def test_returns_none_when_empty(self, tmp_path: Path) -> None:
        """load_pending_diff should return None when no diffs."""
        service = DiffService(project_root=tmp_path)
        assert service.load_pending_diff() is None

    def test_returns_pending_diff(self, tmp_path: Path) -> None:
        """load_pending_diff should return the pending diff."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)

        loaded = service.load_pending_diff()
        assert loaded is not None
        assert loaded.id == diff.id

    def test_returns_most_recent(self, tmp_path: Path) -> None:
        """load_pending_diff should return most recent pending diff."""
        service = DiffService(project_root=tmp_path)
        diff1 = service.generate_diff("a.py")
        service.save_diff(diff1)
        diff2 = service.generate_diff("b.py")
        service.save_diff(diff2)

        loaded = service.load_pending_diff()
        assert loaded is not None
        assert loaded.id == diff2.id

    def test_skips_approved(self, tmp_path: Path) -> None:
        """load_pending_diff should skip approved diffs."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)
        service.approve_diff(diff.id)

        assert service.load_pending_diff() is None


class TestLoadDiff:
    """Tests for load_diff method."""

    def test_returns_none_for_unknown(self, tmp_path: Path) -> None:
        """load_diff should return None for unknown ID."""
        service = DiffService(project_root=tmp_path)
        assert service.load_diff(uuid4()) is None

    def test_returns_diff_by_id(self, tmp_path: Path) -> None:
        """load_diff should return the diff by ID."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)

        loaded = service.load_diff(diff.id)
        assert loaded is not None
        assert loaded.id == diff.id
        assert loaded.target_file == "main.py"


class TestApproveDiff:
    """Tests for approve_diff method."""

    def test_approves_diff(self, tmp_path: Path) -> None:
        """approve_diff should set status to APPROVED."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)

        result = service.approve_diff(diff.id)
        assert result is True

        loaded = service.load_diff(diff.id)
        assert loaded is not None
        assert loaded.status == DiffStatus.APPROVED

    def test_returns_false_for_unknown(self, tmp_path: Path) -> None:
        """approve_diff should return False for unknown ID."""
        service = DiffService(project_root=tmp_path)
        assert service.approve_diff(uuid4()) is False


class TestRejectDiff:
    """Tests for reject_diff method."""

    def test_rejects_diff(self, tmp_path: Path) -> None:
        """reject_diff should set status to REJECTED."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)

        result = service.reject_diff(diff.id)
        assert result is True

        loaded = service.load_diff(diff.id)
        assert loaded is not None
        assert loaded.status == DiffStatus.REJECTED

    def test_returns_false_for_unknown(self, tmp_path: Path) -> None:
        """reject_diff should return False for unknown ID."""
        service = DiffService(project_root=tmp_path)
        assert service.reject_diff(uuid4()) is False


class TestMarkApplied:
    """Tests for mark_applied method."""

    def test_marks_applied(self, tmp_path: Path) -> None:
        """mark_applied should set status to APPLIED."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)

        result = service.mark_applied(diff.id)
        assert result is True

        loaded = service.load_diff(diff.id)
        assert loaded is not None
        assert loaded.status == DiffStatus.APPLIED


class TestGetDiffStatus:
    """Tests for get_diff_status method."""

    def test_returns_status(self, tmp_path: Path) -> None:
        """get_diff_status should return the status."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)

        status = service.get_diff_status(diff.id)
        assert status == DiffStatus.PENDING

    def test_returns_none_for_unknown(self, tmp_path: Path) -> None:
        """get_diff_status should return None for unknown ID."""
        service = DiffService(project_root=tmp_path)
        assert service.get_diff_status(uuid4()) is None


class TestLoadApprovedDiff:
    """Tests for load_approved_diff method."""

    def test_returns_none_when_empty(self, tmp_path: Path) -> None:
        """load_approved_diff should return None when no approved diffs."""
        service = DiffService(project_root=tmp_path)
        assert service.load_approved_diff() is None

    def test_returns_approved_diff(self, tmp_path: Path) -> None:
        """load_approved_diff should return the approved diff."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)
        service.approve_diff(diff.id)

        loaded = service.load_approved_diff()
        assert loaded is not None
        assert loaded.id == diff.id
        assert loaded.status == DiffStatus.APPROVED

    def test_skips_pending(self, tmp_path: Path) -> None:
        """load_approved_diff should skip pending diffs."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        service.save_diff(diff)

        assert service.load_approved_diff() is None


class TestListDiffs:
    """Tests for list_diffs method."""

    def test_returns_empty_list(self, tmp_path: Path) -> None:
        """list_diffs should return empty list when no diffs."""
        service = DiffService(project_root=tmp_path)
        assert service.list_diffs() == []

    def test_returns_all_diffs(self, tmp_path: Path) -> None:
        """list_diffs should return all diffs."""
        service = DiffService(project_root=tmp_path)
        diff1 = service.generate_diff("a.py")
        service.save_diff(diff1)
        diff2 = service.generate_diff("b.py")
        service.save_diff(diff2)

        diffs = service.list_diffs()
        assert len(diffs) == 2

    def test_filters_by_status(self, tmp_path: Path) -> None:
        """list_diffs should filter by status."""
        service = DiffService(project_root=tmp_path)
        diff1 = service.generate_diff("a.py")
        service.save_diff(diff1)
        diff2 = service.generate_diff("b.py")
        service.save_diff(diff2)
        service.approve_diff(diff2.id)

        pending = service.list_diffs(status=DiffStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].id == diff1.id

        approved = service.list_diffs(status=DiffStatus.APPROVED)
        assert len(approved) == 1
        assert approved[0].id == diff2.id


class TestDiffDataclass:
    """Tests for Diff dataclass."""

    def test_to_dict(self, tmp_path: Path) -> None:
        """to_dict should serialize correctly."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        data = diff.to_dict()
        assert data["target_file"] == "main.py"
        assert data["status"] == "pending"

    def test_from_dict(self, tmp_path: Path) -> None:
        """from_dict should deserialize correctly."""
        service = DiffService(project_root=tmp_path)
        diff = service.generate_diff("main.py")
        data = diff.to_dict()

        loaded = Diff.from_dict(data)
        assert loaded.id == diff.id
        assert loaded.target_file == diff.target_file
