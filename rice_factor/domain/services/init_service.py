"""Project initialization service.

This module provides the InitService class for managing project initialization,
including creating the .project/ directory structure and template files.
"""

from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from rice_factor.domain.services.questionnaire import QuestionnaireResponse


# Template content generators
def _requirements_template(responses: QuestionnaireResponse) -> str:
    """Generate requirements.md content.

    Args:
        responses: Questionnaire responses

    Returns:
        Template content with responses filled in
    """
    problem = responses.get("problem", "[Not provided]")
    return f"""# Project Requirements

## Problem Statement

{problem}

## Functional Requirements

<!-- List the functional requirements for your project -->

- [ ] FR-001: [Requirement description]
- [ ] FR-002: [Requirement description]

## Non-Functional Requirements

<!-- List non-functional requirements (performance, security, etc.) -->

- [ ] NFR-001: [Requirement description]

## Success Criteria

<!-- Define what success looks like for this project -->

1. [Success criterion 1]
2. [Success criterion 2]
"""


def _constraints_template(responses: QuestionnaireResponse) -> str:
    """Generate constraints.md content.

    Args:
        responses: Questionnaire responses

    Returns:
        Template content with responses filled in
    """
    architecture = responses.get("architecture", "[Not specified]")
    languages = responses.get("languages", "[Not specified]")
    return f"""# Technical Constraints

## Architectural Style

{architecture}

## Allowed Languages

{languages}

## Technology Stack

<!-- List required technologies, frameworks, and tools -->

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | {languages} | Project requirement |
| Architecture | {architecture} | Project requirement |

## External Dependencies

<!-- List any external services, APIs, or systems this project depends on -->

## Compliance Requirements

<!-- List any compliance, regulatory, or security requirements -->
"""


def _glossary_template(responses: QuestionnaireResponse) -> str:  # noqa: ARG001
    """Generate glossary.md content.

    Args:
        responses: Questionnaire responses (unused but kept for consistency)

    Returns:
        Template content
    """
    return """# Domain Glossary

## Terms

<!-- Define domain-specific terms used in this project -->

| Term | Definition |
|------|------------|
| [Term 1] | [Definition] |
| [Term 2] | [Definition] |

## Acronyms

| Acronym | Expansion |
|---------|-----------|
| [ABC] | [Always Be Coding] |

## Context

<!-- Additional context about the domain -->
"""


def _non_goals_template(responses: QuestionnaireResponse) -> str:  # noqa: ARG001
    """Generate non_goals.md content.

    Args:
        responses: Questionnaire responses (unused but kept for consistency)

    Returns:
        Template content
    """
    return """# Non-Goals and Out of Scope

## Explicit Non-Goals

<!-- Things this project will NOT do -->

1. [Non-goal 1]
2. [Non-goal 2]

## Out of Scope

<!-- Features or functionality explicitly excluded from scope -->

- [Out of scope item 1]
- [Out of scope item 2]

## Deferred

<!-- Items that may be addressed in future iterations -->

| Item | Reason for Deferral |
|------|---------------------|
| [Deferred item] | [Reason] |
"""


def _risks_template(responses: QuestionnaireResponse) -> str:
    """Generate risks.md content.

    Args:
        responses: Questionnaire responses

    Returns:
        Template content with responses filled in
    """
    failures = responses.get("failures", "[Not provided]")
    return f"""# Risk Register

## Unacceptable Failures

{failures}

## Risk Assessment

| ID | Risk | Probability | Impact | Mitigation |
|----|------|-------------|--------|------------|
| R-001 | [Risk description] | Low/Med/High | Low/Med/High | [Mitigation strategy] |

## Assumptions

<!-- List assumptions that, if wrong, could impact the project -->

1. [Assumption 1]
2. [Assumption 2]

## Dependencies

<!-- External dependencies that could pose risks -->

| Dependency | Risk | Contingency |
|------------|------|-------------|
| [Dependency] | [Potential risk] | [Contingency plan] |
"""


# Mapping of file names to template generators
TEMPLATE_GENERATORS: dict[str, Callable[[QuestionnaireResponse], str]] = {
    "requirements.md": _requirements_template,
    "constraints.md": _constraints_template,
    "glossary.md": _glossary_template,
    "non_goals.md": _non_goals_template,
    "risks.md": _risks_template,
}


class IntakeValidationResult:
    """Result of intake file validation.

    Attributes:
        is_valid: Whether all required intake files are populated.
        empty_files: List of empty or missing files.
        populated_files: List of populated files.
    """

    def __init__(
        self,
        is_valid: bool,
        empty_files: list[str] | None = None,
        populated_files: list[str] | None = None,
    ) -> None:
        """Initialize validation result.

        Args:
            is_valid: Whether validation passed.
            empty_files: List of empty or missing file names.
            populated_files: List of populated file names.
        """
        self.is_valid = is_valid
        self.empty_files = empty_files or []
        self.populated_files = populated_files or []


class InitService:
    """Service for project initialization.

    Handles creating the .project/ directory structure and template files
    based on questionnaire responses.
    """

    PROJECT_DIR: ClassVar[str] = ".project"
    ARTIFACTS_DIR: ClassVar[str] = "artifacts"
    AUDIT_DIR: ClassVar[str] = "audit"
    TEMPLATE_FILES: ClassVar[list[str]] = [
        "requirements.md",
        "constraints.md",
        "glossary.md",
        "non_goals.md",
        "risks.md",
    ]
    # Required intake files that must be non-empty for validation
    REQUIRED_INTAKE_FILES: ClassVar[list[str]] = [
        "requirements.md",
        "constraints.md",
        "glossary.md",
    ]

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize the service.

        Args:
            project_root: Root directory of the project. Defaults to current directory.
        """
        self.project_root = project_root or Path.cwd()

    @property
    def project_dir(self) -> Path:
        """Get the .project/ directory path."""
        return self.project_root / self.PROJECT_DIR

    @property
    def artifacts_dir(self) -> Path:
        """Get the artifacts/ directory path."""
        return self.project_root / self.ARTIFACTS_DIR

    @property
    def audit_dir(self) -> Path:
        """Get the audit/ directory path."""
        return self.project_root / self.AUDIT_DIR

    def is_initialized(self) -> bool:
        """Check if the project is already initialized.

        Returns:
            True if .project/ directory exists and is a directory
        """
        return self.project_dir.exists() and self.project_dir.is_dir()

    def initialize(
        self,
        responses: QuestionnaireResponse | None = None,
        force: bool = False,
    ) -> list[Path]:
        """Initialize the project with .project/ directory and template files.

        Also creates artifacts/ and audit/ directories for artifact storage
        and audit trail.

        Args:
            responses: Questionnaire responses for template generation.
                      If None, uses empty responses.
            force: If True, overwrite existing files

        Returns:
            List of paths to created files

        Raises:
            FileExistsError: If already initialized and force=False
        """
        if self.is_initialized() and not force:
            raise FileExistsError(
                f"Project already initialized at {self.project_dir}. "
                "Use --force to overwrite."
            )

        # Create .project/ directory
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Create artifacts/ directory for artifact storage
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Create audit/ directory for audit trail
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Use empty responses if none provided
        if responses is None:
            responses = QuestionnaireResponse()

        # Generate template files
        created_files: list[Path] = []
        for filename in self.TEMPLATE_FILES:
            file_path = self.project_dir / filename
            generator = TEMPLATE_GENERATORS.get(filename)
            if generator:
                content = generator(responses)
                file_path.write_text(content, encoding="utf-8")
                created_files.append(file_path)

        return created_files

    def get_template_content(
        self,
        filename: str,
        responses: QuestionnaireResponse | None = None,
    ) -> str:
        """Get the content for a template file without writing it.

        Args:
            filename: Name of the template file
            responses: Questionnaire responses for template generation

        Returns:
            Generated template content

        Raises:
            ValueError: If filename is not a known template
        """
        generator = TEMPLATE_GENERATORS.get(filename)
        if generator is None:
            raise ValueError(f"Unknown template file: {filename}")

        if responses is None:
            responses = QuestionnaireResponse()

        return generator(responses)

    def validate_intake_files(self) -> IntakeValidationResult:
        """Validate that required intake files are non-empty.

        Checks that requirements.md, constraints.md, and glossary.md exist
        and have non-trivial content (more than just the template markers).

        Returns:
            IntakeValidationResult with validation status and file details.
        """
        empty_files: list[str] = []
        populated_files: list[str] = []

        for filename in self.REQUIRED_INTAKE_FILES:
            file_path = self.project_dir / filename
            if not file_path.exists():
                empty_files.append(filename)
                continue

            content = file_path.read_text(encoding="utf-8").strip()
            if not content:
                empty_files.append(filename)
                continue

            # Check if content is just the template (still has placeholder markers)
            # A file is considered "populated" if it doesn't contain placeholder markers
            # or has significant custom content beyond the template
            if self._is_template_only(content):
                empty_files.append(filename)
            else:
                populated_files.append(filename)

        is_valid = len(empty_files) == 0
        return IntakeValidationResult(
            is_valid=is_valid,
            empty_files=empty_files,
            populated_files=populated_files,
        )

    def _is_template_only(self, content: str) -> bool:
        """Check if content is still just the template.

        A file is considered "template only" if it still contains
        placeholder markers like [Not provided] or [Not specified].

        Args:
            content: File content to check.

        Returns:
            True if content appears to be unchanged template.
        """
        # These markers indicate the file hasn't been customized
        template_markers = [
            "[Not provided]",
            "[Not specified]",
            "[Requirement description]",
            "[Term 1]",
            "[Definition]",
        ]
        return any(marker in content for marker in template_markers)
