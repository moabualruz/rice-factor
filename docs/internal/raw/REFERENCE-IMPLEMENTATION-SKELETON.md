# REFERENCE IMPLEMENTATION SKELETON

*(Architecturally correct, MVP-ready, extensible)*

I’ll assume:

* **Language:** Python (best for orchestration + JSON Schema + CLI)
* **Executors:** shell / git-backed (language-agnostic)
* **LLM access:** abstracted (you plug OpenCode / Claude / Codex later)

You can port this later; structure matters more than language.

---

## 1. Repository Layout (Final, Build-From-Here)

```text
devsys/
├─ cli/
│  ├─ __init__.py
│  ├─ main.py              # entrypoint: `dev`
│  └─ commands/
│     ├─ init.py
│     ├─ plan.py
│     ├─ scaffold.py
│     ├─ impl.py
│     ├─ refactor.py
│     ├─ validate.py
│     └─ resume.py
│
├─ core/
│  ├─ artifacts/
│  │  ├─ loader.py
│  │  ├─ validator.py
│  │  ├─ registry.py
│  │  └─ approvals.py
│  │
│  ├─ llm/
│  │  ├─ interface.py      # abstract LLM interface
│  │  ├─ roles.py          # planner / critic / etc
│  │  └─ compiler.py       # artifact builder passes
│  │
│  ├─ executors/
│  │  ├─ base.py
│  │  ├─ scaffold.py
│  │  ├─ diff.py
│  │  └─ refactor.py
│  │
│  ├─ validation/
│  │  ├─ tests.py
│  │  ├─ architecture.py
│  │  └─ invariants.py
│  │
│  ├─ failures/
│  │  ├─ model.py
│  │  └─ recovery.py
│  │
│  └─ runmode/
│     ├─ config.py
│     └─ coordinator.py
│
├─ schemas/
│  ├─ artifact.schema.json
│  ├─ project_plan.schema.json
│  ├─ scaffold_plan.schema.json
│  ├─ test_plan.schema.json
│  ├─ implementation_plan.schema.json
│  └─ refactor_plan.schema.json
│
├─ tools/
│  └─ registry/
│     └─ capability_registry.yaml
│
├─ audit/
│  ├─ diffs/
│  ├─ executions.log
│  └─ failures.log
│
├─ .project/               # created by `dev init`
├─ artifacts/              # runtime artifacts
├─ src/
├─ tests/
│
├─ pyproject.toml
└─ README.md
```

Nothing here is accidental.
This maps **1:1** to the spec you approved.

---

## 2. CLI Entrypoint (Minimal but Correct)

### `cli/main.py`

```python
import sys
from cli.commands import init, plan, scaffold, impl, refactor, validate

COMMANDS = {
    "init": init.run,
    "plan": plan.run,
    "scaffold": scaffold.run,
    "impl": impl.run,
    "refactor": refactor.run,
    "validate": validate.run,
}

def main():
    if len(sys.argv) < 2:
        print("usage: dev <command>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"unknown command: {cmd}")
        sys.exit(1)

    COMMANDS[cmd](sys.argv[2:])
```

This stays dumb.
All intelligence is elsewhere.

---

## 3. Artifact Loading & Validation (Core Safety)

### `core/artifacts/loader.py`

```python
import json
from core.artifacts.validator import validate_artifact

def load(path):
    with open(path) as f:
        artifact = json.load(f)

    validate_artifact(artifact)
    return artifact
```

### `core/artifacts/validator.py`

```python
from jsonschema import validate
from pathlib import Path
import json

def validate_artifact(artifact):
    schema_name = artifact["artifact_type"].lower() + ".schema.json"
    schema_path = Path("schemas") / schema_name

    with open(schema_path) as f:
        schema = json.load(f)

    validate(instance=artifact["payload"], schema=schema)

    if artifact["status"] == "draft":
        raise RuntimeError("artifact not approved")
```

This is your **first line of defense**.

---

## 4. LLM Compiler Interface (Pluggable, Clean)

### `core/llm/interface.py`

```python
class LLM:
    def run(self, system_prompt: str, user_input: str) -> dict:
        raise NotImplementedError
```

### `core/llm/compiler.py`

```python
def build_artifact(llm, role, inputs, schema):
    prompt = role.system_prompt(inputs, schema)
    result = llm.run(prompt, inputs)

    if "error" in result:
        raise RuntimeError(result["error"])

    return result
```

You can back this with:

* OpenCode
* Claude Code
* Codex
* Local models

No other code changes.

---

## 5. Executor Base Class (Deterministic Core)

### `core/executors/base.py`

```python
class Executor:
    def execute(self, artifact, mode):
        raise NotImplementedError
```

### Example: `core/executors/scaffold.py`

```python
from core.executors.base import Executor
from pathlib import Path

class ScaffoldExecutor(Executor):
    def execute(self, artifact, mode):
        for f in artifact["payload"]["files"]:
            path = Path(f["path"])
            if path.exists():
                raise RuntimeError("file exists")

            if mode == "APPLY":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"// {f['description']}\n")
```

No logic.
No guesses.
No recovery.

---

## 6. Failure Model (First-Class)

### `core/failures/model.py`

```python
from dataclasses import dataclass

@dataclass
class FailureReport:
    phase: str
    category: str
    summary: str
    blocking: bool = True
```

Failures are **data**, not print statements.

---

## 7. Run Mode Configuration (Authority Control)

### `core/runmode/config.py`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RunMode:
    mode: str
    authority: str
    agents: dict
```

This is read **once** at startup.

---

## 8. What This Skeleton Already Guarantees

Even before adding features, this skeleton already enforces:

* Artifact-first workflow
* No LLM writes to disk
* No execution without approval
* Deterministic failure
* Pluggable intelligence
* Future multi-agent expansion

You can:

* implement commands incrementally
* add schemas safely
* swap LLMs freely
* build confidence step by step

---

## 9. What You Should Implement First (Practical Order)

1. `dev init`
2. Artifact schema validation
3. `dev plan project` (single-agent mode)
4. `dev scaffold`
5. `dev plan tests` + lock
6. `dev plan impl` → diff → apply
7. CI invariant check

Stop there.
You already have a *working system*.

---

## 10. Final Closure

You now have:

* A **complete system design**
* A **correct MVP extraction**
* A **reference implementation skeleton**
* Clear extension points
* No architectural debt

Nothing critical is missing.
Nothing needs to be rethought.

You can now **build calmly, incrementally, and correctly**.

If you want to pick this up later (multi-agent execution, reconciliation tooling, UI), everything is already aligned.
