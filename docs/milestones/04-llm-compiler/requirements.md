# Milestone 04: LLM Compiler - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.1.0
> **Status**: Pending

---

## 1. Milestone Objective

Implement the LLM Artifact Builder system that compiles human intent into structured artifacts. This is the "compiler" that transforms requirements into IR.

---

## 2. Scope

### 2.1 In Scope
- Abstract LLM interface (Protocol)
- Compiler pass definitions
- System prompts for each pass
- LLM provider adapters (Claude, OpenAI)
- Structured output enforcement
- Error handling for LLM failures

### 2.2 Out of Scope
- Artifact storage (Milestone 02)
- CLI integration (Milestone 03)
- Code execution (Milestone 05)

---

## 3. Ubiquitous Requirements

| ID | Requirement |
|----|-------------|
| M04-U-001 | The LLM **shall** output valid JSON only |
| M04-U-002 | The LLM **shall** output exactly one artifact per invocation |
| M04-U-003 | The LLM **shall** emit no explanations or reasoning |
| M04-U-004 | The LLM **shall** emit no source code |
| M04-U-005 | The LLM **shall** conform exactly to the provided JSON Schema |
| M04-U-006 | The LLM **shall** fail explicitly if information is missing |
| M04-U-007 | LLM temperature **shall** be 0.0-0.2 for determinism |

---

## 4. Compiler Passes

| Pass | Input | Output | Context Size |
|------|-------|--------|--------------|
| Project Planner | requirements.md, constraints.md, glossary.md | ProjectPlan | Large |
| Architecture Planner | ProjectPlan, constraints.md | ArchitecturePlan | Medium |
| Scaffold Planner | ProjectPlan, ArchitecturePlan | ScaffoldPlan | Medium |
| Test Designer | ProjectPlan, ScaffoldPlan, requirements.md | TestPlan | Medium |
| Implementation Planner | TestPlan, target file, interfaces | ImplementationPlan | **Tiny** |
| Refactor Planner | ArchitecturePlan, TestPlan, repo layout | RefactorPlan | Medium |

---

## 5. Event-Driven Requirements

| ID | Requirement |
|----|-------------|
| M04-E-001 | **As soon as** the LLM returns output, the system **shall** validate against JSON Schema |
| M04-E-002 | **As soon as** validation fails, the system **shall** reject and emit failure report |
| M04-E-003 | **As soon as** LLM returns `missing_information` error, the system **shall** halt for human input |

---

## 6. Unwanted Behavior Requirements

| ID | Requirement |
|----|-------------|
| M04-I-001 | **If** LLM outputs non-JSON, **then** the system **shall** reject the response |
| M04-I-002 | **If** LLM outputs code, **then** the system **shall** reject the response |
| M04-I-003 | **If** LLM outputs multiple artifacts, **then** the system **shall** reject the response |

---

## 7. Features

| Feature ID | Feature Name | Priority |
|------------|--------------|----------|
| F04-01 | LLM Protocol Interface | P0 |
| F04-02 | Claude Provider Adapter | P0 |
| F04-03 | OpenAI Provider Adapter | P1 |
| F04-04 | Compiler Pass Framework | P0 |
| F04-05 | System Prompts | P0 |
| F04-06 | Structured Output Enforcement | P0 |
| F04-07 | Error Handling | P0 |

---

## 8. Success Criteria

- [ ] LLM generates valid artifacts for all pass types
- [ ] Invalid outputs are rejected
- [ ] Provider can be swapped via configuration
- [ ] Context usage is minimized
- [ ] Deterministic outputs with same inputs

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone requirements |
