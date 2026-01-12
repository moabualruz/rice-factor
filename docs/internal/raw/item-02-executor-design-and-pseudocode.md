# ITEM 2 — **Executor Design & Pseudocode**

## 2.1 Executor Philosophy (Non-Negotiable)

Executors are:

* **Dumb**
* **Deterministic**
* **Stateless**
* **Fail-fast**
* **Auditable**

They are **not allowed** to:

* infer intent
* repair artifacts
* recover silently
* call LLMs
* mutate artifacts

Think: **Unix tools, not agents**.

---

## 2.2 Executor Interface (Universal)

All executors conform to the same interface.

### Abstract Interface

```text
execute(
  artifact_path: Path,
  repo_root: Path,
  mode: DRY_RUN | APPLY
) -> ExecutionResult
```

---

### ExecutionResult

```json
{
  "status": "success | failure",
  "diffs": ["audit/diffs/<id>.diff"],
  "errors": ["string"],
  "logs": ["string"]
}
```

---

## 2.3 Shared Executor Pipeline (All Executors)

Every executor follows this exact pipeline:

```text
1. Load artifact
2. Validate schema
3. Verify approval & lock status
4. Capability check
5. Precondition checks
6. Generate diff
7. (If APPLY) Apply diff
8. Emit audit logs
9. Return result
```

No step is optional.

---

## 2.4 Shared Utility Functions (Pseudocode)

These are reused everywhere.

### Load & Validate Artifact

```pseudo
function load_artifact(path):
  artifact = read_json(path)

  if not validate_schema(artifact):
    fail("schema_validation_failed")

  if artifact.status == "draft":
    fail("artifact_not_approved")

  return artifact
```

---

### Approval Verification

```pseudo
function verify_approval(artifact_id):
  approvals = read_json("artifacts/_meta/approvals.json")

  if artifact_id not in approvals:
    fail("artifact_not_approved")
```

---

### Capability Check

```pseudo
function check_capability(operation, language):
  registry = read_yaml("tools/registry/capability_registry.yaml")

  if registry.languages[language].operations[operation] != true:
    fail("operation_not_supported")
```

---

## 2.5 Executor 1 — Scaffold Executor

### Purpose

Create empty files and directories only.

---

### Inputs

* `ScaffoldPlan`
* Repo root

---

### Preconditions

* File does not already exist
* Path is within repo
* No file content allowed beyond headers/comments

---

### Pseudocode

```pseudo
function execute_scaffold(artifact_path, repo_root):
  artifact = load_artifact(artifact_path)

  for file in artifact.payload.files:
    abs_path = repo_root / file.path

    if exists(abs_path):
      fail("file_already_exists")

    create_directories(parent(abs_path))

    content = generate_header_comment(file.description)
    write_file(abs_path, content)

    record_log("created " + file.path)

  return success
```

---

### Failure Modes

* File already exists
* Path escapes repo root
* Missing description

---

## 2.6 Executor 2 — Diff Executor (Implementation)

### Purpose

Apply **approved diffs only**.

---

### Inputs

* Diff file
* Repo root

---

### Preconditions

* Diff touches only files declared in `ImplementationPlan`
* Tests are not modified if locked
* No binary files

---

### Pseudocode

```pseudo
function execute_diff(diff_path, repo_root, mode):
  diff = read_diff(diff_path)

  for file in diff.touched_files:
    if file not in allowed_files:
      fail("unauthorized_file_modification")

    if is_test_file(file) and tests_locked():
      fail("test_modification_forbidden")

  if mode == DRY_RUN:
    return diff

  result = git_apply(diff)

  if not result.success:
    fail("patch_failed")

  return success
```

---

### Key Rule

> **Diff executor never generates diffs — only applies them**

---

## 2.7 Executor 3 — Refactor Executor (MVP)

### Purpose

Perform **mechanical refactors** only.

---

### Supported Operations (MVP)

* `move_file`
* `rename_symbol` (simple textual / tool-assisted)

---

### Pseudocode

```pseudo
function execute_refactor(artifact_path, repo_root, mode):
  artifact = load_artifact(artifact_path)

  for op in artifact.payload.operations:
    check_capability(op.type, language)

    if op.type == "move_file":
      plan_move(op)

    if op.type == "rename_symbol":
      plan_rename(op)

  diff = generate_diff_from_plans()

  if mode == DRY_RUN:
    return diff

  apply_diff(diff)
  return success
```

---

### Example: Move File

```pseudo
function plan_move(op):
  if not exists(op.from):
    fail("source_missing")

  if exists(op.to):
    fail("destination_exists")

  stage_move(op.from, op.to)
```

---

## 2.8 Executor 4 — Test Runner

### Purpose

Verify correctness.

---

### Pseudocode

```pseudo
function run_tests(language):
  if language == "rust":
    result = exec("cargo test")

  if result.exit_code != 0:
    emit ValidationResult(failed)
    return failure

  emit ValidationResult(passed)
  return success
```

---

## 2.9 Executor 5 — Architecture Validator (Optional in MVP)

Reads `ArchitecturePlan` and checks imports.

Fails on violation.

No auto-fixing.

---

## 2.10 Audit Logging (Mandatory)

Every executor must append logs.

### Example

```json
{
  "timestamp": "...",
  "executor": "diff_executor",
  "artifact": "implementation/user.json",
  "status": "success",
  "diff": "audit/diffs/123.diff"
}
```

No log → execution is invalid.

---

## 2.11 Failure Is a Feature

Executors must **fail loudly** when:

* Artifact invalid
* Approval missing
* Capability unsupported
* Patch fails
* Preconditions violated

There is **no recovery logic** in executors.

Recovery happens at the **planning layer**, not execution.

---

## 2.12 Why This Design Is Correct

This executor design guarantees:

* No accidental changes
* No hidden intelligence
* Perfect reproducibility
* Clear failure points
* Easy debugging
* Language independence

You can:

* rewrite executors in any language
* parallelize them later
* sandbox them
* CI-run them

Without changing the architecture.