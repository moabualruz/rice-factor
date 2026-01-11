# Milestone 13: Multi-Agent Orchestration - Requirements

> **Document Type**: Milestone Requirements Specification
> **Version**: 1.0.0
> **Status**: Planned
> **Parent**: [Project Requirements](../../project/requirements.md)
> **Source**: [item-04-Multi-Agent-Coordination-Model-and-Run-Modes.md](../../raw/item-04-Multi-Agent-Coordination-Model-and-Run-Modes.md)

---

## 1. Milestone Objective

Implement multi-agent orchestration modes allowing different agent topologies and coordination patterns for artifact generation, review, and approval. This addresses sections 4.4-4.6 of the specification.

### 1.1 Problem Statement

Single-agent mode (Mode A) works but has limitations:
- No independent review/critique of generated artifacts
- Single point of failure for complex decisions
- No specialization for domain-specific work
- Limited parallelism in artifact generation

### 1.2 Solution Overview

Implement configurable run modes:
- **Mode A**: Solo Agent (current, default)
- **Mode B**: Orchestrator + Sub-agents
- **Mode C**: Voting Agents (consensus)
- **Mode D**: Role-Locked (specialized agents)
- **Mode E**: Hybrid (configurable per phase)

From the spec:
> "The system supports multiple agent topologies via `run_mode.yaml`"

---

## 2. Scope

### 2.1 In Scope

- Run mode configuration loading
- Orchestrator mode with sub-agents
- Voting/consensus mode
- Role-locked agents (Critic, Domain Specialist)
- Hybrid mode configuration
- Agent coordination protocol

### 2.2 Out of Scope

- Distributed agents across machines
- Agent learning/training
- Dynamic agent spawning
- Cost optimization between agents

---

## 3. Requirements

### 3.1 User Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M13-U-001 | User can select run mode via config | P0 | 4.6 |
| M13-U-002 | User can run with orchestrator pattern | P0 | 4.5.2 |
| M13-U-003 | User can run with voting pattern | P1 | 4.5.3 |
| M13-U-004 | User can assign agent roles | P1 | 4.4 |
| M13-U-005 | User can configure hybrid per phase | P2 | 4.5.5 |

### 3.2 System Requirements

| ID | Requirement | Priority | Source |
|----|-------------|----------|--------|
| M13-S-001 | System loads run_mode.yaml | P0 | 4.6 |
| M13-S-002 | Orchestrator delegates to sub-agents | P0 | 4.5.2 |
| M13-S-003 | Voting agents reach consensus | P1 | 4.5.3 |
| M13-S-004 | Critic agent reviews before approval | P0 | 4.4 |
| M13-S-005 | Domain Specialist handles specific areas | P1 | 4.4 |
| M13-S-006 | Agents coordinate via structured protocol | P0 | - |

### 3.3 Agent Roles (From Specification)

| Role | Description | Source |
|------|-------------|--------|
| Builder | Generates artifacts | 4.4 |
| Critic | Reviews artifacts for issues | 4.4 |
| Domain Specialist | Handles domain-specific decisions | 4.4 |
| Orchestrator | Coordinates other agents | 4.5.2 |
| Voter | Participates in consensus | 4.5.3 |

### 3.4 Run Modes (From Specification)

| Mode | Name | Description | Agents |
|------|------|-------------|--------|
| A | Solo | Single agent does everything | 1 |
| B | Orchestrator | Lead agent delegates work | 1 + N sub-agents |
| C | Voting | Agents vote on decisions | N equal agents |
| D | Role-Locked | Agents have fixed roles | N specialized agents |
| E | Hybrid | Different modes per phase | Configurable |

---

## 4. Features in This Milestone

| Feature ID | Feature Name | Priority | Status |
|------------|--------------|----------|--------|
| F13-01 | Run Mode Configuration | P0 | Pending |
| F13-02 | Orchestrator Mode | P0 | Pending |
| F13-03 | Voting Mode | P1 | Pending |
| F13-04 | Role-Locked Mode | P1 | Pending |
| F13-05 | Hybrid Mode | P2 | Pending |

---

## 5. Success Criteria

- [ ] `run_mode.yaml` configures agent topology
- [ ] Orchestrator mode delegates artifact generation
- [ ] Voting mode reaches consensus on decisions
- [ ] Critic role reviews artifacts before approval
- [ ] Hybrid mode allows different modes per phase
- [ ] Agent communication is structured and auditable

---

## 6. Dependencies

### 6.1 Internal Dependencies

| Dependency | Milestone | Reason |
|------------|-----------|--------|
| LLM Compiler | 04 | Agent implementation |
| Artifact System | 02 | Artifact handling |
| Approval System | 02 | Review workflow |

### 6.2 External Dependencies

| Dependency | Reason |
|------------|--------|
| Multiple LLM instances | Parallel agents |
| Message queue (optional) | Agent coordination |

---

## 7. Acceptance Criteria

### 7.1 Run Mode Configuration

```yaml
# .project/run_mode.yaml
mode: orchestrator

orchestrator:
  model: claude-3-opus
  max_delegation_depth: 2

sub_agents:
  - name: builder
    model: claude-3-sonnet
    capabilities: [plan, scaffold, implement]

  - name: critic
    model: claude-3-opus
    capabilities: [review, validate]
    reviews_before_approval: true
```

### 7.2 Orchestrator Mode

```bash
$ rice-factor plan project --mode orchestrator

[Orchestrator] Starting project planning...
[Orchestrator] Delegating to builder agent...
[Builder] Generating ProjectPlan artifact...
[Builder] ProjectPlan complete (15 milestones)
[Orchestrator] Delegating to critic agent...
[Critic] Reviewing ProjectPlan...
[Critic] Found 2 issues:
  - Milestone 3 has circular dependency
  - Missing success criteria for Milestone 7
[Orchestrator] Requesting revision from builder...
[Builder] Revising ProjectPlan...
[Builder] Issues resolved
[Critic] Approved with no issues
[Orchestrator] ProjectPlan ready for human approval

ProjectPlan saved: artifacts/project-plan-001.json
```

### 7.3 Voting Mode

```bash
$ rice-factor decide architecture --mode voting

[Voting] Architecture decision: Database choice
[Voting] Options: PostgreSQL, MongoDB, SQLite

[Agent 1] Vote: PostgreSQL (ACID compliance needed)
[Agent 2] Vote: PostgreSQL (Team expertise)
[Agent 3] Vote: MongoDB (Schema flexibility)

[Voting] Result: PostgreSQL (2/3 votes)
[Voting] Reasoning consolidated...

Decision recorded: PostgreSQL
Justification: ACID compliance and team expertise outweigh flexibility needs
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial requirements |
