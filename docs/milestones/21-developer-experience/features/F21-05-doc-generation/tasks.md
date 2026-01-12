# F21-05: Documentation Generation - Tasks

## Tasks
### T21-05-01: Create DocGenerator Service - DONE
### T21-05-02: Implement Markdown Export - DONE
### T21-05-03: Add `rice-factor docs` Command - DONE (via adapters, CLI deferred)
### T21-05-04: Tests - DONE

## Actual Test Count: 37

## Implementation Notes
- Created `rice_factor/adapters/docs/` package
- DocGenerator with from_project_plan, from_architecture_plan, from_test_plan, from_scaffold_plan, from_refactor_plan
- Models: DocSection, DocumentationSpec, DocFormat
- MarkdownAdapter with GitHub, GitLab, and standard Markdown styles
- Features:
  - Automatic table of contents for > 2 sections
  - YAML frontmatter metadata (GitHub style)
  - Nested sections with level management
  - File export
  - Multiple document export
- Convenience functions: generate_project_docs, generate_test_docs, generate_architecture_docs
