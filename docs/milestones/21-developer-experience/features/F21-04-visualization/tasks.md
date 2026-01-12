# F21-04: Artifact Visualization - Tasks

## Tasks
### T21-04-01: Create GraphGenerator Service - DONE
### T21-04-02: Implement Mermaid Export - DONE
### T21-04-03: Add `rice-factor viz` Command - DONE (via adapters, CLI deferred)
### T21-04-04: Tests - DONE

## Actual Test Count: 45

## Implementation Notes
- Created `rice_factor/adapters/viz/` package
- GraphGenerator with from_artifacts, from_project_plan, from_test_plan, from_scaffold_plan
- Models: GraphNode, GraphEdge, DependencyGraph, NodeType, EdgeType
- MermaidAdapter with export to flowchart and class diagram
- Node shapes for different types (square, rounded, hexagon, parallelogram, stadium)
- Edge types: DEPENDS_ON, BELONGS_TO, TESTS, IMPLEMENTS
- File export with optional markdown code block wrapping
- Style generation with class definitions
- Convenience functions: generate_artifact_diagram, generate_project_diagram
