"""Unit tests for GlossaryValidator service."""

from pathlib import Path

import pytest

from rice_factor.domain.services.glossary_validator import (
    GlossaryParser,
    GlossaryValidationResult,
    GlossaryValidator,
    UndefinedTerm,
)


class TestGlossaryParser:
    """Tests for GlossaryParser."""

    def test_parse_table_format(self, tmp_path: Path) -> None:
        """Parser should extract terms from markdown tables."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """# Glossary

| Term | Definition |
|------|------------|
| Artifact | A structured plan document |
| TestPlan | Test specification artifact |
"""
        )

        parser = GlossaryParser()
        terms = parser.parse(glossary)

        assert "artifact" in terms
        assert "testplan" in terms

    def test_parse_acronyms_table(self, tmp_path: Path) -> None:
        """Parser should extract terms from acronyms table."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """# Glossary

## Acronyms

| Acronym | Expansion |
|---------|-----------|
| LLM | Large Language Model |
| CLI | Command Line Interface |
"""
        )

        parser = GlossaryParser()
        terms = parser.parse(glossary)

        assert "llm" in terms
        assert "cli" in terms

    def test_parse_empty_glossary(self, tmp_path: Path) -> None:
        """Parser should return empty set for empty glossary."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text("# Glossary\n\nNo terms defined yet.")

        parser = GlossaryParser()
        terms = parser.parse(glossary)

        assert len(terms) == 0

    def test_parse_missing_glossary(self, tmp_path: Path) -> None:
        """Parser should return empty set for missing file."""
        glossary = tmp_path / "glossary.md"
        # Don't create the file

        parser = GlossaryParser()
        terms = parser.parse(glossary)

        assert len(terms) == 0

    def test_parse_header_format(self, tmp_path: Path) -> None:
        """Parser should extract terms from headers."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """# Glossary

## Artifact
A structured plan document.

## TestPlan
Test specification artifact.
"""
        )

        parser = GlossaryParser()
        terms = parser.parse(glossary)

        assert "artifact" in terms
        assert "testplan" in terms

    def test_ignores_table_headers(self, tmp_path: Path) -> None:
        """Parser should ignore table header rows."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """# Glossary

| Term | Definition |
|------|------------|
| MyTerm | A real term |
"""
        )

        parser = GlossaryParser()
        terms = parser.parse(glossary)

        assert "term" not in terms
        assert "definition" not in terms
        assert "myterm" in terms


class TestGlossaryValidator:
    """Tests for GlossaryValidator."""

    def test_valid_text_with_defined_terms(self, tmp_path: Path) -> None:
        """Validator should pass when all terms are defined."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """| Term | Definition |
|------|------------|
| ProjectPlan | Project planning artifact |
| TestPlan | Test specification |
"""
        )

        validator = GlossaryValidator(glossary_path=glossary)
        result = validator.validate_text(
            "The ProjectPlan defines the TestPlan structure."
        )

        assert result.valid is True
        assert len(result.undefined_terms) == 0

    def test_detects_undefined_term(self, tmp_path: Path) -> None:
        """Validator should detect undefined PascalCase terms."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """| Term | Definition |
|------|------------|
| ProjectPlan | Project planning artifact |
"""
        )

        validator = GlossaryValidator(glossary_path=glossary)
        result = validator.validate_text(
            "The ProjectPlan uses DataIngestion module."
        )

        assert result.valid is False
        assert len(result.undefined_terms) == 1
        assert result.undefined_terms[0].term == "DataIngestion"

    def test_detects_multiple_undefined_terms(self, tmp_path: Path) -> None:
        """Validator should detect multiple undefined terms."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """| Term | Definition |
|------|------------|
| Known | A known term |
"""
        )

        validator = GlossaryValidator(glossary_path=glossary)
        result = validator.validate_text(
            "Uses UndefinedOne and UndefinedTwo components."
        )

        assert result.valid is False
        assert len(result.undefined_terms) == 2
        terms = {t.term for t in result.undefined_terms}
        assert "UndefinedOne" in terms
        assert "UndefinedTwo" in terms

    def test_ignores_common_words(self, tmp_path: Path) -> None:
        """Validator should ignore common English words."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text("# Empty glossary")

        validator = GlossaryValidator(glossary_path=glossary)
        # These look like PascalCase but are common words
        result = validator.validate_text("The JSON API uses HTTP protocol.")

        # Should not report JSON, API, HTTP as undefined
        assert result.valid is True

    def test_includes_location_in_errors(self, tmp_path: Path) -> None:
        """Validator should include location in error messages."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text("# Empty glossary")

        validator = GlossaryValidator(glossary_path=glossary)
        result = validator.validate_text(
            "Uses CustomModule.",
            location="ProjectPlan.description",
        )

        assert result.valid is False
        assert result.undefined_terms[0].location == "ProjectPlan.description"

    def test_suggests_similar_terms(self, tmp_path: Path) -> None:
        """Validator should suggest similar terms when available."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """| Term | Definition |
|------|------------|
| DataImport | Import data from sources |
"""
        )

        validator = GlossaryValidator(glossary_path=glossary)
        result = validator.validate_text("Uses DataImporter module.")

        assert result.valid is False
        # "dataimporter" should suggest "dataimport"
        assert result.undefined_terms[0].suggestion == "dataimport"


class TestGlossaryValidatorArtifacts:
    """Tests for artifact validation."""

    def test_validates_artifact_dict(self, tmp_path: Path) -> None:
        """Validator should validate artifact dictionary content."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """| Term | Definition |
|------|------------|
| ProjectPlan | Project planning artifact |
"""
        )

        validator = GlossaryValidator(glossary_path=glossary)
        artifact = {
            "name": "My Project",
            "description": "Uses CustomModule for processing",
        }
        result = validator.validate_artifact(artifact, "ProjectPlan")

        assert result.valid is False
        assert result.undefined_terms[0].term == "CustomModule"
        assert "ProjectPlan.description" in result.undefined_terms[0].location

    def test_validates_nested_artifact(self, tmp_path: Path) -> None:
        """Validator should validate nested artifact content."""
        glossary = tmp_path / "glossary.md"
        glossary.write_text(
            """| Term | Definition |
|------|------------|
| Known | A known term |
"""
        )

        validator = GlossaryValidator(glossary_path=glossary)
        artifact = {
            "modules": [
                {"name": "ModuleOne", "uses": "UnknownService"},
            ]
        }
        result = validator.validate_artifact(artifact)

        assert result.valid is False
        # Should find UnknownService and ModuleOne
        terms = {t.term for t in result.undefined_terms}
        assert "UnknownService" in terms
        assert "ModuleOne" in terms


class TestGlossaryValidationResult:
    """Tests for GlossaryValidationResult."""

    def test_format_errors_when_valid(self) -> None:
        """format_errors should indicate success when valid."""
        result = GlossaryValidationResult(valid=True, undefined_terms=[])
        formatted = result.format_errors()
        assert "All glossary terms are defined" in formatted

    def test_format_errors_shows_undefined_terms(self) -> None:
        """format_errors should list undefined terms."""
        result = GlossaryValidationResult(
            valid=False,
            undefined_terms=[
                UndefinedTerm(
                    term="CustomModule",
                    location="ProjectPlan.modules[0]",
                    suggestion=None,
                ),
            ],
        )
        formatted = result.format_errors()

        assert "CustomModule" in formatted
        assert "ProjectPlan.modules[0]" in formatted
        assert "Add to glossary.md" in formatted

    def test_format_errors_shows_suggestions(self) -> None:
        """format_errors should show suggestions when available."""
        result = GlossaryValidationResult(
            valid=False,
            undefined_terms=[
                UndefinedTerm(
                    term="DataImporter",
                    location="description",
                    suggestion="dataimport",
                ),
            ],
        )
        formatted = result.format_errors()

        assert 'Did you mean "dataimport"' in formatted


class TestGlossaryValidatorInit:
    """Tests for GlossaryValidator initialization."""

    def test_default_glossary_path(self) -> None:
        """Validator should default to .project/glossary.md."""
        validator = GlossaryValidator()
        assert validator.glossary_path == Path.cwd() / ".project" / "glossary.md"

    def test_custom_glossary_path(self, tmp_path: Path) -> None:
        """Validator should accept custom glossary path."""
        custom_path = tmp_path / "custom_glossary.md"
        custom_path.write_text("# Custom glossary")

        validator = GlossaryValidator(glossary_path=custom_path)
        assert validator.glossary_path == custom_path
