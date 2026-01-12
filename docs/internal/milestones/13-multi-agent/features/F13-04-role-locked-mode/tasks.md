# Feature F13-04: Role-Locked Mode - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T13-04-01 | Implement RoleLockedMode coordinator | Complete | P0 |
| T13-04-02 | Define workflow determination | Complete | P0 |
| T13-04-03 | Implement role handoff | Complete | P0 |
| T13-04-04 | Add mandatory critic review | Complete | P0 |
| T13-04-05 | Create role-specific prompts | Complete | P1 |
| T13-04-06 | Write unit tests | Complete | P0 |

---

## 2. Task Details

### T13-04-01: Implement RoleLockedMode Coordinator

**Objective**: Create role-locked mode coordinator.

**Files to Create**:
- [x] `rice_factor/adapters/agents/role_locked_mode.py`

**Implementation**:
```python
class RoleLockedMode(CoordinatorPort):
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
        workflow = self._determine_workflow(task)
        responses = await self._execute_workflow(workflow, task, context)
        return CoordinationResult(
            final_response=responses[-1],
            agent_responses=responses,
            iterations=len(responses),
        )

    def get_active_agents(self) -> list[Agent]:
        return list(self.roles.values())
```

**Acceptance Criteria**:
- [x] Implements CoordinatorPort
- [x] Roles are fixed
- [x] Critic configurable

---

### T13-04-02: Define Workflow Determination

**Objective**: Determine which roles participate.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/role_locked_mode.py`

**Workflow Rules**:
| Task Type | Roles |
|-----------|-------|
| Planning | architect → critic |
| Implementation | architect → implementer → critic |
| Testing | tester → critic |
| Review | critic |
| Refactoring | architect → implementer → critic |

**Implementation**:
```python
def _determine_workflow(self, task: str) -> list[str]:
    task_lower = task.lower()

    workflows = {
        "plan": ["architect", "critic"],
        "implement": ["architect", "implementer", "critic"],
        "test": ["tester", "critic"],
        "review": ["critic"],
        "refactor": ["architect", "implementer", "critic"],
    }

    for keyword, workflow in workflows.items():
        if keyword in task_lower:
            return [r for r in workflow if r in self.roles]

    # Default: all roles
    return list(self.roles.keys())
```

**Acceptance Criteria**:
- [x] Task type detected
- [x] Only available roles used
- [x] Reasonable defaults

---

### T13-04-03: Implement Role Handoff

**Objective**: Pass work between roles.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/role_locked_mode.py`

**Implementation**:
```python
async def _execute_workflow(
    self,
    workflow: list[str],
    task: str,
    context: dict,
) -> list[AgentResponse]:
    responses = []

    for role_name in workflow:
        agent = self.roles.get(role_name)
        if not agent:
            continue

        # Build context with previous work
        role_context = {
            **context,
            "previous_responses": [r.content for r in responses],
            "your_role": role_name,
        }

        message = AgentMessage(
            task=task,
            context=role_context,
            constraints=self._get_role_constraints(role_name),
            response_schema=None,
        )

        response = await agent.execute(message)
        responses.append(response)

        # Check if critic rejected
        if role_name == "critic" and not response.approved:
            # Need to loop back
            break

    return responses
```

**Acceptance Criteria**:
- [x] Context passed forward
- [x] Roles execute in order
- [x] Rejection handled

---

### T13-04-04: Add Mandatory Critic Review

**Objective**: Critic must review before approval.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/role_locked_mode.py`

**Implementation**:
```python
async def _execute_workflow(
    self,
    workflow: list[str],
    task: str,
    context: dict,
) -> list[AgentResponse]:
    responses = []

    for i, role_name in enumerate(workflow):
        agent = self.roles.get(role_name)
        response = await agent.execute(message)
        responses.append(response)

        # Mandatory critic review after each non-critic
        if self.critic_required and role_name != "critic":
            critic = self.roles.get("critic")
            if critic:
                review = await self._critic_review(critic, response)
                responses.append(review)

                if not review.approved:
                    # Request revision and re-review
                    revised = await self._request_revision(
                        agent, response, review
                    )
                    responses.append(revised)

                    # Re-submit to critic
                    re_review = await self._critic_review(critic, revised)
                    responses.append(re_review)

    return responses
```

**Acceptance Criteria**:
- [x] Critic reviews each output
- [x] Rejection triggers revision
- [x] Can be disabled

---

### T13-04-05: Create Role-Specific Prompts

**Objective**: System prompts tailored to roles.

**Files to Create**:
- [x] `rice_factor/adapters/agents/role_prompts.py`

**Prompts**:
```python
ROLE_PROMPTS = {
    "architect": """You are a software architect.
Your responsibilities:
- Design system structure
- Define interfaces and contracts
- Ensure architectural coherence
- Consider non-functional requirements

You must NOT write implementation code.""",

    "implementer": """You are a software implementer.
Your responsibilities:
- Write code following the architect's design
- Ensure code quality and best practices
- Write clean, maintainable code

You must follow the provided design exactly.""",

    "critic": """You are a code reviewer and critic.
Your responsibilities:
- Review artifacts for correctness
- Identify potential issues
- Ensure requirements are met
- Approve or reject with reasoning

Be thorough but constructive.""",

    "tester": """You are a test engineer.
Your responsibilities:
- Design comprehensive tests
- Ensure edge cases are covered
- Verify requirements through tests

Focus on behavior, not implementation.""",
}
```

**Acceptance Criteria**:
- [x] Each role has prompt
- [x] Clear responsibilities
- [x] Boundaries defined

---

### T13-04-06: Write Unit Tests

**Objective**: Test role-locked mode.

**Files to Create**:
- [x] `tests/unit/adapters/agents/test_role_locked_mode.py`

**Test Cases**:
- [x] Workflow determination
- [x] Role handoff
- [x] Critic approval path
- [x] Critic rejection + revision
- [x] Missing role handling
- [x] Critic disabled
- [x] Role-specific prompts

**Acceptance Criteria**:
- [x] All workflows tested
- [x] Critic paths verified

---

## 3. Task Dependencies

```
T13-04-01 (Coordinator) ──→ T13-04-02 (Workflow) ──→ T13-04-03 (Handoff)
                                                          │
                                                          ↓
                                                  T13-04-04 (Critic)
                                                          │
                                                          ↓
                                                  T13-04-05 (Prompts)
                                                          │
                                                          ↓
                                                  T13-04-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T13-04-01 | Medium | Coordinator setup |
| T13-04-02 | Medium | Task parsing |
| T13-04-03 | Medium | Context passing |
| T13-04-04 | High | Loop logic |
| T13-04-05 | Low | Static prompts |
| T13-04-06 | High | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.1.0 | 2026-01-11 | Implementation | All tasks completed |
