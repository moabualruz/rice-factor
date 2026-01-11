# Feature F12-04: jscodeshift Adapter - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T12-04-01 | Implement jscodeshift detection | Pending | P0 |
| T12-04-02 | Create transform templates | Pending | P0 |
| T12-04-03 | Implement rename transform | Pending | P0 |
| T12-04-04 | Implement extract transform | Pending | P1 |
| T12-04-05 | Handle TypeScript | Pending | P0 |
| T12-04-06 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T12-04-01: Implement jscodeshift Detection

**Objective**: Detect if jscodeshift is available.

**Files to Create**:
- [ ] `rice_factor/adapters/refactoring/jscodeshift_adapter.py`

**Detection Logic**:
- [ ] Check `npx jscodeshift --version`
- [ ] Verify package.json exists
- [ ] Check for node_modules

**Implementation**:
```python
def is_available(self) -> bool:
    # Check jscodeshift via npx
    result = subprocess.run(
        ["npx", "jscodeshift", "--version"],
        capture_output=True,
        cwd=self.project_root,
    )
    if result.returncode != 0:
        return False

    # Verify JS/TS project
    package_json = self.project_root / "package.json"
    return package_json.exists()
```

**Acceptance Criteria**:
- [ ] Detects jscodeshift
- [ ] Works with npx
- [ ] Verifies JS project

---

### T12-04-02: Create Transform Templates

**Objective**: Bundle transform scripts for operations.

**Files to Create**:
- [ ] `rice_factor/adapters/refactoring/transforms/rename-symbol.js`
- [ ] `rice_factor/adapters/refactoring/transforms/extract-function.js`
- [ ] `rice_factor/adapters/refactoring/transforms/extract-variable.js`

**Rename Transform**:
```javascript
// rename-symbol.js
module.exports = function(fileInfo, api, options) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);

  const { oldName, newName } = options;

  // Rename identifier references
  root.find(j.Identifier, { name: oldName })
    .forEach(path => {
      path.node.name = newName;
    });

  return root.toSource();
};
```

**Acceptance Criteria**:
- [ ] Transforms are valid JS
- [ ] Accept options correctly
- [ ] Preserve formatting

---

### T12-04-03: Implement Rename Transform

**Objective**: Rename symbols using jscodeshift.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/jscodeshift_adapter.py`

**Command**:
```bash
npx jscodeshift \
  -t transforms/rename-symbol.js \
  --oldName=OldClass \
  --newName=NewClass \
  --parser=tsx \
  src/**/*.ts src/**/*.tsx
```

**Implementation**:
```python
def _rename(
    self,
    request: RefactorRequest,
    dry_run: bool,
) -> RefactorResult:
    transform = self.transforms_dir / "rename-symbol.js"

    cmd = [
        "npx", "jscodeshift",
        "-t", str(transform),
        "--parser", "tsx",
        f"--oldName={request.target}",
        f"--newName={request.new_value}",
    ]

    if dry_run:
        cmd.append("--dry")
        cmd.append("--print")

    # Add target files
    cmd.extend(self._get_js_files())

    result = subprocess.run(
        cmd,
        cwd=self.project_root,
        capture_output=True,
        text=True,
    )

    return self._parse_result(result, dry_run)
```

**Acceptance Criteria**:
- [ ] Renames identifiers
- [ ] Works with JSX/TSX
- [ ] Dry-run shows changes

---

### T12-04-04: Implement Extract Transform

**Objective**: Extract function/variable transforms.

**Files to Create**:
- [ ] `rice_factor/adapters/refactoring/transforms/extract-function.js`

**Extract Function Transform**:
```javascript
// extract-function.js
module.exports = function(fileInfo, api, options) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);

  const { startLine, endLine, functionName } = options;

  // Find statements in range
  // Extract to new function
  // Replace with function call
  ...

  return root.toSource();
};
```

**Implementation**:
```python
def _extract_function(
    self,
    request: RefactorRequest,
    dry_run: bool,
) -> RefactorResult:
    transform = self.transforms_dir / "extract-function.js"

    params = request.parameters or {}

    cmd = [
        "npx", "jscodeshift",
        "-t", str(transform),
        "--parser", "tsx",
        f"--startLine={params.get('start_line')}",
        f"--endLine={params.get('end_line')}",
        f"--functionName={request.new_value}",
        request.target,  # Single file
    ]

    if dry_run:
        cmd.extend(["--dry", "--print"])

    result = subprocess.run(
        cmd,
        cwd=self.project_root,
        capture_output=True,
        text=True,
    )

    return self._parse_result(result, dry_run)
```

**Acceptance Criteria**:
- [ ] Extracts code range
- [ ] Creates new function
- [ ] Updates call site

---

### T12-04-05: Handle TypeScript

**Objective**: Full TypeScript support.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/jscodeshift_adapter.py`

**TypeScript Considerations**:
- [ ] Use `tsx` parser
- [ ] Handle type annotations
- [ ] Support .ts, .tsx, .d.ts files
- [ ] Preserve type imports

**Implementation**:
```python
def _get_parser(self, file_path: str) -> str:
    """Get appropriate parser for file type."""
    ext = Path(file_path).suffix

    parsers = {
        ".js": "babel",
        ".jsx": "babel",
        ".ts": "tsx",
        ".tsx": "tsx",
        ".mjs": "babel",
        ".cjs": "babel",
    }

    return parsers.get(ext, "tsx")

def _get_js_files(self) -> list[str]:
    """Get all JS/TS files in project."""
    extensions = [".js", ".jsx", ".ts", ".tsx"]
    files = []

    for ext in extensions:
        files.extend(
            str(p) for p in self.project_root.rglob(f"*{ext}")
            if "node_modules" not in str(p)
        )

    return files
```

**Acceptance Criteria**:
- [ ] TS files refactored
- [ ] Types preserved
- [ ] node_modules ignored

---

### T12-04-06: Write Unit Tests

**Objective**: Test jscodeshift adapter.

**Files to Create**:
- [ ] `tests/unit/adapters/refactoring/test_jscodeshift_adapter.py`

**Test Cases**:
- [ ] jscodeshift detection
- [ ] Transform execution
- [ ] Rename transform
- [ ] Extract transform
- [ ] TypeScript handling
- [ ] Dry-run output parsing
- [ ] Error handling

**Acceptance Criteria**:
- [ ] All transforms tested
- [ ] Output parsing verified

---

## 3. Task Dependencies

```
T12-04-01 (Detection) ──→ T12-04-02 (Templates) ──→ T12-04-03 (Rename)
                                                          │
                                                          ↓
                                                   T12-04-04 (Extract)
                                                          │
                                                          ↓
                                                   T12-04-05 (TypeScript)
                                                          │
                                                          ↓
                                                   T12-04-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T12-04-01 | Low | npx check |
| T12-04-02 | Medium | AST manipulation |
| T12-04-03 | Medium | Transform logic |
| T12-04-04 | High | Complex extraction |
| T12-04-05 | Medium | Parser config |
| T12-04-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
