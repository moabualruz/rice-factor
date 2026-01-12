# Milestone 13: Multi-Agent Orchestration - Design

> **Document Type**: Milestone Design Specification
> **Version**: 1.0.0
> **Status**: Draft
> **Parent**: [Project Design](../../project/design.md)

---

## 1. Design Overview

### 1.1 Architecture Approach

Multi-agent orchestration adds a coordination layer above the existing LLM adapter, enabling multiple agents to collaborate on artifact generation.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│              rice-factor plan project                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Run Mode Router                           │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │  Solo    │ │Orchestr- │ │  Voting  │ │  Hybrid  │        │
│  │  (A)     │ │  ator(B) │ │   (C)    │ │   (E)    │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Coordinator                          │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Agent Pool                            ││
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐         ││
│  │  │Builder │  │ Critic │  │Specialist│ │ Voter  │         ││
│  │  └────────┘  └────────┘  └────────┘  └────────┘         ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Message Protocol                            ││
│  │  { task, context, constraints, response_schema }        ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      LLM Adapters                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │  Claude  │  │  OpenAI  │  │  Local   │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 File Organization

```
rice_factor/
├── domain/
│   ├── models/
│   │   └── agent.py                   # Agent, Role, Message
│   ├── ports/
│   │   └── coordinator.py             # CoordinatorPort
│   └── services/
│       └── run_mode_router.py         # Mode selection
├── adapters/
│   └── agents/
│       ├── coordinator.py             # AgentCoordinator
│       ├── solo_mode.py               # Mode A
│       ├── orchestrator_mode.py       # Mode B
│       ├── voting_mode.py             # Mode C
│       ├── role_locked_mode.py        # Mode D
│       └── hybrid_mode.py             # Mode E
└── config/
    └── run_mode_config.py             # run_mode.yaml loader
```

---

## 2. Domain Models

### 2.1 Agent Models

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class AgentRole(str, Enum):
    """Roles an agent can assume."""

    BUILDER = "builder"           # Generates artifacts
    CRITIC = "critic"             # Reviews artifacts
    DOMAIN_SPECIALIST = "domain_specialist"  # Domain expertise
    ORCHESTRATOR = "orchestrator" # Coordinates agents
    VOTER = "voter"              # Participates in voting


class AgentCapability(str, Enum):
    """Capabilities an agent may have."""

    PLAN = "plan"
    SCAFFOLD = "scaffold"
    IMPLEMENT = "implement"
    TEST = "test"
    REFACTOR = "refactor"
    REVIEW = "review"
    VALIDATE = "validate"
    DECIDE = "decide"


@dataclass
class AgentConfig:
    """Configuration for a single agent."""

    name: str
    role: AgentRole
    model: str                              # LLM model identifier
    capabilities: list[AgentCapability]
    system_prompt_override: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096


@dataclass
class Agent:
    """A configured agent instance."""

    config: AgentConfig
    llm_adapter: "LLMPort"

    async def execute(self, message: "AgentMessage") -> "AgentResponse":
        """Execute a task and return response."""
        prompt = self._build_prompt(message)
        response = await self.llm_adapter.generate(prompt)
        return AgentResponse(
            agent_name=self.config.name,
            content=response,
            metadata={},
        )

    def _build_prompt(self, message: "AgentMessage") -> str:
        """Build prompt from message and role context."""
        role_prompts = {
            AgentRole.BUILDER: "You are a software architect...",
            AgentRole.CRITIC: "You are a code reviewer...",
            AgentRole.DOMAIN_SPECIALIST: "You are a domain expert...",
        }
        base = role_prompts.get(self.config.role, "")
        return f"{base}\n\n{message.content}"
```

### 2.2 Message Protocol

```python
@dataclass
class AgentMessage:
    """Message sent to an agent."""

    task: str                    # What to do
    context: dict[str, Any]      # Relevant context
    constraints: list[str]       # Must follow
    response_schema: dict | None # Expected response format
    history: list["AgentMessage"] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Response from an agent."""

    agent_name: str
    content: str | dict
    metadata: dict[str, Any]
    issues: list[str] = field(default_factory=list)
    approved: bool = True


@dataclass
class CoordinationResult:
    """Result of multi-agent coordination."""

    final_response: AgentResponse
    agent_responses: list[AgentResponse]
    iterations: int
    consensus_reached: bool = True
```

---

## 3. Run Mode Configuration

### 3.1 Configuration Model

```python
from dataclasses import dataclass
from pathlib import Path
import yaml


class RunMode(str, Enum):
    """Available run modes."""

    SOLO = "solo"
    ORCHESTRATOR = "orchestrator"
    VOTING = "voting"
    ROLE_LOCKED = "role_locked"
    HYBRID = "hybrid"


@dataclass
class RunModeConfig:
    """Configuration for multi-agent run mode."""

    mode: RunMode = RunMode.SOLO

    # Orchestrator mode settings
    orchestrator_model: str | None = None
    max_delegation_depth: int = 2
    sub_agents: list[AgentConfig] = field(default_factory=list)

    # Voting mode settings
    voting_agents: int = 3
    voting_threshold: float = 0.5  # Majority needed
    voting_model: str | None = None

    # Role-locked mode settings
    roles: dict[str, AgentConfig] = field(default_factory=dict)
    critic_required: bool = True

    # Hybrid mode settings
    phase_modes: dict[str, RunMode] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> "RunModeConfig":
        """Load configuration from YAML file."""
        if not path.exists():
            return cls()  # Default solo mode

        with open(path) as f:
            data = yaml.safe_load(f)

        mode = RunMode(data.get("mode", "solo"))

        config = cls(mode=mode)

        if mode == RunMode.ORCHESTRATOR:
            config.orchestrator_model = data.get("orchestrator", {}).get("model")
            config.max_delegation_depth = data.get("orchestrator", {}).get(
                "max_delegation_depth", 2
            )
            config.sub_agents = [
                cls._parse_agent(a) for a in data.get("sub_agents", [])
            ]

        elif mode == RunMode.VOTING:
            config.voting_agents = data.get("voting", {}).get("agents", 3)
            config.voting_threshold = data.get("voting", {}).get("threshold", 0.5)

        elif mode == RunMode.ROLE_LOCKED:
            config.roles = {
                name: cls._parse_agent(cfg)
                for name, cfg in data.get("roles", {}).items()
            }
            config.critic_required = data.get("critic_required", True)

        elif mode == RunMode.HYBRID:
            config.phase_modes = {
                phase: RunMode(mode_name)
                for phase, mode_name in data.get("phases", {}).items()
            }

        return config

    @staticmethod
    def _parse_agent(data: dict) -> AgentConfig:
        """Parse agent configuration from dict."""
        return AgentConfig(
            name=data.get("name", "agent"),
            role=AgentRole(data.get("role", "builder")),
            model=data.get("model", "claude-3-sonnet"),
            capabilities=[
                AgentCapability(c) for c in data.get("capabilities", [])
            ],
        )
```

### 3.2 YAML Format Examples

**Solo Mode (Default)**:
```yaml
mode: solo
```

**Orchestrator Mode**:
```yaml
mode: orchestrator

orchestrator:
  model: claude-3-opus
  max_delegation_depth: 2

sub_agents:
  - name: builder
    role: builder
    model: claude-3-sonnet
    capabilities: [plan, scaffold, implement]

  - name: critic
    role: critic
    model: claude-3-opus
    capabilities: [review, validate]
```

**Voting Mode**:
```yaml
mode: voting

voting:
  agents: 3
  threshold: 0.66  # 2/3 majority
  model: claude-3-sonnet
```

**Role-Locked Mode**:
```yaml
mode: role_locked

critic_required: true

roles:
  architect:
    role: builder
    model: claude-3-opus
    capabilities: [plan]

  implementer:
    role: builder
    model: claude-3-sonnet
    capabilities: [scaffold, implement]

  reviewer:
    role: critic
    model: claude-3-opus
    capabilities: [review, validate]
```

**Hybrid Mode**:
```yaml
mode: hybrid

phases:
  planning: orchestrator
  implementation: solo
  review: voting
```

---

## 4. Mode Implementations

### 4.1 Coordinator Port

```python
from abc import ABC, abstractmethod


class CoordinatorPort(ABC):
    """Port for agent coordination."""

    @abstractmethod
    async def coordinate(
        self,
        task: str,
        context: dict,
    ) -> CoordinationResult:
        """Coordinate agents to complete a task."""
        ...

    @abstractmethod
    def get_active_agents(self) -> list[Agent]:
        """Get currently active agents."""
        ...
```

### 4.2 Orchestrator Mode (B)

```python
class OrchestratorMode(CoordinatorPort):
    """Orchestrator delegates to sub-agents."""

    def __init__(
        self,
        orchestrator: Agent,
        sub_agents: list[Agent],
        max_depth: int = 2,
    ) -> None:
        self.orchestrator = orchestrator
        self.sub_agents = {a.config.name: a for a in sub_agents}
        self.max_depth = max_depth

    async def coordinate(
        self,
        task: str,
        context: dict,
    ) -> CoordinationResult:
        responses = []

        # Orchestrator decides delegation
        delegation_plan = await self._plan_delegation(task, context)

        for step in delegation_plan:
            agent = self.sub_agents.get(step["agent"])
            if not agent:
                continue

            message = AgentMessage(
                task=step["task"],
                context=context,
                constraints=step.get("constraints", []),
                response_schema=step.get("schema"),
            )

            response = await agent.execute(message)
            responses.append(response)

            # Check for critic review
            if self._needs_review(step, response):
                critic = self._get_critic()
                if critic:
                    review = await self._request_review(critic, response)
                    responses.append(review)

                    if not review.approved:
                        # Request revision
                        revised = await self._request_revision(
                            agent, response, review
                        )
                        responses.append(revised)

        return CoordinationResult(
            final_response=responses[-1],
            agent_responses=responses,
            iterations=len(responses),
        )

    async def _plan_delegation(
        self,
        task: str,
        context: dict,
    ) -> list[dict]:
        """Have orchestrator create delegation plan."""
        message = AgentMessage(
            task=f"Plan delegation for: {task}",
            context=context,
            constraints=["Assign to appropriate sub-agents"],
            response_schema={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "task": {"type": "string"},
                    },
                },
            },
        )
        response = await self.orchestrator.execute(message)
        return response.content  # Parsed JSON
```

### 4.3 Voting Mode (C)

```python
class VotingMode(CoordinatorPort):
    """Agents vote to reach consensus."""

    def __init__(
        self,
        voters: list[Agent],
        threshold: float = 0.5,
    ) -> None:
        self.voters = voters
        self.threshold = threshold

    async def coordinate(
        self,
        task: str,
        context: dict,
    ) -> CoordinationResult:
        # Collect votes from all agents
        votes: list[AgentResponse] = []

        for voter in self.voters:
            message = AgentMessage(
                task=task,
                context=context,
                constraints=["Provide your vote and reasoning"],
                response_schema={
                    "type": "object",
                    "properties": {
                        "vote": {"type": "string"},
                        "reasoning": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                },
            )
            response = await voter.execute(message)
            votes.append(response)

        # Tally votes
        vote_counts = self._tally_votes(votes)
        winner = self._determine_winner(vote_counts)

        # Check if threshold met
        winner_ratio = vote_counts[winner] / len(votes)
        consensus = winner_ratio >= self.threshold

        # Consolidate reasoning
        final_response = AgentResponse(
            agent_name="voting_consensus",
            content={
                "decision": winner,
                "vote_count": vote_counts,
                "consensus": consensus,
                "reasoning": self._consolidate_reasoning(votes, winner),
            },
            metadata={"votes": len(votes)},
        )

        return CoordinationResult(
            final_response=final_response,
            agent_responses=votes,
            iterations=1,
            consensus_reached=consensus,
        )

    def _tally_votes(
        self,
        votes: list[AgentResponse],
    ) -> dict[str, int]:
        counts: dict[str, int] = {}
        for vote in votes:
            choice = vote.content.get("vote", "abstain")
            counts[choice] = counts.get(choice, 0) + 1
        return counts

    def _determine_winner(self, counts: dict[str, int]) -> str:
        return max(counts, key=counts.get)
```

### 4.4 Role-Locked Mode (D)

```python
class RoleLockedMode(CoordinatorPort):
    """Agents have fixed roles and handoff work."""

    def __init__(
        self,
        roles: dict[str, Agent],
        critic_required: bool = True,
    ) -> None:
        self.roles = roles
        self.critic_required = critic_required

    async def coordinate(
        self,
        task: str,
        context: dict,
    ) -> CoordinationResult:
        responses = []

        # Determine workflow based on task type
        workflow = self._determine_workflow(task)

        for role_name in workflow:
            agent = self.roles.get(role_name)
            if not agent:
                continue

            message = AgentMessage(
                task=task,
                context={**context, "previous_responses": responses},
                constraints=self._get_role_constraints(role_name),
                response_schema=None,
            )

            response = await agent.execute(message)
            responses.append(response)

            # Critic review if required
            if self.critic_required and role_name != "critic":
                critic = self.roles.get("critic")
                if critic:
                    review = await self._critic_review(critic, response)
                    responses.append(review)

                    if not review.approved:
                        # Loop back for revision
                        break

        return CoordinationResult(
            final_response=responses[-1],
            agent_responses=responses,
            iterations=len(responses),
        )

    def _determine_workflow(self, task: str) -> list[str]:
        """Determine which roles participate based on task."""
        if "plan" in task.lower():
            return ["architect", "critic"]
        elif "implement" in task.lower():
            return ["architect", "implementer", "critic"]
        elif "review" in task.lower():
            return ["critic"]
        else:
            return list(self.roles.keys())
```

---

## 5. CLI Integration

### 5.1 Mode Selection

```python
import typer

@app.command()
def plan(
    artifact_type: str,
    mode: str = typer.Option(
        None,
        "--mode",
        help="Override run mode (solo, orchestrator, voting)",
    ),
) -> None:
    """Generate a plan artifact."""
    # Load run mode config
    config = RunModeConfig.from_file(
        Path(".project/run_mode.yaml")
    )

    # CLI override
    if mode:
        config.mode = RunMode(mode)

    # Get appropriate coordinator
    coordinator = get_coordinator(config)

    # Coordinate artifact generation
    result = coordinator.coordinate(
        task=f"Generate {artifact_type}",
        context=load_project_context(),
    )

    # Handle result
    ...
```

---

## 6. Agent Communication Protocol

### 6.1 Message Format

```json
{
  "message_id": "uuid",
  "from_agent": "orchestrator",
  "to_agent": "builder",
  "message_type": "task",
  "content": {
    "task": "Generate ProjectPlan",
    "context": {
      "requirements": "...",
      "constraints": "..."
    },
    "constraints": [
      "Follow JSON schema",
      "Include all milestones"
    ],
    "response_schema": { ... }
  },
  "timestamp": "2026-01-11T10:00:00Z"
}
```

### 6.2 Response Format

```json
{
  "message_id": "uuid",
  "in_reply_to": "original-message-id",
  "from_agent": "builder",
  "to_agent": "orchestrator",
  "message_type": "response",
  "content": {
    "artifact": { ... },
    "confidence": 0.95,
    "notes": "Completed successfully"
  },
  "issues": [],
  "approved": true,
  "timestamp": "2026-01-11T10:01:00Z"
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial design |
