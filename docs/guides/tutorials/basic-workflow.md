# Basic Workflow Tutorial

This hands-on tutorial teaches you the complete Rice-Factor workflow by building a simple project.

## What You'll Build

A temperature converter library with:
- Celsius to Fahrenheit conversion
- Fahrenheit to Celsius conversion
- Kelvin conversions
- Input validation

## Prerequisites

- Rice-Factor installed ([Installation Guide](../getting-started/installation.md))
- API key configured (Claude or OpenAI)
- ~30 minutes

## Step 1: Project Setup

### Create Project Directory

```bash
mkdir temp-converter
cd temp-converter
git init
```

### Initialize Rice-Factor

```bash
rice-factor init
```

You'll see:
```
Created .project/ directory
Created .project/requirements.md
Created .project/constraints.md
Created .project/glossary.md
Created .project/non_goals.md
Created .project/risks.md
```

## Step 2: Define Requirements

Edit `.project/requirements.md`:

```markdown
# Temperature Converter

## Description
A Python library for converting temperatures between different scales.

## Functional Requirements

### FR-1: Celsius to Fahrenheit
Convert Celsius temperatures to Fahrenheit using: F = (C × 9/5) + 32

### FR-2: Fahrenheit to Celsius
Convert Fahrenheit temperatures to Celsius using: C = (F - 32) × 5/9

### FR-3: Kelvin Conversions
- Celsius to Kelvin: K = C + 273.15
- Kelvin to Celsius: C = K - 273.15

### FR-4: Input Validation
- Reject temperatures below absolute zero (-273.15°C, -459.67°F, 0K)
- Raise ValueError with descriptive message

## Non-Functional Requirements
- Pure functions (no side effects)
- Type hints on all functions
- 100% test coverage on conversion logic
```

Edit `.project/constraints.md`:

```markdown
# Technical Constraints

## Language
- Python 3.11+
- No external dependencies (stdlib only)

## Architecture
- Single module: `temp_converter.py`
- Functional style (pure functions)

## Testing
- pytest for test runner
- Tests in `tests/` directory
```

## Step 3: Generate Project Plan

```bash
rice-factor plan project
```

Output:
```
Generating ProjectPlan...
✓ Created artifact: project_plans/abc123.json
```

### Review the Plan

```bash
# View the artifact
cat .project/artifacts/project_plans/*.json | python -m json.tool
```

The plan should include:
- Domain: "temperature_conversion"
- Module: "temp_converter"
- Constraints from your requirements

### Approve the Plan

```bash
rice-factor approve abc123
```

Output:
```
Artifact abc123 approved
Status: DRAFT → APPROVED
```

## Step 4: Create Scaffolding

```bash
rice-factor scaffold
```

This creates:
```
temp_converter/
├── __init__.py
└── converter.py      # TODO: Implement conversions

tests/
└── test_converter.py # TODO: Implement tests
```

## Step 5: Generate Test Plan

This is the critical TDD step - tests come before implementation.

```bash
rice-factor plan tests
```

### Review Tests

The TestPlan includes test definitions like:

```json
{
  "tests": [
    {
      "id": "test_celsius_to_fahrenheit_freezing",
      "target": "celsius_to_fahrenheit",
      "assertions": ["0°C equals 32°F"]
    },
    {
      "id": "test_celsius_to_fahrenheit_boiling",
      "target": "celsius_to_fahrenheit",
      "assertions": ["100°C equals 212°F"]
    },
    {
      "id": "test_below_absolute_zero_raises",
      "target": "celsius_to_fahrenheit",
      "assertions": ["ValueError raised for -300°C"]
    }
  ]
}
```

### Approve and Lock

```bash
# Approve
rice-factor approve <test-plan-id>

# Lock (PERMANENT!)
rice-factor lock tests
```

Type "LOCK" when prompted. Once locked, tests cannot be modified by automation.

## Step 6: Implement the Converter

### Plan Implementation

```bash
rice-factor plan impl temp_converter/converter.py
```

This creates an ImplementationPlan with steps like:
1. Define `celsius_to_fahrenheit(celsius: float) -> float`
2. Define `fahrenheit_to_celsius(fahrenheit: float) -> float`
3. Define Kelvin conversion functions
4. Add input validation

### Generate Code

```bash
rice-factor impl temp_converter/converter.py
```

This generates a diff in `.project/audit/diffs/`.

### Review Changes

```bash
rice-factor review
```

You'll see the proposed code:

```python
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    if celsius < -273.15:
        raise ValueError(f"Temperature {celsius}°C is below absolute zero")
    return (celsius * 9/5) + 32
```

Press `[a]` to approve.

### Apply Changes

```bash
rice-factor apply
```

The code is now in your file!

## Step 7: Run Tests

```bash
rice-factor test
```

If tests pass:
```
✓ All tests passed
ValidationResult created: validation_results/xyz789.json
```

If tests fail:
```
✗ 2 tests failed
See ValidationResult for details
```

Fix the implementation and re-run. Remember: tests are locked, so you must fix the code, not the tests!

## Step 8: Complete Remaining Files

Repeat the implementation cycle for any remaining files:

```bash
# For each file
rice-factor plan impl <file>
rice-factor impl <file>
rice-factor review
rice-factor apply
rice-factor test
```

## Final Project Structure

```
temp-converter/
├── .project/
│   ├── artifacts/
│   │   ├── project_plans/
│   │   ├── scaffold_plans/
│   │   ├── test_plans/
│   │   ├── implementation_plans/
│   │   └── validation_results/
│   ├── audit/
│   │   └── diffs/
│   ├── requirements.md
│   ├── constraints.md
│   ├── glossary.md
│   ├── non_goals.md
│   └── risks.md
├── temp_converter/
│   ├── __init__.py
│   └── converter.py
└── tests/
    └── test_converter.py
```

## Key Takeaways

1. **Requirements first** - Fill in `.project/` before planning
2. **Plans before code** - Generate and approve plans
3. **Tests before implementation** - Lock tests, then implement
4. **Review everything** - Approve diffs before applying
5. **Trust the audit trail** - Everything is logged and replayable

## What's Next?

- [Artifact Lifecycle](artifact-lifecycle.md) - Understand states in depth
- [TDD Workflow](tdd-workflow.md) - Advanced TDD patterns
- [Configure LLM Providers](../how-to/configure-llm-providers.md) - Use different LLMs

## Troubleshooting

### "TestPlan must be locked"
You're trying to implement before locking tests. Run `rice-factor lock tests`.

### "Artifact not found"
Use the full artifact ID or path. Run `ls .project/artifacts/` to see available artifacts.

### "Tests failed"
Read the ValidationResult for details. Fix your implementation (not tests!) and re-run.
