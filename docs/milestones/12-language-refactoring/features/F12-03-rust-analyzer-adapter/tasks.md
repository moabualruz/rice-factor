# Feature F12-03: rust-analyzer Adapter - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T12-03-01 | Implement rust-analyzer detection | Pending | P0 |
| T12-03-02 | Create Rust LSP client | Pending | P0 |
| T12-03-03 | Implement rename refactoring | Pending | P0 |
| T12-03-04 | Implement extract refactoring | Pending | P1 |
| T12-03-05 | Handle Cargo workspace | Pending | P1 |
| T12-03-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T12-03-01: Implement rust-analyzer Detection

**Objective**: Detect if rust-analyzer is installed.

**Files to Create**:
- [ ] `rice_factor/adapters/refactoring/rust_analyzer_adapter.py`

**Detection Logic**:
- [ ] Check `rust-analyzer --version`
- [ ] Verify Cargo project (`Cargo.toml`)
- [ ] Check cargo installation

**Implementation**:
```python
def is_available(self) -> bool:
    # Check rust-analyzer
    result = subprocess.run(
        ["rust-analyzer", "--version"],
        capture_output=True,
    )
    if result.returncode != 0:
        return False

    # Check for Cargo project
    cargo_toml = self.project_root / "Cargo.toml"
    return cargo_toml.exists()
```

**Acceptance Criteria**:
- [ ] Detects rust-analyzer
- [ ] Verifies Rust project
- [ ] Handles missing tools

---

### T12-03-02: Create Rust LSP Client

**Objective**: LSP client specialized for rust-analyzer.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/lsp_client.py`

**rust-analyzer Specifics**:
- [ ] Initialization with cargo workspace
- [ ] Extended capabilities
- [ ] Proc macro support

**Implementation**:
```python
class RustAnalyzerClient(LSPClient):
    """LSP client for rust-analyzer."""

    def __init__(self, project_root: Path) -> None:
        super().__init__(["rust-analyzer"])
        self.project_root = project_root

    def _initialize(self) -> None:
        self._send({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": os.getpid(),
                "rootUri": f"file://{self.project_root}",
                "capabilities": {
                    "textDocument": {
                        "rename": {"prepareSupport": True},
                        "codeAction": {"codeActionLiteralSupport": {}},
                    },
                },
                "initializationOptions": {
                    "cargo": {"loadOutDirsFromCheck": True},
                },
            },
        })
```

**Acceptance Criteria**:
- [ ] Connects to rust-analyzer
- [ ] Handles workspace
- [ ] Proper capabilities

---

### T12-03-03: Implement Rename Refactoring

**Objective**: Rename Rust symbols via LSP.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/rust_analyzer_adapter.py`

**Rename Flow**:
1. Prepare rename (get valid range)
2. Execute rename
3. Apply workspace edit

**Implementation**:
```python
def _rename(
    self,
    request: RefactorRequest,
    dry_run: bool,
) -> RefactorResult:
    file_path, position = self._parse_target(request.target)
    file_uri = f"file://{file_path}"

    # Prepare rename (validates position)
    prepare_result = self.lsp_client.prepare_rename(file_uri, position)
    if "error" in prepare_result:
        return RefactorResult(
            success=False,
            changes=[],
            errors=[prepare_result["error"]["message"]],
            tool_used="rust-analyzer",
            dry_run=dry_run,
        )

    # Execute rename
    workspace_edit = self.lsp_client.rename(
        file_uri,
        position,
        request.new_value,
    )

    changes = self._parse_workspace_edit(workspace_edit)

    if not dry_run:
        self._apply_changes(changes)

    return RefactorResult(
        success=True,
        changes=changes,
        errors=[],
        tool_used="rust-analyzer",
        dry_run=dry_run,
    )
```

**Acceptance Criteria**:
- [ ] Renames across crate
- [ ] Updates imports
- [ ] Handles trait impls

---

### T12-03-04: Implement Extract Refactoring

**Objective**: Extract function/variable via rust-analyzer.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/rust_analyzer_adapter.py`

**Code Actions**:
- `rust-analyzer.extractFunction`
- `rust-analyzer.extractVariable`

**Implementation**:
```python
def _extract(
    self,
    request: RefactorRequest,
    dry_run: bool,
) -> RefactorResult:
    file_uri = f"file://{request.target}"
    range_spec = request.parameters.get("range")

    # Get code actions for range
    actions = self.lsp_client.get_code_actions(file_uri, range_spec)

    # Find extract action
    action_title = {
        RefactorOperation.EXTRACT_METHOD: "Extract into function",
        RefactorOperation.EXTRACT_VARIABLE: "Extract into variable",
    }.get(request.operation)

    extract_action = next(
        (a for a in actions if action_title in a.get("title", "")),
        None,
    )

    if not extract_action:
        return RefactorResult(
            success=False,
            changes=[],
            errors=["Extract action not available for selection"],
            tool_used="rust-analyzer",
            dry_run=dry_run,
        )

    # Apply or preview
    ...
```

**Acceptance Criteria**:
- [ ] Extracts functions
- [ ] Extracts variables
- [ ] Handles lifetimes

---

### T12-03-05: Handle Cargo Workspace

**Objective**: Support multi-crate workspaces.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/rust_analyzer_adapter.py`

**Workspace Considerations**:
- [ ] Detect workspace root
- [ ] Refactor across crates
- [ ] Update Cargo.toml deps

**Implementation**:
```python
def _find_workspace_root(self) -> Path:
    """Find Cargo workspace root."""
    current = self.project_root

    while current != current.parent:
        cargo_toml = current / "Cargo.toml"
        if cargo_toml.exists():
            content = cargo_toml.read_text()
            if "[workspace]" in content:
                return current
        current = current.parent

    return self.project_root

def _get_workspace_members(self) -> list[Path]:
    """Get all crates in workspace."""
    root = self._find_workspace_root()
    cargo_toml = root / "Cargo.toml"

    # Parse workspace members
    ...
```

**Acceptance Criteria**:
- [ ] Finds workspace root
- [ ] Refactors all members
- [ ] Single-crate works too

---

### T12-03-06: Write Unit Tests

**Objective**: Test rust-analyzer adapter.

**Files to Create**:
- [ ] `tests/unit/adapters/refactoring/test_rust_analyzer_adapter.py`

**Test Cases**:
- [ ] rust-analyzer detection
- [ ] LSP initialization
- [ ] Rename execution
- [ ] Extract execution
- [ ] Workspace detection
- [ ] Error handling

**Acceptance Criteria**:
- [ ] All methods tested
- [ ] LSP mocked properly

---

## 3. Task Dependencies

```
T12-03-01 (Detection) ──→ T12-03-02 (LSP) ──→ T12-03-03 (Rename)
                                                   │
                                        ┌──────────┴──────────┐
                                        ↓                     ↓
                                T12-03-04 (Extract)   T12-03-05 (Workspace)
                                        │                     │
                                        └──────────┬──────────┘
                                                   ↓
                                           T12-03-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T12-03-01 | Low | Version check |
| T12-03-02 | High | LSP protocol |
| T12-03-03 | Medium | LSP rename |
| T12-03-04 | High | Code actions |
| T12-03-05 | Medium | TOML parsing |
| T12-03-06 | Medium | Mock setup |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
