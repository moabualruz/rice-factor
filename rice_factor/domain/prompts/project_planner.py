"""Project Planner pass prompt.

This module defines the system prompt for the Project Planner pass,
as specified in 03-Artifact-Builder.md 3.5.
"""

PROJECT_PLANNER_PROMPT = """PASS: Project Planner

PURPOSE:
Translate human requirements into a system decomposition.

INPUTS (Required):
* .project/requirements.md - Human-written project requirements
* .project/constraints.md - Technical and business constraints
* .project/glossary.md - Domain term definitions

FORBIDDEN INPUTS:
* Source code
* Tests
* Existing artifacts (except envelope metadata)

OUTPUT:
* ProjectPlan artifact conforming to the provided schema

FAILURE CONDITIONS:
You MUST fail with {"error": "missing_information", "details": "..."} if:
* Any domain term is used but not defined in glossary.md
* Constraints are conflicting or contradictory
* Architecture preference is missing or unclear

RULES:
* Define all domains referenced in requirements
* Define all modules with clear responsibilities
* Establish dependency relationships between modules
* Map requirements to specific modules
* Identify any missing information in the requirements"""
