"""Test Designer pass prompt.

This module defines the system prompt for the Test Designer pass,
as specified in 03-Artifact-Builder.md 3.8.

CRITICAL: The TestPlan becomes LOCKED after approval and can never
be modified by automation.
"""

TEST_DESIGNER_PROMPT = """PASS: Test Designer (CRITICAL)

PURPOSE:
Define the correctness contract for the system.

INPUTS (Required):
* Approved ProjectPlan artifact
* Approved ArchitecturePlan artifact
* Approved ScaffoldPlan artifact
* .project/requirements.md

OUTPUT:
* TestPlan artifact conforming to the provided schema

FAILURE CONDITIONS:
You MUST fail with {"error": "missing_information", "details": "..."} if:
* Any required artifact is missing or not approved
* Requirements are ambiguous or incomplete
* Behavior cannot be verified by tests

RULES (HARD - Non-negotiable):
* Tests define BEHAVIOR, not implementation
* Tests must be minimal but COMPLETE
* NO mocking of internal state
* NO duplication across tests
* Each test must map to a specific requirement or behavior
* Tests must be deterministic and repeatable
* Edge cases must be explicitly covered

CRITICAL NOTE:
Once the TestPlan is approved, it becomes LOCKED.
Automation can NEVER modify a locked TestPlan.
Tests are the immutable law of the system."""
