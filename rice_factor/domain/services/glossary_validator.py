"""Glossary term validation service.

This module provides the GlossaryValidator class for validating that domain
terms used in artifacts are properly defined in the project glossary.

The validator ensures LLM outputs don't introduce undefined domain terminology,
maintaining consistency across the project.
"""

import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from pathlib import Path
from typing import Any, ClassVar


@dataclass
class UndefinedTerm:
    """Represents an undefined term found during validation.

    Attributes:
        term: The undefined term that was found.
        location: Where the term was found (e.g., "ProjectPlan.description").
        suggestion: Closest matching term from glossary, if any.
    """

    term: str
    location: str
    suggestion: str | None = None


@dataclass
class GlossaryValidationResult:
    """Result of glossary term validation.

    Attributes:
        valid: Whether all terms are defined.
        undefined_terms: List of undefined terms found.
    """

    valid: bool
    undefined_terms: list[UndefinedTerm] = field(default_factory=list)

    def format_errors(self) -> str:
        """Format errors for CLI display.

        Returns:
            Formatted string describing undefined terms.
        """
        if self.valid:
            return "All glossary terms are defined."

        lines = [
            "Undefined glossary terms detected:",
            "",
            "The following terms are used but not defined in .project/glossary.md:",
            "",
        ]

        for term in self.undefined_terms:
            lines.append(f'  - "{term.term}" in {term.location}')
            if term.suggestion:
                lines.append(f'    Suggestion: Did you mean "{term.suggestion}"?')
            else:
                lines.append(
                    "    No close match found. Add to glossary.md or use existing term."
                )
            lines.append("")

        lines.append("Add missing terms to glossary.md before continuing.")
        return "\n".join(lines)


class GlossaryParser:
    """Parses glossary.md to extract defined terms.

    Supports two markdown formats:
    1. Table format: | Term | Definition |
    2. Header format: ## TermName
    """

    def parse(self, glossary_path: Path) -> set[str]:
        """Extract defined terms from glossary.md.

        Args:
            glossary_path: Path to glossary.md file.

        Returns:
            Set of defined term names (normalized to lowercase).
        """
        if not glossary_path.exists():
            return set()

        content = glossary_path.read_text(encoding="utf-8")
        terms: set[str] = set()

        # Extract from tables (| Term | Definition |)
        # Skip header rows that contain "Term", "Acronym", "---"
        table_pattern = r"^\|\s*([^|]+?)\s*\|"
        for match in re.finditer(table_pattern, content, re.MULTILINE):
            term = match.group(1).strip()
            # Skip table headers and separators
            if (
                term.lower() not in ("term", "acronym", "---", "definition")
                and term
                and not term.startswith("-")
            ):
                terms.add(term.lower())

        # Extract from headers (## TermName)
        header_pattern = r"^##\s+(\w+)"
        for match in re.finditer(header_pattern, content, re.MULTILINE):
            term = match.group(1).strip()
            # Skip common section headers
            if term.lower() not in ("terms", "acronyms", "context"):
                terms.add(term.lower())

        return terms


class GlossaryValidator:
    """Validates that domain terms used in text are defined in glossary.

    This validator enforces glossary consistency during execution phase,
    ensuring LLM-generated artifacts don't introduce undefined terminology.
    """

    # Pattern for PascalCase terms (likely domain concepts)
    DOMAIN_TERM_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b"
    )

    # Pattern for UPPERCASE acronyms
    ACRONYM_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b([A-Z]{2,})\b")

    # Common words to ignore (not domain terms)
    IGNORE_TERMS: ClassVar[set[str]] = {
        # Common sentence starters
        "the",
        "this",
        "that",
        "when",
        "where",
        "what",
        "which",
        "how",
        "why",
        # Common programming terms
        "todo",
        "fixme",
        "note",
        "warning",
        "error",
        # Common abbreviations
        "api",
        "url",
        "uri",
        "http",
        "https",
        "json",
        "xml",
        "html",
        "css",
        "sql",
        "cli",
        "gui",
        # Common words that look like PascalCase
        "readme",
        "changelog",
        "license",
    }

    def __init__(self, glossary_path: Path | None = None) -> None:
        """Initialize the validator.

        Args:
            glossary_path: Path to glossary.md. Defaults to .project/glossary.md in CWD.
        """
        if glossary_path is None:
            self.glossary_path = Path.cwd() / ".project" / "glossary.md"
        else:
            self.glossary_path = glossary_path

        parser = GlossaryParser()
        self.defined_terms = parser.parse(self.glossary_path)

    def validate_text(
        self, text: str, location: str = "text"
    ) -> GlossaryValidationResult:
        """Validate text for undefined domain terms.

        Args:
            text: Text to validate.
            location: Description of where the text came from.

        Returns:
            GlossaryValidationResult with any undefined terms found.
        """
        undefined: list[UndefinedTerm] = []

        # Extract potential domain terms
        extracted_terms = self._extract_terms(text)

        for term in extracted_terms:
            term_lower = term.lower()

            # Skip if it's a common word to ignore
            if term_lower in self.IGNORE_TERMS:
                continue

            # Check if term is defined in glossary
            if term_lower not in self.defined_terms:
                # Find suggestion
                suggestion = self._find_suggestion(term_lower)
                undefined.append(
                    UndefinedTerm(
                        term=term,
                        location=location,
                        suggestion=suggestion,
                    )
                )

        return GlossaryValidationResult(
            valid=len(undefined) == 0,
            undefined_terms=undefined,
        )

    def validate_artifact(
        self, artifact_dict: dict[str, Any], artifact_type: str = "artifact"
    ) -> GlossaryValidationResult:
        """Validate artifact content for undefined terms.

        Args:
            artifact_dict: Artifact payload as dictionary.
            artifact_type: Type name for location reporting.

        Returns:
            GlossaryValidationResult with any undefined terms found.
        """
        undefined: list[UndefinedTerm] = []

        # Recursively extract text from artifact and validate
        self._validate_dict(artifact_dict, artifact_type, undefined)

        return GlossaryValidationResult(
            valid=len(undefined) == 0,
            undefined_terms=undefined,
        )

    def _validate_dict(
        self,
        data: dict[str, Any] | list[Any] | str,
        path: str,
        undefined: list[UndefinedTerm],
    ) -> None:
        """Recursively validate dictionary/list/string content.

        Args:
            data: Data to validate.
            path: Current path for location reporting.
            undefined: List to append undefined terms to.
        """
        if isinstance(data, str):
            result = self.validate_text(data, path)
            undefined.extend(result.undefined_terms)
        elif isinstance(data, dict):
            for key, value in data.items():
                self._validate_dict(value, f"{path}.{key}", undefined)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._validate_dict(item, f"{path}[{i}]", undefined)

    def _extract_terms(self, text: str) -> set[str]:
        """Extract potential domain terms from text.

        Args:
            text: Text to extract terms from.

        Returns:
            Set of potential domain terms.
        """
        terms: set[str] = set()

        # Extract PascalCase terms (e.g., ProjectPlan, TestRunner)
        for match in self.DOMAIN_TERM_PATTERN.finditer(text):
            terms.add(match.group(1))

        # Extract UPPERCASE acronyms (e.g., API, LLM)
        for match in self.ACRONYM_PATTERN.finditer(text):
            terms.add(match.group(1))

        return terms

    def _find_suggestion(self, term: str) -> str | None:
        """Find the closest matching term from glossary.

        Args:
            term: Undefined term to find suggestion for.

        Returns:
            Closest matching term, or None if no good match.
        """
        if not self.defined_terms:
            return None

        matches = get_close_matches(term, self.defined_terms, n=1, cutoff=0.6)
        return matches[0] if matches else None
