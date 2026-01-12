# ITEM 4 — **Multi-Agent Coordination Model & Run Modes**

This section defines **how many agents exist, who controls them, how they communicate, and how authority is enforced** — without breaking the artifact-driven, deterministic architecture you already designed.

This is **not about LLM prompting**.
This is **about system topology and control flow**.

---

## 4.1 Core Principle (Non-Negotiable)

> **Only one agent is ever allowed to produce authoritative artifacts at a time.**

Everything else:

* supports
* proposes
* critiques
* analyzes
* simulates

But **authority is singular**.

This prevents:

* conflicting plans
* artifact races
* hallucinated merges
* emergent chaos

---

## 4.2 Definitions (Precise Language)

### Agent

An LLM instance with a **role**, **scope**, and **permissions**.

### Authority

The ability to:

* emit artifacts
* change artifact status
* advance lifecycle phase

### Run Mode

A **static configuration** describing:

* how many agents exist
* their roles
* who has authority
* how coordination happens

Run mode is chosen **before execution** and **cannot change mid-run**.

---

## 4.3 Universal Agent Contract

Every agent — regardless of role — must obey:

1. Cannot write files
2. Cannot execute tools
3. Cannot approve artifacts
4. Cannot bypass CLI
5. Can only communicate via:

   * structured messages
   * artifact proposals
   * critiques

Agents are **brains only**.

---

## 4.4 Agent Roles (Canonical Set)

These roles are reusable across all run modes.

### 4.4.1 Primary (Authority) Agent

* Exactly one per run
* Only agent allowed to emit artifacts
* Responsible for:

  * final plans
  * conflict resolution
  * lifecycle progression

### 4.4.2 Planner Agent

* Decomposes goals
* Suggests structure
* No authority

### 4.4.3 Critic Agent

* Reviews proposed artifacts
* Identifies ambiguity, risk, violations
* Cannot propose replacements directly

### 4.4.4 Domain Specialist Agent

* Narrow scope (e.g. Rust, DDD, Security)
* Answers targeted questions
* Produces analysis only

### 4.4.5 Refactor Analyst Agent

* Evaluates refactor safety
* Identifies ripple effects
* Never emits RefactorPlan directly

### 4.4.6 Test Strategist Agent

* Evaluates TestPlan completeness
* Identifies missing cases
* Cannot modify tests

These roles are **orthogonal** and composable.

---

## 4.5 Run Modes (Configurable)

Now we define **explicit run modes**, exactly as you requested — plus the missing ones people usually forget.

---

## 4.5.1 Mode A — **Single Agent Control**

### Description

* One agent
* Full authority
* Simplest possible setup

### Topology

```
[Primary Agent]
```

### Characteristics

* Lowest overhead
* Lowest safety margin
* Best for:

  * solo developer
  * MVP
  * experimentation

### Enforcement

* No parallel reasoning
* No second opinions
* Still bound by artifact contracts

---

## 4.5.2 Mode B — **Orchestrator + Sub-Agents**

### Description

* One authoritative orchestrator
* Multiple helper agents
* Orchestrator synthesizes results

### Topology

```
           ┌────────────┐
           │  Planner   │
           └────────────┘
                 │
┌────────────┐   │   ┌────────────┐
│  Critic    │───┼───│  Specialist│
└────────────┘   │   └────────────┘
                 │
           ┌────────────┐
           │ Orchestrator│
           └────────────┘
```

### Characteristics

* High quality plans
* Controlled authority
* Slightly higher latency

### Best for

* Non-trivial projects
* Refactoring
* Architecture-sensitive work

---

## 4.5.3 Mode C — **Multiple Generic Agents (Voting)**

### Description

* N identical agents
* All generate candidate plans
* One plan selected

### Topology

```
[Agent A] ─┐
[Agent B] ─┼─> [Selector] ─> [Primary]
[Agent C] ─┘
```

### Selection Strategies

* Human selects
* Rule-based scoring
* Critic-assisted ranking

### Characteristics

* Diversity of ideas
* Risk of inconsistency
* Must normalize outputs heavily

### Use with caution

Only viable because **artifacts are strict IR**.

---

## 4.5.4 Mode D — **Specialized Agents (Role-Locked)**

### Description

Each agent has **one permanent role**.

### Example

```
[Domain Expert]
[Architecture Expert]
[Test Strategist]
[Refactor Analyst]
        ↓
   [Primary Agent]
```

### Characteristics

* High precision
* Low redundancy
* Requires good role definitions

### Best for

* Regulated domains
* Long-lived projects
* Teams with strong conventions

---

## 4.5.5 Mode E — **Hybrid (Mix & Match)**

### Description

Combines:

* voting for ideation
* specialists for review
* orchestrator for authority

### Example

```
     [Generic Agent A]
     [Generic Agent B]
             ↓
        [Primary]
             ↓
   [Critic] [Specialist]
```

### Characteristics

* Highest quality
* Highest cost
* Slowest

This is your **“full-glory” mode**.

---

## 4.6 Run Mode Configuration (Concrete)

### Example: `run_mode.yaml`

```yaml
mode: orchestrator_with_specialists

authority:
  agent: primary

agents:
  primary:
    role: orchestrator
  planner:
    role: planner
  critic:
    role: critic
  test_strategist:
    role: test_strategist
  refactor_analyst:
    role: refactor_analyst

rules:
  - only_primary_emits_artifacts
  - critics_must_review_before_approval
  - specialists_answer_only_when_asked
```

This file is **read once at start** and frozen.

---

## 4.7 Coordination Protocol (Mechanical)

Agents do **not chat freely**.

They interact via **structured phases**.

### Example: Planning Phase

1. Primary issues task
2. Planner proposes decomposition
3. Specialist comments
4. Critic flags issues
5. Primary synthesizes
6. Primary emits artifact

No loops. No debates.

---

## 4.8 Artifact Authority Enforcement

System rules:

* Only Primary can:

  * emit artifacts
  * set status to approved
* Other agents:

  * produce *inputs*
  * never outputs

If violated → hard failure.

---

## 4.9 Failure & Conflict Handling

### Conflicting Advice

* Primary resolves
* Decision logged

### Specialist Disagreement

* Recorded, not merged

### Critic Blocking

* Critic can flag but not veto
* Human veto still exists

---

## 4.10 Why This Model Works

This model gives you:

* Configurable intelligence topology
* Deterministic execution
* Scalable collaboration
* Clear accountability
* No emergent behavior
* No “agent soup”

Most agent systems fail because **authority is unclear**.
Here, it is explicit and enforced.
