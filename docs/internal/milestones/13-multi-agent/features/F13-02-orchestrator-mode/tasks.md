# Feature F13-02: Orchestrator Mode - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T13-02-01 | Create CoordinatorPort interface | Complete | P0 |
| T13-02-02 | Create Agent class | Complete | P0 |
| T13-02-03 | Implement delegation planning | Complete | P0 |
| T13-02-04 | Implement sub-agent execution | Complete | P0 |
| T13-02-05 | Add critic review loop | Complete | P0 |
| T13-02-06 | Handle delegation depth | Complete | P1 |
| T13-02-07 | Write unit tests | Complete | P0 |

---

## 2. Task Details

### T13-02-01: Create CoordinatorPort Interface

**Objective**: Define port for agent coordination.

**Files to Create**:
- [x] `rice_factor/domain/ports/coordinator.py`

**Implementation**:
```python
class CoordinatorPort(ABC):
    @abstractmethod
    async def coordinate(
        self,
        task: str,
        context: dict,
    ) -> CoordinationResult:
        ...

    @abstractmethod
    def get_active_agents(self) -> list[Agent]:
        ...
```

**Acceptance Criteria**:
- [x] Port follows hexagonal pattern
- [x] Async interface
- [x] Clear contract

---

### T13-02-02: Create Agent Class

**Objective**: Implement agent that wraps LLM.

**Files to Create**:
- [x] `rice_factor/adapters/agents/agent.py`

**Implementation**:
```python
@dataclass
class Agent:
    config: AgentConfig
    llm_adapter: LLMPort

    async def execute(
        self,
        message: AgentMessage,
    ) -> AgentResponse:
        prompt = self._build_prompt(message)
        response = await self.llm_adapter.generate(prompt)
        return AgentResponse(
            agent_name=self.config.name,
            content=response,
            metadata={},
        )
```

**Acceptance Criteria**:
- [x] Wraps LLM adapter
- [x] Builds role-specific prompt
- [x] Returns structured response

---

### T13-02-03: Implement Delegation Planning

**Objective**: Orchestrator creates delegation plan.

**Files to Create**:
- [x] `rice_factor/adapters/agents/orchestrator_mode.py`

**Implementation**:
```python
async def _plan_delegation(
    self,
    task: str,
    context: dict,
) -> list[DelegationStep]:
    message = AgentMessage(
        task=f"Plan how to delegate: {task}",
        context=context,
        constraints=[
            "Assign each subtask to appropriate agent",
            "Consider agent capabilities",
        ],
        response_schema=DELEGATION_SCHEMA,
    )
    response = await self.orchestrator.execute(message)
    return self._parse_delegation(response.content)
```

**Acceptance Criteria**:
- [x] Creates structured plan
- [x] Respects agent capabilities
- [x] Valid JSON response

---

### T13-02-04: Implement Sub-Agent Execution

**Objective**: Execute tasks on sub-agents.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/orchestrator_mode.py`

**Implementation**:
```python
async def _execute_delegation(
    self,
    steps: list[DelegationStep],
    context: dict,
) -> list[AgentResponse]:
    responses = []

    for step in steps:
        agent = self.sub_agents.get(step.agent_name)
        if not agent:
            continue

        message = AgentMessage(
            task=step.task,
            context={**context, "previous": responses},
            constraints=step.constraints,
            response_schema=step.schema,
        )

        response = await agent.execute(message)
        responses.append(response)

    return responses
```

**Acceptance Criteria**:
- [x] Routes to correct agent
- [x] Passes context forward
- [x] Collects responses

---

### T13-02-05: Add Critic Review Loop

**Objective**: Critic reviews before approval.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/orchestrator_mode.py`

**Implementation**:
```python
async def _request_review(
    self,
    response: AgentResponse,
) -> AgentResponse:
    critic = self._get_critic()
    if not critic:
        return response

    review_message = AgentMessage(
        task="Review this artifact for issues",
        context={"artifact": response.content},
        constraints=[
            "Identify any problems",
            "Suggest improvements",
            "Approve or reject",
        ],
        response_schema=REVIEW_SCHEMA,
    )

    review = await critic.execute(review_message)

    if not review.approved:
        # Request revision from original agent
        revised = await self._request_revision(response, review)
        return await self._request_review(revised)

    return response
```

**Acceptance Criteria**:
- [x] Critic reviews output
- [x] Rejection triggers revision
- [x] Loop terminates

---

### T13-02-06: Handle Delegation Depth

**Objective**: Prevent infinite delegation.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/orchestrator_mode.py`

**Implementation**:
```python
async def coordinate(
    self,
    task: str,
    context: dict,
    _depth: int = 0,
) -> CoordinationResult:
    if _depth >= self.max_depth:
        raise DelegationDepthError(
            f"Max delegation depth {self.max_depth} exceeded"
        )

    # ... delegation logic ...

    # If sub-agent needs to delegate further
    if needs_sub_delegation:
        result = await sub_coordinator.coordinate(
            sub_task,
            context,
            _depth=_depth + 1,
        )
```

**Acceptance Criteria**:
- [x] Depth tracked
- [x] Max depth enforced
- [x] Clear error message

---

### T13-02-07: Write Unit Tests

**Objective**: Test orchestrator mode.

**Files to Create**:
- [x] `tests/unit/adapters/agents/test_orchestrator_mode.py`

**Test Cases**:
- [x] Delegation planning
- [x] Sub-agent routing
- [x] Critic review pass
- [x] Critic review rejection + revision
- [x] Depth limit enforced
- [x] Missing agent handling

**Acceptance Criteria**:
- [x] All coordination paths tested
- [x] Mocked LLM responses

---

## 3. Task Dependencies

```
T13-02-01 (Port) ──→ T13-02-02 (Agent) ──→ T13-02-03 (Planning)
                                                  │
                                                  ↓
                                          T13-02-04 (Execution)
                                                  │
                                                  ↓
                                          T13-02-05 (Review)
                                                  │
                                                  ↓
                                          T13-02-06 (Depth)
                                                  │
                                                  ↓
                                          T13-02-07 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T13-02-01 | Low | Interface |
| T13-02-02 | Medium | LLM wrapping |
| T13-02-03 | High | JSON parsing |
| T13-02-04 | Medium | Routing logic |
| T13-02-05 | High | Loop logic |
| T13-02-06 | Low | Counter |
| T13-02-07 | High | Many mocks |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.1.0 | 2026-01-11 | Implementation | All tasks completed |
