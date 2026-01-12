"""Diff review API routes.

Provides endpoints for listing, viewing, and managing code diffs.
Maps to F22-02: Diff Review Interface feature.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from rice_factor_web.backend.deps import CurrentUser, ServiceAdapter
from rice_factor_web.backend.schemas.diff import (
    ApproveDiffRequest,
    DiffActionResponse,
    DiffListResponse,
    DiffResponse,
    DiffSummary,
    RejectDiffRequest,
)
from rice_factor_web.backend.websocket.events import diff_approved_event
from rice_factor_web.backend.websocket.manager import ws_manager

router = APIRouter(prefix="/diffs", tags=["diffs"])


def _get_language_from_path(file_path: str) -> str:
    """Determine language from file extension for syntax highlighting."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".kt": "kotlin",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sql": "sql",
        ".sh": "shell",
        ".bash": "shell",
    }
    for ext, lang in ext_map.items():
        if file_path.lower().endswith(ext):
            return lang
    return "text"


def _count_diff_changes(content: str) -> tuple[int, int]:
    """Count lines added and removed from unified diff content."""
    added = 0
    removed = 0
    for line in content.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed


def _apply_diff_to_content(original: str, diff_content: str) -> str:
    """Apply a unified diff to original content to get modified version.

    This is a simplified implementation that handles basic unified diffs.
    """
    result_lines = []
    original_lines = original.split("\n")
    original_idx = 0

    in_hunk = False
    hunk_start = 0

    for line in diff_content.split("\n"):
        if line.startswith("@@"):
            # Parse hunk header: @@ -start,count +start,count @@
            import re

            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
            if match:
                hunk_start = int(match.group(1)) - 1
                # Copy lines before this hunk
                while original_idx < hunk_start and original_idx < len(original_lines):
                    result_lines.append(original_lines[original_idx])
                    original_idx += 1
                in_hunk = True
        elif in_hunk:
            if line.startswith("+") and not line.startswith("+++"):
                # Added line - add to result
                result_lines.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                # Removed line - skip in original
                original_idx += 1
            elif line.startswith(" "):
                # Context line - copy from original
                result_lines.append(line[1:])
                original_idx += 1
            elif not line.startswith("---") and not line.startswith("+++"):
                # End of hunk or other line
                in_hunk = False

    # Copy remaining original lines
    while original_idx < len(original_lines):
        result_lines.append(original_lines[original_idx])
        original_idx += 1

    return "\n".join(result_lines)


@router.get("", response_model=DiffListResponse)
async def list_diffs(
    adapter: ServiceAdapter,
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
) -> DiffListResponse:
    """List all diffs with optional status filtering.

    Args:
        adapter: Service adapter dependency.
        status_filter: Optional filter by status (pending, approved, rejected, applied).

    Returns:
        List of diff summaries.
    """
    diffs: list[DiffSummary] = []
    pending_count = 0

    # Get diffs from the diffs directory
    diffs_dir = adapter.project_root / "diffs"
    if not diffs_dir.exists():
        return DiffListResponse(diffs=[], total=0, pending_count=0)

    for diff_file in diffs_dir.glob("*.diff"):
        try:
            content = diff_file.read_text()
            diff_id = UUID(diff_file.stem)

            # Parse diff metadata from filename or content
            # Format: <uuid>.diff or <uuid>_<target>.diff
            target_file = "unknown"
            if "_" in diff_file.stem:
                parts = diff_file.stem.split("_", 1)
                if len(parts) > 1:
                    target_file = parts[1].replace("_", "/")

            # Try to extract target from diff content
            for line in content.split("\n")[:10]:
                if line.startswith("+++ b/"):
                    target_file = line[6:]
                    break
                elif line.startswith("+++ "):
                    target_file = line[4:]
                    break

            lines_added, lines_removed = _count_diff_changes(content)
            created_at = datetime.fromtimestamp(
                diff_file.stat().st_mtime, tz=UTC
            )

            # Check approval status
            status_file = diff_file.with_suffix(".status")
            diff_status = "pending"
            if status_file.exists():
                diff_status = status_file.read_text().strip()

            if diff_status == "pending":
                pending_count += 1

            # Apply filter
            if status_filter and diff_status != status_filter:
                continue

            diffs.append(
                DiffSummary(
                    id=diff_id,
                    target_file=target_file,
                    status=diff_status,
                    created_at=created_at,
                    lines_added=lines_added,
                    lines_removed=lines_removed,
                    artifact_id=None,
                )
            )
        except Exception:
            # Skip malformed diff files
            continue

    return DiffListResponse(
        diffs=diffs,
        total=len(diffs),
        pending_count=pending_count,
    )


@router.get("/{diff_id}", response_model=DiffResponse)
async def get_diff(
    diff_id: UUID,
    adapter: ServiceAdapter,
) -> DiffResponse:
    """Get a single diff by ID.

    Args:
        diff_id: UUID of the diff.
        adapter: Service adapter dependency.

    Returns:
        Full diff details including content.

    Raises:
        HTTPException: 404 if diff not found.
    """
    diffs_dir = adapter.project_root / "diffs"

    # Try to find the diff file
    diff_file = diffs_dir / f"{diff_id}.diff"
    if not diff_file.exists():
        # Try pattern with target in filename
        matches = list(diffs_dir.glob(f"{diff_id}*.diff"))
        if matches:
            diff_file = matches[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diff not found: {diff_id}",
            )

    content = diff_file.read_text()

    # Extract target file from content
    target_file = "unknown"
    for line in content.split("\n")[:10]:
        if line.startswith("+++ b/"):
            target_file = line[6:]
            break
        elif line.startswith("+++ "):
            target_file = line[4:]
            break

    lines_added, lines_removed = _count_diff_changes(content)
    created_at = datetime.fromtimestamp(diff_file.stat().st_mtime, tz=UTC)

    # Check status
    status_file = diff_file.with_suffix(".status")
    diff_status = "pending"
    if status_file.exists():
        diff_status = status_file.read_text().strip()

    # Try to read original file and compute modified content
    original_content: str | None = None
    modified_content: str | None = None

    if target_file and target_file != "unknown":
        # Try to read the original file
        original_path = adapter.project_root / target_file
        if original_path.exists():
            try:
                original_content = original_path.read_text()
                modified_content = _apply_diff_to_content(original_content, content)
            except Exception:
                # If we can't read or apply, leave as None
                pass
        else:
            # File doesn't exist yet (new file), original is empty
            original_content = ""
            modified_content = _apply_diff_to_content("", content)

    return DiffResponse(
        id=diff_id,
        target_file=target_file,
        status=diff_status,
        created_at=created_at,
        lines_added=lines_added,
        lines_removed=lines_removed,
        artifact_id=None,
        content=content,
        language=_get_language_from_path(target_file),
        original_content=original_content,
        modified_content=modified_content,
    )


@router.post("/{diff_id}/approve", response_model=DiffActionResponse)
async def approve_diff(
    diff_id: UUID,
    adapter: ServiceAdapter,
    user: CurrentUser,
    request: ApproveDiffRequest | None = None,
) -> DiffActionResponse:
    """Approve a diff for application.

    Args:
        diff_id: UUID of the diff to approve.
        adapter: Service adapter dependency.
        user: Current user (optional if auth disabled).
        request: Optional approval request with comment.

    Returns:
        Approval confirmation.

    Raises:
        HTTPException: 404 if diff not found.
    """
    diffs_dir = adapter.project_root / "diffs"
    diff_file = diffs_dir / f"{diff_id}.diff"

    if not diff_file.exists():
        matches = list(diffs_dir.glob(f"{diff_id}*.diff"))
        if matches:
            diff_file = matches[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diff not found: {diff_id}",
            )

    # Write status file
    status_file = diff_file.with_suffix(".status")
    status_file.write_text("approved")

    username = "anonymous"
    if user:
        username = user.get("username", user.get("id", "anonymous"))

    # Broadcast WebSocket event
    content = diff_file.read_text()
    target_file = "unknown"
    for line in content.split("\n")[:10]:
        if line.startswith("+++ b/"):
            target_file = line[6:]
            break

    event = diff_approved_event(
        diff_id=str(diff_id),
        target_file=target_file,
        approved_by=username,
    )
    await ws_manager.broadcast(event)

    return DiffActionResponse(
        diff_id=diff_id,
        action="approved",
        performed_by=username,
        performed_at=datetime.now(UTC),
    )


@router.post("/{diff_id}/reject", response_model=DiffActionResponse)
async def reject_diff(
    diff_id: UUID,
    adapter: ServiceAdapter,
    user: CurrentUser,
    request: RejectDiffRequest,
) -> DiffActionResponse:
    """Reject a diff.

    Args:
        diff_id: UUID of the diff to reject.
        adapter: Service adapter dependency.
        user: Current user (optional if auth disabled).
        request: Rejection request with reason.

    Returns:
        Rejection confirmation.

    Raises:
        HTTPException: 404 if diff not found.
    """
    diffs_dir = adapter.project_root / "diffs"
    diff_file = diffs_dir / f"{diff_id}.diff"

    if not diff_file.exists():
        matches = list(diffs_dir.glob(f"{diff_id}*.diff"))
        if matches:
            diff_file = matches[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diff not found: {diff_id}",
            )

    # Write status file with reason
    status_file = diff_file.with_suffix(".status")
    status_file.write_text(f"rejected:{request.reason}")

    username = "anonymous"
    if user:
        username = user.get("username", user.get("id", "anonymous"))

    return DiffActionResponse(
        diff_id=diff_id,
        action="rejected",
        performed_by=username,
        performed_at=datetime.now(UTC),
    )


# In-memory store for inline comments (could be persisted to filesystem or database)
_comments_store: dict[str, list[dict]] = {}


class CommentRequest(BaseModel):
    """Request to create or update a comment."""

    line_number: int = Field(..., description="Line number for the comment")
    content: str = Field(..., description="Comment content")


class CommentResponse(BaseModel):
    """Response for a single comment."""

    id: str = Field(..., description="Comment ID")
    diff_id: str = Field(..., description="Diff ID")
    line_number: int = Field(..., description="Line number")
    content: str = Field(..., description="Comment content")
    author: str = Field(..., description="Comment author")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class CommentsListResponse(BaseModel):
    """Response for listing comments."""

    comments: list[CommentResponse] = Field(default_factory=list)


@router.get("/{diff_id}/comments", response_model=CommentsListResponse)
async def list_comments(
    diff_id: UUID,
    adapter: ServiceAdapter,
) -> CommentsListResponse:
    """List all comments for a diff.

    Args:
        diff_id: UUID of the diff.
        adapter: Service adapter dependency.

    Returns:
        List of comments.
    """
    diff_key = str(diff_id)
    comments = _comments_store.get(diff_key, [])
    return CommentsListResponse(
        comments=[CommentResponse(**c) for c in comments]
    )


@router.post("/{diff_id}/comments", response_model=CommentResponse)
async def create_comment(
    diff_id: UUID,
    adapter: ServiceAdapter,
    user: CurrentUser,
    request: CommentRequest,
) -> CommentResponse:
    """Create a new inline comment on a diff.

    Args:
        diff_id: UUID of the diff.
        adapter: Service adapter dependency.
        user: Current user.
        request: Comment request with line number and content.

    Returns:
        Created comment.
    """
    diff_key = str(diff_id)

    username = "anonymous"
    if user:
        username = user.get("username", user.get("id", "anonymous"))

    comment_id = f"{diff_key}-{datetime.now(UTC).timestamp()}"
    now = datetime.now(UTC)

    comment_data = {
        "id": comment_id,
        "diff_id": diff_key,
        "line_number": request.line_number,
        "content": request.content,
        "author": username,
        "created_at": now,
        "updated_at": None,
    }

    if diff_key not in _comments_store:
        _comments_store[diff_key] = []
    _comments_store[diff_key].append(comment_data)

    return CommentResponse(**comment_data)


@router.put("/{diff_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    diff_id: UUID,
    comment_id: str,
    adapter: ServiceAdapter,
    user: CurrentUser,
    request: CommentRequest,
) -> CommentResponse:
    """Update an existing inline comment.

    Args:
        diff_id: UUID of the diff.
        comment_id: ID of the comment to update.
        adapter: Service adapter dependency.
        user: Current user.
        request: Updated comment content.

    Returns:
        Updated comment.

    Raises:
        HTTPException: 404 if comment not found.
    """
    diff_key = str(diff_id)
    comments = _comments_store.get(diff_key, [])

    for comment in comments:
        if comment["id"] == comment_id:
            comment["content"] = request.content
            comment["updated_at"] = datetime.now(UTC)
            return CommentResponse(**comment)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Comment not found: {comment_id}",
    )


@router.delete("/{diff_id}/comments/{comment_id}")
async def delete_comment(
    diff_id: UUID,
    comment_id: str,
    adapter: ServiceAdapter,
    user: CurrentUser,
) -> dict[str, bool]:
    """Delete an inline comment.

    Args:
        diff_id: UUID of the diff.
        comment_id: ID of the comment to delete.
        adapter: Service adapter dependency.
        user: Current user.

    Returns:
        Deletion confirmation.

    Raises:
        HTTPException: 404 if comment not found.
    """
    diff_key = str(diff_id)
    comments = _comments_store.get(diff_key, [])

    for i, comment in enumerate(comments):
        if comment["id"] == comment_id:
            del comments[i]
            return {"deleted": True}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Comment not found: {comment_id}",
    )
