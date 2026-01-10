"""Unit tests for ApprovalsTracker."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.domain.artifacts.approval import Approval


class TestApprovalsTracker:
    """Tests for ApprovalsTracker class."""

    def test_init_creates_empty_approvals(self, tmp_path: Path) -> None:
        """ApprovalsTracker initializes with empty approvals when no file exists."""
        tracker = ApprovalsTracker(tmp_path)

        assert tracker.list_approvals() == []

    def test_approvals_file_path(self, tmp_path: Path) -> None:
        """approvals_file returns correct path."""
        tracker = ApprovalsTracker(tmp_path)

        expected = tmp_path / "_meta" / "approvals.json"
        assert tracker.approvals_file == expected

    def test_approve_creates_approval_record(self, tmp_path: Path) -> None:
        """approve() creates and returns an Approval record."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        approval = tracker.approve(artifact_id, "human@test.com")

        assert isinstance(approval, Approval)
        assert approval.artifact_id == artifact_id
        assert approval.approved_by == "human@test.com"
        assert isinstance(approval.approved_at, datetime)

    def test_approve_persists_to_file(self, tmp_path: Path) -> None:
        """approve() persists the approval to JSON file."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        tracker.approve(artifact_id, "human@test.com")

        # Check file exists and contains the approval
        assert tracker.approvals_file.exists()
        content = json.loads(tracker.approvals_file.read_text(encoding="utf-8"))
        assert len(content["approvals"]) == 1
        assert content["approvals"][0]["artifact_id"] == str(artifact_id)

    def test_is_approved_returns_true_for_approved(self, tmp_path: Path) -> None:
        """is_approved() returns True for approved artifacts."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        tracker.approve(artifact_id, "human@test.com")

        assert tracker.is_approved(artifact_id) is True

    def test_is_approved_returns_false_for_unapproved(self, tmp_path: Path) -> None:
        """is_approved() returns False for unapproved artifacts."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        assert tracker.is_approved(artifact_id) is False

    def test_get_approval_returns_approval_record(self, tmp_path: Path) -> None:
        """get_approval() returns the Approval record for approved artifacts."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        tracker.approve(artifact_id, "human@test.com")
        approval = tracker.get_approval(artifact_id)

        assert approval is not None
        assert approval.artifact_id == artifact_id

    def test_get_approval_returns_none_for_unapproved(self, tmp_path: Path) -> None:
        """get_approval() returns None for unapproved artifacts."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        assert tracker.get_approval(artifact_id) is None

    def test_list_approvals_returns_all_approvals(self, tmp_path: Path) -> None:
        """list_approvals() returns all approval records."""
        tracker = ApprovalsTracker(tmp_path)
        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()

        tracker.approve(id1, "user1")
        tracker.approve(id2, "user2")
        tracker.approve(id3, "user3")

        approvals = tracker.list_approvals()
        assert len(approvals) == 3
        artifact_ids = {a.artifact_id for a in approvals}
        assert artifact_ids == {id1, id2, id3}

    def test_revoke_removes_approval(self, tmp_path: Path) -> None:
        """revoke() removes an approval and returns True."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        tracker.approve(artifact_id, "human@test.com")
        result = tracker.revoke(artifact_id)

        assert result is True
        assert tracker.is_approved(artifact_id) is False

    def test_revoke_returns_false_for_unapproved(self, tmp_path: Path) -> None:
        """revoke() returns False for unapproved artifacts."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        result = tracker.revoke(artifact_id)

        assert result is False

    def test_revoke_persists_removal(self, tmp_path: Path) -> None:
        """revoke() persists the removal to JSON file."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        tracker.approve(artifact_id, "human@test.com")
        tracker.revoke(artifact_id)

        # Reload and verify
        tracker2 = ApprovalsTracker(tmp_path)
        assert tracker2.is_approved(artifact_id) is False

    def test_loads_existing_approvals(self, tmp_path: Path) -> None:
        """ApprovalsTracker loads existing approvals from file."""
        artifact_id = uuid4()
        now = datetime.now(UTC)

        # Create approvals file manually
        meta_dir = tmp_path / "_meta"
        meta_dir.mkdir(parents=True)
        approvals_file = meta_dir / "approvals.json"
        approvals_file.write_text(
            json.dumps(
                {
                    "approvals": [
                        {
                            "artifact_id": str(artifact_id),
                            "approved_by": "preexisting@test.com",
                            "approved_at": now.isoformat(),
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        # Load tracker
        tracker = ApprovalsTracker(tmp_path)

        assert tracker.is_approved(artifact_id) is True
        approval = tracker.get_approval(artifact_id)
        assert approval is not None
        assert approval.approved_by == "preexisting@test.com"

    def test_handles_corrupted_json_gracefully(self, tmp_path: Path) -> None:
        """ApprovalsTracker handles corrupted JSON by starting fresh."""
        # Create corrupted file
        meta_dir = tmp_path / "_meta"
        meta_dir.mkdir(parents=True)
        approvals_file = meta_dir / "approvals.json"
        approvals_file.write_text("not valid json", encoding="utf-8")

        # Should not raise, just start fresh
        tracker = ApprovalsTracker(tmp_path)

        assert tracker.list_approvals() == []

    def test_handles_missing_keys_gracefully(self, tmp_path: Path) -> None:
        """ApprovalsTracker handles malformed JSON by starting fresh."""
        # Create file with missing keys
        meta_dir = tmp_path / "_meta"
        meta_dir.mkdir(parents=True)
        approvals_file = meta_dir / "approvals.json"
        approvals_file.write_text('{"approvals": [{"bad": "data"}]}', encoding="utf-8")

        # Should not raise, just start fresh
        tracker = ApprovalsTracker(tmp_path)

        assert tracker.list_approvals() == []

    def test_approve_overwrites_existing_approval(self, tmp_path: Path) -> None:
        """approve() overwrites if approving same artifact twice."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        tracker.approve(artifact_id, "user1")
        tracker.approve(artifact_id, "user2")

        approval = tracker.get_approval(artifact_id)
        assert approval is not None
        assert approval.approved_by == "user2"
        assert len(tracker.list_approvals()) == 1

    def test_creates_meta_directory_on_save(self, tmp_path: Path) -> None:
        """approve() creates _meta directory if it doesn't exist."""
        tracker = ApprovalsTracker(tmp_path)
        artifact_id = uuid4()

        # _meta shouldn't exist yet
        meta_dir = tmp_path / "_meta"
        assert not meta_dir.exists()

        tracker.approve(artifact_id, "human@test.com")

        assert meta_dir.exists()
        assert tracker.approvals_file.exists()
