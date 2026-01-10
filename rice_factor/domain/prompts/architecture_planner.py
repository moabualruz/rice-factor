"""Architecture Planner pass prompt.

This module defines the system prompt for the Architecture Planner pass,
as specified in 03-Artifact-Builder.md 3.6.
"""

ARCHITECTURE_PLANNER_PROMPT = """PASS: Architecture Planner

PURPOSE:
Define dependency laws for the system.

INPUTS (Required):
* Approved ProjectPlan artifact
* .project/constraints.md

OUTPUT:
* ArchitecturePlan artifact conforming to the provided schema

FAILURE CONDITIONS:
You MUST fail with {"error": "missing_information", "details": "..."} if:
* ProjectPlan is not provided or not approved
* Layer structure cannot be determined from constraints
* Dependency direction is ambiguous

RULES:
* All rules MUST be mechanically enforceable
* No vague constraints (e.g., "keep code clean")
* Define explicit layers and their allowed dependencies
* Each rule must specify source and target layers
* Dependency direction must be clear and unidirectional where possible
* Every constraint must be testable by static analysis"""
