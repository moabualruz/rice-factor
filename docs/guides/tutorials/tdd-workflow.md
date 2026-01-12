# Test-Driven Development Workflow

This tutorial teaches you how Rice-Factor enforces TDD at the system level.

## Why System-Level TDD?

Traditional TDD relies on developer discipline:
1. Write a failing test
2. Write code to pass
3. Refactor

Rice-Factor enforces this at the system level:
1. TestPlan is **locked** before implementation
2. Automation **cannot modify** locked tests
3. If tests fail, **implementation must change**

This makes TDD non-negotiable - it's built into the workflow.

## The TDD Cycle in Rice-Factor

```
┌─────────────────────────────────────────────────────────────────┐
│  1. PLAN TESTS                                                  │
│     rice-factor plan tests                                      │
│     ↓                                                           │
│  2. REVIEW TESTS                                                │
│     Ensure tests cover requirements                             │
│     ↓                                                           │
│  3. APPROVE & LOCK                                              │
│     rice-factor approve <id>                                    │
│     rice-factor lock tests  ← TESTS BECOME IMMUTABLE            │
│     ↓                                                           │
│  4. IMPLEMENT                                                   │
│     rice-factor plan impl <file>                                │
│     rice-factor impl <file>                                     │
│     ↓                                                           │
│  5. RUN TESTS                                                   │
│     rice-factor test                                            │
│     ↓                                                           │
│     ┌─────────────┐                                             │
│     │ Tests pass? │                                             │
│     └──────┬──────┘                                             │
│            │                                                    │
│     ┌──────┴──────┐                                             │
│     │Yes         │No                                            │
│     ↓             ↓                                             │
│   DONE      FIX IMPLEMENTATION (not tests!)                     │
│             Go back to step 4                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Hands-On: TDD in Practice

### Step 1: Define Requirements

Create `.project/requirements.md`:

```markdown
# User Validation Module

## Requirements
- Validate email format (must contain @ and domain)
- Validate password strength (min 8 chars, 1 uppercase, 1 number)
- Validate username (alphanumeric, 3-20 chars)

## Edge Cases
- Empty strings should fail validation
- Whitespace-only strings should fail
- Unicode characters in usernames not allowed
```

### Step 2: Generate Test Plan

```bash
rice-factor plan tests
```

This creates a TestPlan like:

```json
{
  "payload": {
    "tests": [
      {
        "id": "test_valid_email",
        "target": "validate_email",
        "assertions": [
          "user@example.com returns True",
          "user@domain.co.uk returns True"
        ]
      },
      {
        "id": "test_invalid_email_no_at",
        "target": "validate_email",
        "assertions": [
          "userexample.com returns False"
        ]
      },
      {
        "id": "test_empty_email",
        "target": "validate_email",
        "assertions": [
          "empty string returns False"
        ]
      },
      {
        "id": "test_password_too_short",
        "target": "validate_password",
        "assertions": [
          "1234567 (7 chars) returns False"
        ]
      },
      {
        "id": "test_password_valid",
        "target": "validate_password",
        "assertions": [
          "Password1 returns True"
        ]
      }
    ]
  }
}
```

### Step 3: Review Tests Thoroughly

Before locking, ensure tests are:

**Complete**: Cover all requirements
```bash
# Cross-reference with requirements
# Each FR-* should have corresponding tests
```

**Correct**: Assertions match expected behavior
```bash
# Verify edge cases are covered
# Empty strings, boundary values, etc.
```

**Clear**: Test IDs and assertions are readable
```bash
# Will you understand these in 6 months?
```

### Step 4: Lock the Tests

```bash
rice-factor approve <test-plan-id>
rice-factor lock tests
# Type "LOCK" to confirm
```

**After this point:**
- Tests CANNOT be changed
- If a test is wrong, you must work around it
- Automation CANNOT modify tests

### Step 5: Implement to Pass Tests

```bash
# Plan implementation
rice-factor plan impl src/validators.py

# Generate code
rice-factor impl src/validators.py

# Review and apply
rice-factor review
rice-factor apply
```

### Step 6: Run Tests

```bash
rice-factor test
```

**If tests pass**: You're done!

**If tests fail**: Fix your implementation, not the tests!

### Step 7: Iterate Until Green

```bash
# View what failed
cat .project/artifacts/validation_results/*.json | jq '.payload'

# Fix the implementation
rice-factor plan impl src/validators.py
rice-factor impl src/validators.py
rice-factor review
rice-factor apply

# Test again
rice-factor test
```

## Why Lock Tests?

### Problem: Test Modification Temptation

Without locking, when tests fail:
1. Developer thinks "the test must be wrong"
2. Modifies test to match implementation
3. Tests pass, but requirements aren't met

### Solution: Locked Tests

With Rice-Factor:
1. Tests are locked before implementation
2. When tests fail, only implementation can change
3. Tests truly verify requirements

### Real-World Example

**Scenario**: Password validation test expects uppercase letter, but your implementation doesn't check for it.

**Without locking**:
```python
# Developer changes test from:
assert validate_password("password1") == False
# To:
assert validate_password("password1") == True  # Wrong!
```

**With Rice-Factor**:
```python
# Test is LOCKED - cannot change
# Must fix implementation:
def validate_password(password):
    # Add uppercase check
    if not any(c.isupper() for c in password):
        return False
```

## Advanced TDD Patterns

### Pattern 1: Test-First Planning

Ask Rice-Factor to generate TestPlan directly from requirements:

```bash
# Ensure requirements are detailed
rice-factor plan tests
```

The LLM will derive tests from your requirements.

### Pattern 2: Incremental Testing

Lock tests for one feature, implement, then add more:

```bash
# First iteration
rice-factor plan tests  # Generates initial tests
rice-factor lock tests
rice-factor impl <file>
rice-factor test  # Pass

# Later: Add new requirements
# (Requires new planning cycle)
```

### Pattern 3: Diagnose Failures

When tests fail, use diagnose:

```bash
rice-factor diagnose
```

This analyzes failures and suggests fixes for your implementation.

## Common TDD Questions

### "What if the test is genuinely wrong?"

If you locked a test with incorrect assertions:
1. Document the issue
2. Complete current implementation working around it
3. For next feature, start fresh with corrected requirements
4. Use override sparingly for critical fixes

### "Can I add more tests after locking?"

Not to the locked TestPlan. You would:
1. Complete current cycle
2. Update requirements for new features
3. Generate new TestPlan (new artifact)
4. Lock and implement

### "What about integration tests?"

Rice-Factor TestPlans cover unit tests. Integration tests can be:
- Added manually to your test suite
- Covered in a separate testing phase
- Defined in additional TestPlan artifacts

## TDD Best Practices

### 1. Write Detailed Requirements

The better your requirements, the better the generated tests:

```markdown
# Good
## FR-1: Email Validation
- Must contain exactly one @ symbol
- Must have non-empty local part (before @)
- Must have valid domain (letters, numbers, dots, hyphens)
- Maximum length 254 characters

# Bad
## FR-1: Validate emails
```

### 2. Review Tests Before Locking

Spend time reviewing. You can't change them later!

### 3. Small, Focused Tests

Each test should verify one thing:
- One assertion per test (when possible)
- Clear test names
- Independent tests

### 4. Trust the Process

When tests fail, resist the urge to blame the test. Ask:
- Does my implementation meet the requirement?
- Is there a bug in my code?
- Did I misunderstand the requirement?

## Summary

| TDD Step | Rice-Factor Command |
|----------|-------------------|
| Write tests | `rice-factor plan tests` |
| Review tests | Manual review |
| Lock tests | `rice-factor lock tests` |
| Implement | `rice-factor impl <file>` |
| Run tests | `rice-factor test` |
| Fix failures | Fix implementation, not tests |

## What's Next?

- [Configure LLM Providers](../how-to/configure-llm-providers.md) - Different LLMs for test generation
- [Common Errors](../troubleshooting/common-errors.md) - Test-related errors
- [CLI Reference](../../reference/cli/commands.md) - All testing commands
