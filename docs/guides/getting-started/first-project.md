# Your First Project

This tutorial walks you through creating your first Rice-Factor project from scratch.

## Overview

You'll learn the complete Rice-Factor workflow:
1. Initialize a project
2. Generate and approve plans
3. Create file scaffolding
4. Write and lock tests
5. Implement code
6. Apply changes

## Step 1: Initialize the Project

Create a new directory and initialize Rice-Factor:

```bash
# Create project directory
mkdir my-first-project
cd my-first-project

# Initialize Rice-Factor
rice-factor init
```

This creates the `.project/` directory with template files:

```
.project/
├── requirements.md      # Project requirements
├── constraints.md       # Technical constraints
├── glossary.md          # Domain terminology
├── non_goals.md         # Explicit non-goals
└── risks.md             # Known risks
```

### Fill in Project Context

Edit `.project/requirements.md` with your project description:

```markdown
# Project Requirements

## Description
A simple calculator library that performs basic arithmetic operations.

## Features
- Addition, subtraction, multiplication, division
- Support for integers and floats
- Error handling for division by zero
```

## Step 2: Generate a Project Plan

Ask Rice-Factor to analyze your requirements and generate a project plan:

```bash
rice-factor plan project
```

This creates a `ProjectPlan` artifact in `.project/artifacts/project_plans/`. The plan includes:
- Identified domains
- Module structure
- Constraints and architecture recommendations

### Review the Plan

View the generated artifact:

```bash
# List artifacts
ls .project/artifacts/project_plans/

# View the plan (it's JSON)
cat .project/artifacts/project_plans/*.json
```

### Approve the Plan

If the plan looks good, approve it:

```bash
# Get the artifact ID from the filename or list
rice-factor approve <artifact-id>
```

## Step 3: Create File Scaffolding

Generate the file structure based on your approved ProjectPlan:

```bash
rice-factor scaffold
```

This creates empty files with TODO comments:

```
src/
├── calculator/
│   ├── __init__.py
│   └── operations.py
tests/
└── test_operations.py
```

## Step 4: Generate and Lock Tests

### Generate TestPlan

```bash
rice-factor plan tests
```

This creates a `TestPlan` artifact defining all test cases based on your requirements.

### Review and Approve

```bash
# Review the test plan
cat .project/artifacts/test_plans/*.json

# Approve it
rice-factor approve <test-plan-id>
```

### Lock the Tests

**This is critical.** Locking the TestPlan makes it immutable - automation cannot modify tests.

```bash
rice-factor lock tests
```

You'll be asked to confirm by typing "LOCK". Once locked, tests become the source of truth.

## Step 5: Plan Implementation

Generate an implementation plan for a specific file:

```bash
rice-factor plan impl src/calculator/operations.py
```

This creates an `ImplementationPlan` artifact with step-by-step instructions for implementing the file.

## Step 6: Generate Implementation

Generate the actual code diff:

```bash
rice-factor impl src/calculator/operations.py
```

This creates a diff file in `.project/audit/diffs/` showing the changes to be made.

## Step 7: Review and Apply

### Review the Diff

```bash
rice-factor review
```

This shows the proposed changes and asks for your approval:
- `[a]` - Approve
- `[r]` - Reject
- `[s]` - Skip

### Apply Changes

After approval:

```bash
rice-factor apply
```

This applies the diff to your codebase using `git apply`.

## Step 8: Run Tests

Verify everything works:

```bash
rice-factor test
```

This runs your test suite and creates a `ValidationResult` artifact.

## Complete Workflow Summary

```bash
# 1. Initialize
rice-factor init
# Edit .project/requirements.md

# 2. Plan
rice-factor plan project
rice-factor approve <project-plan-id>

# 3. Scaffold
rice-factor scaffold

# 4. Test-first
rice-factor plan tests
rice-factor approve <test-plan-id>
rice-factor lock tests

# 5. Implement (repeat for each file)
rice-factor plan impl src/myfile.py
rice-factor impl src/myfile.py
rice-factor review
rice-factor apply

# 6. Validate
rice-factor test
```

## What's Next?

- [Core Concepts](concepts.md) - Understand the philosophy behind Rice-Factor
- [Artifact Lifecycle](../tutorials/artifact-lifecycle.md) - Deep dive into artifact states
- [TDD Workflow](../tutorials/tdd-workflow.md) - Master test-driven development
- [CLI Reference](../../reference/cli/commands.md) - Explore all commands

## Tips

1. **Always fill in requirements** - The more context in `.project/`, the better the plans
2. **Review before approving** - Artifacts define what gets built
3. **Lock tests early** - Locked tests ensure implementation stays on track
4. **Use `--dry-run`** - Preview changes before committing: `rice-factor scaffold --dry-run`
5. **Check the audit trail** - All actions are logged in `.project/audit/`
