# Feature F12-02: gopls Adapter - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T12-02-01 | Implement gopls detection | Pending | P0 |
| T12-02-02 | Create LSP client wrapper | Pending | P0 |
| T12-02-03 | Implement rename refactoring | Pending | P0 |
| T12-02-04 | Implement extract refactoring | Pending | P1 |
| T12-02-05 | Parse LSP responses | Pending | P0 |
| T12-02-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T12-02-01: Implement gopls Detection

**Objective**: Detect if gopls is installed and usable.

**Files to Create**:
- [ ] `rice_factor/adapters/refactoring/gopls_adapter.py`

**Detection Logic**:
- [ ] Check `gopls version` command
- [ ] Verify Go module in project (`go.mod`)
- [ ] Check gorename availability (simpler CLI)

**Implementation**:
```python
def is_available(self) -> bool:
    # Check gopls
    result = subprocess.run(
        ["gopls", "version"],
        capture_output=True,
    )
    if result.returncode != 0:
        return False

    # Check for Go module
    go_mod = self.project_root / "go.mod"
    return go_mod.exists()
```

**Acceptance Criteria**:
- [ ] gopls detected correctly
- [ ] Missing gopls returns False
- [ ] Non-Go project returns False

---

### T12-02-02: Create LSP Client Wrapper

**Objective**: Wrapper for LSP communication with gopls.

**Files to Create**:
- [ ] `rice_factor/adapters/refactoring/lsp_client.py`

**LSP Operations**:
- [ ] Initialize connection
- [ ] Send textDocument/rename request
- [ ] Send textDocument/codeAction request
- [ ] Apply workspace/applyEdit

**Implementation**:
```python
class LSPClient:
    """Simple LSP client for refactoring operations."""

    def __init__(self, server_cmd: list[str]) -> None:
        self.process = subprocess.Popen(
            server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._initialize()

    def _initialize(self) -> None:
        """Send LSP initialize request."""
        self._send({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "capabilities": {},
            },
        })

    def rename(
        self,
        file_uri: str,
        position: dict,
        new_name: str,
    ) -> dict:
        """Request rename refactoring."""
        return self._send({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "textDocument/rename",
            "params": {
                "textDocument": {"uri": file_uri},
                "position": position,
                "newName": new_name,
            },
        })
```

**Acceptance Criteria**:
- [ ] LSP protocol correct
- [ ] Handles responses
- [ ] Graceful shutdown

---

### T12-02-03: Implement Rename Refactoring

**Objective**: Perform Go rename via gopls.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/gopls_adapter.py`

**Alternative: Use gorename**:
```bash
gorename -from "pkg.OldName" -to "NewName"
```

**Implementation**:
```python
def _rename(
    self,
    request: RefactorRequest,
    dry_run: bool,
) -> RefactorResult:
    cmd = [
        "gorename",
        "-from", request.target,
        "-to", request.new_value,
    ]

    if dry_run:
        cmd.append("-d")

    result = subprocess.run(
        cmd,
        cwd=self.project_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return RefactorResult(
            success=False,
            changes=[],
            errors=[result.stderr],
            tool_used="gorename",
            dry_run=dry_run,
        )

    changes = self._parse_diff(result.stdout)
    return RefactorResult(
        success=True,
        changes=changes,
        errors=[],
        tool_used="gorename",
        dry_run=dry_run,
    )
```

**Acceptance Criteria**:
- [ ] Renames symbols across files
- [ ] Dry-run shows changes
- [ ] Errors reported

---

### T12-02-04: Implement Extract Refactoring

**Objective**: Extract method/variable via gopls.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/gopls_adapter.py`

**LSP Code Action**:
```python
def _extract(
    self,
    request: RefactorRequest,
    dry_run: bool,
) -> RefactorResult:
    # Use LSP code actions
    file_uri = f"file://{request.target}"

    # Get code actions for selection
    actions = self.lsp_client.get_code_actions(
        file_uri,
        request.parameters.get("range"),
    )

    # Find extract action
    extract_action = next(
        (a for a in actions if "extract" in a["title"].lower()),
        None,
    )

    if not extract_action:
        return RefactorResult(
            success=False,
            changes=[],
            errors=["No extract action available"],
            tool_used="gopls",
            dry_run=dry_run,
        )

    if dry_run:
        # Return what would change
        return RefactorResult(
            success=True,
            changes=self._preview_action(extract_action),
            errors=[],
            tool_used="gopls",
            dry_run=True,
        )

    # Apply the action
    self.lsp_client.execute_command(extract_action["command"])
    ...
```

**Acceptance Criteria**:
- [ ] Finds extract actions
- [ ] Applies code action
- [ ] Dry-run previews

---

### T12-02-05: Parse LSP Responses

**Objective**: Convert LSP edits to RefactorChange.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/gopls_adapter.py`

**LSP WorkspaceEdit Format**:
```json
{
  "changes": {
    "file:///path/to/file.go": [
      {
        "range": {"start": {...}, "end": {...}},
        "newText": "..."
      }
    ]
  }
}
```

**Implementation**:
```python
def _parse_workspace_edit(
    self,
    edit: dict,
) -> list[RefactorChange]:
    changes = []

    for uri, text_edits in edit.get("changes", {}).items():
        file_path = uri.replace("file://", "")
        original = Path(file_path).read_text()

        # Apply edits to get new content
        new_content = self._apply_edits(original, text_edits)

        changes.append(RefactorChange(
            file_path=file_path,
            original_content=original,
            new_content=new_content,
            description=f"{len(text_edits)} edits",
        ))

    return changes
```

**Acceptance Criteria**:
- [ ] URIs converted to paths
- [ ] Text edits applied
- [ ] Changes list complete

---

### T12-02-06: Write Unit Tests

**Objective**: Test gopls adapter.

**Files to Create**:
- [ ] `tests/unit/adapters/refactoring/test_gopls_adapter.py`

**Test Cases**:
- [ ] gopls detection
- [ ] gorename command building
- [ ] Dry-run output parsing
- [ ] LSP response parsing
- [ ] Rename execution
- [ ] Error handling

**Acceptance Criteria**:
- [ ] All methods tested
- [ ] Mocked subprocess calls

---

## 3. Task Dependencies

```
T12-02-01 (Detection) ──→ T12-02-02 (LSP Client) ──→ T12-02-03 (Rename)
                                                          │
                                                          ↓
                                                   T12-02-04 (Extract)
                                                          │
                                                          ↓
                                                   T12-02-05 (Parse)
                                                          │
                                                          ↓
                                                   T12-02-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T12-02-01 | Low | Version check |
| T12-02-02 | High | LSP protocol |
| T12-02-03 | Medium | gorename CLI |
| T12-02-04 | High | LSP code actions |
| T12-02-05 | Medium | JSON parsing |
| T12-02-06 | Medium | Mock setup |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
