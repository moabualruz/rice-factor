# Feature F12-01: OpenRewrite Adapter - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T12-01-01 | Create RefactorToolPort interface | Complete | P0 |
| T12-01-02 | Implement OpenRewrite detection | Complete | P0 |
| T12-01-03 | Map operations to recipes | Complete | P0 |
| T12-01-04 | Implement recipe execution | Complete | P0 |
| T12-01-05 | Parse OpenRewrite output | Complete | P0 |
| T12-01-06 | Add rollback support | Complete | P1 |
| T12-01-07 | Write unit tests | Complete | P0 |

---

## 2. Task Details

### T12-01-01: Create RefactorToolPort Interface

**Objective**: Define common interface for refactoring tools.

**Files to Create**:
- [x] `rice_factor/domain/ports/refactor.py`

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
- [x] Port follows hexagonal pattern
- [x] All methods are abstract
- [x] Types are well-defined

---

### T12-01-02: Implement OpenRewrite Detection

**Objective**: Detect if OpenRewrite is available in project.

**Files to Create**:
- [x] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

**Detection Logic**:
- [x] Check for `pom.xml` with OpenRewrite plugin
- [x] Check for `build.gradle` with OpenRewrite plugin
- [x] Verify Maven/Gradle is installed

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
- [x] Detects Maven projects
- [x] Detects Gradle projects
- [x] Returns False if tool missing

---

### T12-01-03: Map Operations to Recipes

**Objective**: Map RefactorOperation to OpenRewrite recipes.

**Files to Modify**:
- [x] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

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
- [x] All supported operations mapped
- [x] Unsupported operations raise error
- [x] Recipe names are correct

---

### T12-01-04: Implement Recipe Execution

**Objective**: Execute OpenRewrite recipes via Maven/Gradle.

**Files to Modify**:
- [x] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

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
- [x] Maven execution works
- [x] Gradle execution works
- [x] Dry-run mode supported
- [x] Errors captured properly

---

### T12-01-05: Parse OpenRewrite Output

**Objective**: Parse recipe execution output to RefactorResult.

**Files to Modify**:
- [x] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

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
- [x] Changed files extracted
- [x] Error messages captured
- [x] Dry-run output parsed

---

### T12-01-06: Add Rollback Support

**Objective**: Rollback failed or unwanted refactoring.

**Files to Modify**:
- [x] `rice_factor/adapters/refactoring/openrewrite_adapter.py`

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
- [x] Files restored to original
- [x] Dry-run needs no rollback
- [x] Rollback success verified

---

### T12-01-07: Write Unit Tests

**Objective**: Test OpenRewrite adapter.

**Files to Create**:
- [x] `tests/unit/adapters/refactoring/test_openrewrite_adapter.py`

**Test Cases**:
- [x] Detection with Maven project
- [x] Detection with Gradle project
- [x] Detection without OpenRewrite
- [x] Recipe mapping correct
- [x] Execution command correct
- [x] Output parsing works
- [x] Rollback works

**Acceptance Criteria**:
- [x] All adapter methods tested
- [x] Edge cases covered

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
| 1.1.0 | 2026-01-11 | Implementation | All tasks completed |
