# Feature F12-01: OpenRewrite Adapter - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.0.0
> **Status**: Pending
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T12-01-01 | Create RefactorToolPort interface | Pending | P0 |
| T12-01-02 | Implement OpenRewrite detection | Pending | P0 |
| T12-01-03 | Map operations to recipes | Pending | P0 |
| T12-01-04 | Implement recipe execution | Pending | P0 |
| T12-01-05 | Parse OpenRewrite output | Pending | P0 |
| T12-01-06 | Add rollback support | Pending | P1 |
| T12-01-07 | Write unit tests | Pending | P0 |

---

## 2. Task Details

### T12-01-01: Create RefactorToolPort Interface

**Objective**: Define common interface for refactoring tools.

**Files to Create**:
- [ ] `rice_factor/domain/ports/refactor.py`

**Implementation**:
```python
class RefactorToolPort(ABC):
    @abstractmethod
    def get_supported_languages(self) -> list[str]: ...

    @abstractmethod
    def get_supported_operations(self) -> list[RefactorOperation]: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def execute(
        self,
        request: RefactorRequest,
        dry_run: bool = True,
    ) -> RefactorResult: ...

    @abstractmethod
    def rollback(self, result: RefactorResult) -> bool: ...
```

**Acceptance Criteria**:
- [ ] Port follows hexagonal pattern
- [ ] All methods are abstract
- [ ] Types are well-defined

---

### T12-01-02: Implement OpenRewrite Detection

**Objective**: Detect if OpenRewrite is available in project.

**Files to Create**:
- [ ] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

**Detection Logic**:
- [ ] Check for `pom.xml` with OpenRewrite plugin
- [ ] Check for `build.gradle` with OpenRewrite plugin
- [ ] Verify Maven/Gradle is installed

**Implementation**:
```python
def is_available(self) -> bool:
    # Check pom.xml
    pom = self.project_root / "pom.xml"
    if pom.exists() and "openrewrite" in pom.read_text().lower():
        return self._maven_available()

    # Check build.gradle
    gradle = self.project_root / "build.gradle"
    if gradle.exists() and "openrewrite" in gradle.read_text().lower():
        return self._gradle_available()

    return False
```

**Acceptance Criteria**:
- [ ] Detects Maven projects
- [ ] Detects Gradle projects
- [ ] Returns False if tool missing

---

### T12-01-03: Map Operations to Recipes

**Objective**: Map RefactorOperation to OpenRewrite recipes.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

**Recipe Mapping**:

| Operation | Recipe |
|-----------|--------|
| RENAME | `org.openrewrite.java.ChangeType` |
| MOVE | `org.openrewrite.java.ChangePackage` |
| CHANGE_SIGNATURE | `org.openrewrite.java.ChangeMethodName` |

**Implementation**:
```python
RECIPE_MAP = {
    RefactorOperation.RENAME: "org.openrewrite.java.ChangeType",
    RefactorOperation.MOVE: "org.openrewrite.java.ChangePackage",
    RefactorOperation.CHANGE_SIGNATURE: "org.openrewrite.java.ChangeMethodName",
}

def _get_recipe(self, operation: RefactorOperation) -> str:
    recipe = self.RECIPE_MAP.get(operation)
    if not recipe:
        raise UnsupportedOperationError(operation)
    return recipe
```

**Acceptance Criteria**:
- [ ] All supported operations mapped
- [ ] Unsupported operations raise error
- [ ] Recipe names are correct

---

### T12-01-04: Implement Recipe Execution

**Objective**: Execute OpenRewrite recipes via Maven/Gradle.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

**Maven Command**:
```bash
mvn rewrite:run \
  -Drewrite.activeRecipes=org.openrewrite.java.ChangeType \
  -Drewrite.oldType=com.example.UserService \
  -Drewrite.newType=com.example.AccountService
```

**Gradle Command**:
```bash
./gradlew rewriteRun \
  -Drewrite.activeRecipe=org.openrewrite.java.ChangeType \
  -Drewrite.options.oldFullyQualifiedTypeName=com.example.UserService \
  -Drewrite.options.newFullyQualifiedTypeName=com.example.AccountService
```

**Acceptance Criteria**:
- [ ] Maven execution works
- [ ] Gradle execution works
- [ ] Dry-run mode supported
- [ ] Errors captured properly

---

### T12-01-05: Parse OpenRewrite Output

**Objective**: Parse recipe execution output to RefactorResult.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

**Output Format**:
```
[INFO] Running recipe: org.openrewrite.java.ChangeType
[INFO] Changes made to:
[INFO]   src/main/java/com/example/UserService.java
[INFO]   src/main/java/com/example/UserController.java
[INFO] 2 files changed
```

**Implementation**:
```python
def _parse_output(self, stdout: str) -> list[RefactorChange]:
    changes = []
    for line in stdout.splitlines():
        if line.strip().startswith("src/"):
            file_path = line.strip()
            changes.append(RefactorChange(
                file_path=file_path,
                original_content="",  # Would need git diff
                new_content="",
                description="Modified by OpenRewrite",
            ))
    return changes
```

**Acceptance Criteria**:
- [ ] Changed files extracted
- [ ] Error messages captured
- [ ] Dry-run output parsed

---

### T12-01-06: Add Rollback Support

**Objective**: Rollback failed or unwanted refactoring.

**Files to Modify**:
- [ ] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

**Rollback Strategy**:
1. Use git to restore original files
2. Track which files were modified
3. Verify rollback success

**Implementation**:
```python
def rollback(self, result: RefactorResult) -> bool:
    if result.dry_run:
        return True  # Nothing to rollback

    for change in result.changes:
        subprocess.run(
            ["git", "checkout", change.file_path],
            cwd=self.project_root,
        )

    return True
```

**Acceptance Criteria**:
- [ ] Files restored to original
- [ ] Dry-run needs no rollback
- [ ] Rollback success verified

---

### T12-01-07: Write Unit Tests

**Objective**: Test OpenRewrite adapter.

**Files to Create**:
- [ ] `tests/unit/adapters/refactoring/test_openrewrite_adapter.py`

**Test Cases**:
- [ ] Detection with Maven project
- [ ] Detection with Gradle project
- [ ] Detection without OpenRewrite
- [ ] Recipe mapping correct
- [ ] Execution command correct
- [ ] Output parsing works
- [ ] Rollback works

**Acceptance Criteria**:
- [ ] All adapter methods tested
- [ ] Edge cases covered

---

## 3. Task Dependencies

```
T12-01-01 (Port) ──→ T12-01-02 (Detection) ──→ T12-01-03 (Mapping)
                                                      │
                                                      ↓
                                              T12-01-04 (Execute)
                                                      │
                                                      ↓
                                              T12-01-05 (Parse)
                                                      │
                                                      ↓
                                              T12-01-06 (Rollback)
                                                      │
                                                      ↓
                                              T12-01-07 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T12-01-01 | Low | Interface definition |
| T12-01-02 | Medium | File parsing |
| T12-01-03 | Low | Mapping table |
| T12-01-04 | High | Subprocess handling |
| T12-01-05 | Medium | Output parsing |
| T12-01-06 | Low | Git operations |
| T12-01-07 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
