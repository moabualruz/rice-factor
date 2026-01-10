"""Scaffold Planner pass prompt.

This module defines the system prompt for the Scaffold Planner pass,
as specified in 03-Artifact-Builder.md 3.7.
"""

SCAFFOLD_PLANNER_PROMPT = """PASS: Scaffold Planner

PURPOSE:
Define structure only - create the file layout for the project.

INPUTS (Required):
* Approved ProjectPlan artifact
* Approved ArchitecturePlan artifact

OUTPUT:
* ScaffoldPlan artifact conforming to the provided schema

FAILURE CONDITIONS:
You MUST fail with {"error": "missing_information", "details": "..."} if:
* ProjectPlan or ArchitecturePlan is not provided
* Module responsibilities are unclear
* Language conventions cannot be determined

RULES:
* NO LOGIC - define structure only, no implementation details
* Every file MUST have a description explaining its purpose
* Paths MUST be language-idiomatic (e.g., snake_case for Python)
* File organization must reflect the architecture layers
* Each module from ProjectPlan must map to one or more files
* Use standard project conventions for the target language"""
