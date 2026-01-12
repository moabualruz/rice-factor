# Milestone 04: LLM Compiler - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.2.0
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
- Run mode configuration schema
- Agent role definitions

### 2.2 Out of Scope
- Artifact storage (Milestone 02)
- CLI integration (Milestone 03)
- Code execution (Milestone 05)
- Multi-agent coordination (post-MVP)

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
| M04-U-008 | The system **shall** support configurable run modes via `run_mode.yaml` |
| M04-U-009 | Only one agent **shall** have authority to emit artifacts at a time |
| M04-U-010 | Blocking failures **shall** create FailureReport artifacts |

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

## 5. Run Modes

The system supports 5 run modes, configurable via `run_mode.yaml`. **MVP implements Mode A only.**

| Mode | Name | Description |
|------|------|-------------|
| A | Single Agent Control | One agent with full authority (MVP) |
| B | Orchestrator + Sub-Agents | One authoritative orchestrator + helpers |
| C | Multiple Generic Agents | N identical agents with voting/selection |
| D | Specialized Agents | Role-locked agents with single authority |
| E | Hybrid | Combines voting, specialists, orchestrator |

### 5.1 Run Mode Configuration Schema

```yaml
# .project/run_mode.yaml
mode: single_agent | orchestrator_with_specialists | voting | role_locked | hybrid

authority:
  agent: <agent_name>  # Only this agent can emit artifacts

agents:
  primary:
    role: orchestrator | planner | critic | domain_specialist | refactor_analyst | test_strategist
  planner:           # Optional for modes B, D, E
    role: planner
  critic:            # Optional for modes B, D, E
    role: critic
  # Additional agents as needed...

rules:
  - only_primary_emits_artifacts          # Always required
  - critics_must_review_before_approval   # Optional
  - specialists_answer_only_when_asked    # Optional
```

### 5.2 MVP Configuration (Mode A)

```yaml
mode: single_agent
authority:
  agent: primary
agents:
  primary:
    role: orchestrator
rules:
  - only_primary_emits_artifacts
```

---

## 6. Agent Roles

| Role | Description | Authority |
|------|-------------|-----------|
| Primary/Orchestrator | Emits artifacts, resolves conflicts, advances lifecycle | YES |
| Planner | Decomposes goals, suggests structure | NO |
| Critic | Reviews artifacts, identifies risks | NO |
| Domain Specialist | Narrow scope expertise (e.g., Rust, Security) | NO |
| Refactor Analyst | Evaluates refactor safety, identifies ripple effects | NO |
| Test Strategist | Evaluates TestPlan completeness | NO |

### 6.1 Universal Agent Contract

Every agent must obey:
1. Cannot write files directly
2. Cannot execute tools directly
3. Cannot approve artifacts
4. Cannot bypass CLI
5. Can only communicate via structured messages and artifact proposals

---

## 7. Event-Driven Requirements

| ID | Requirement |
|----|-------------|
| M04-E-001 | **As soon as** the LLM returns output, the system **shall** validate against JSON Schema |
| M04-E-002 | **As soon as** validation fails, the system **shall** reject and emit failure report |
| M04-E-003 | **As soon as** LLM returns `missing_information` error, the system **shall** halt for human input |

---

## 8. Unwanted Behavior Requirements

| ID | Requirement |
|----|-------------|
| M04-I-001 | **If** LLM outputs non-JSON, **then** the system **shall** reject the response |
| M04-I-002 | **If** LLM outputs code, **then** the system **shall** reject the response |
| M04-I-003 | **If** LLM outputs multiple artifacts, **then** the system **shall** reject the response |

---

## 9. Features

| Feature ID | Feature Name | Priority | Description |
|------------|--------------|----------|-------------|
| F04-01 | LLM Protocol Interface | P0 | Abstract LLMPort protocol in domain/ports |
| F04-02 | Claude Provider Adapter | P0 | Anthropic Claude API adapter |
| F04-03 | OpenAI Provider Adapter | P1 | OpenAI/Azure adapter |
| F04-04 | Compiler Pass Framework | P0 | Pass orchestration and registry |
| F04-05 | System Prompts | P0 | Global + pass-specific prompts |
| F04-06 | Structured Output Enforcement | P0 | JSON extraction and validation |
| F04-07 | Error Handling | P0 | LLM errors and FailureReport |

---

## 10. Success Criteria

- [ ] LLM generates valid artifacts for all pass types
- [ ] Invalid outputs are rejected
- [ ] Provider can be swapped via configuration
- [ ] Context usage is minimized per pass
- [ ] Deterministic outputs with same inputs
- [ ] Run mode configuration is validated on load
- [ ] FailureReport artifacts created for blocking failures

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-10 | SDD Process | Initial milestone requirements |
| 1.2.0 | 2026-01-10 | SDD Process | Added run modes, agent roles, FailureReport, feature descriptions |
