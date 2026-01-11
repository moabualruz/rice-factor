# Feature F13-03: Voting Mode - Tasks

> **Document Type**: Feature Task Breakdown
> **Version**: 1.1.0
> **Status**: Complete
> **Parent**: [requirements.md](../../requirements.md)

---

## 1. Task Overview

| Task ID | Task Name | Status | Priority |
|---------|-----------|--------|----------|
| T13-03-01 | Implement VotingMode coordinator | Complete | P0 |
| T13-03-02 | Create vote collection | Complete | P0 |
| T13-03-03 | Implement vote tallying | Complete | P0 |
| T13-03-04 | Add consensus checking | Complete | P0 |
| T13-03-05 | Consolidate reasoning | Complete | P1 |
| T13-03-06 | Write unit tests | Complete | P0 |

---

## 2. Task Details

### T13-03-01: Implement VotingMode Coordinator

**Objective**: Create voting mode coordinator.

**Files to Create**:
- [x] `rice_factor/adapters/agents/voting_mode.py`

**Implementation**:
```python
class VotingMode(CoordinatorPort):
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
        votes = await self._collect_votes(task, context)
        result = self._tally_and_decide(votes)
        return result

    def get_active_agents(self) -> list[Agent]:
        return self.voters
```

**Acceptance Criteria**:
- [x] Implements CoordinatorPort
- [x] Configurable threshold
- [x] Returns CoordinationResult

---

### T13-03-02: Create Vote Collection

**Objective**: Collect votes from all agents.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/voting_mode.py`

**Vote Schema**:
```json
{
  "vote": "option_a",
  "reasoning": "Why I chose this...",
  "confidence": 0.85,
  "alternatives_considered": ["option_b", "option_c"]
}
```

**Implementation**:
```python
async def _collect_votes(
    self,
    task: str,
    context: dict,
) -> list[AgentResponse]:
    votes = []

    for voter in self.voters:
        message = AgentMessage(
            task=task,
            context=context,
            constraints=[
                "Provide your vote with reasoning",
                "Rate your confidence 0-1",
                "Consider alternatives",
            ],
            response_schema=VOTE_SCHEMA,
        )
        vote = await voter.execute(message)
        votes.append(vote)

    return votes
```

**Acceptance Criteria**:
- [x] All voters queried
- [x] Structured responses
- [x] Parallel execution option

---

### T13-03-03: Implement Vote Tallying

**Objective**: Count votes and determine winner.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/voting_mode.py`

**Implementation**:
```python
def _tally_votes(
    self,
    votes: list[AgentResponse],
) -> dict[str, VoteTally]:
    tallies: dict[str, VoteTally] = {}

    for vote in votes:
        choice = vote.content.get("vote")
        confidence = vote.content.get("confidence", 1.0)

        if choice not in tallies:
            tallies[choice] = VoteTally(choice=choice)

        tallies[choice].count += 1
        tallies[choice].total_confidence += confidence
        tallies[choice].voters.append(vote.agent_name)

    return tallies

def _determine_winner(
    self,
    tallies: dict[str, VoteTally],
) -> str:
    # Winner by count, then by confidence
    return max(
        tallies.values(),
        key=lambda t: (t.count, t.total_confidence),
    ).choice
```

**Acceptance Criteria**:
- [x] Counts votes correctly
- [x] Tracks confidence
- [x] Tie-breaking logic

---

### T13-03-04: Add Consensus Checking

**Objective**: Determine if consensus threshold met.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/voting_mode.py`

**Implementation**:
```python
def _check_consensus(
    self,
    tallies: dict[str, VoteTally],
    winner: str,
    total_votes: int,
) -> bool:
    winner_tally = tallies[winner]
    winner_ratio = winner_tally.count / total_votes
    return winner_ratio >= self.threshold

def _handle_no_consensus(
    self,
    tallies: dict[str, VoteTally],
    votes: list[AgentResponse],
) -> CoordinationResult:
    # Options:
    # 1. Request re-vote with narrowed options
    # 2. Return top choice with warning
    # 3. Require human decision

    return CoordinationResult(
        final_response=AgentResponse(
            agent_name="voting",
            content={
                "status": "no_consensus",
                "tallies": tallies,
            },
            metadata={},
        ),
        agent_responses=votes,
        iterations=1,
        consensus_reached=False,
    )
```

**Acceptance Criteria**:
- [x] Threshold comparison correct
- [x] No-consensus handled
- [x] Result indicates status

---

### T13-03-05: Consolidate Reasoning

**Objective**: Combine reasoning from winning votes.

**Files to Modify**:
- [x] `rice_factor/adapters/agents/voting_mode.py`

**Implementation**:
```python
def _consolidate_reasoning(
    self,
    votes: list[AgentResponse],
    winner: str,
) -> str:
    # Get reasoning from all votes for winner
    winning_reasons = [
        vote.content.get("reasoning")
        for vote in votes
        if vote.content.get("vote") == winner
    ]

    # Also include dissenting views
    dissenting_reasons = [
        f"{vote.agent_name}: {vote.content.get('reasoning')}"
        for vote in votes
        if vote.content.get("vote") != winner
    ]

    consolidated = f"""
Decision: {winner}

Supporting Arguments:
{chr(10).join(f"- {r}" for r in winning_reasons)}

Dissenting Views:
{chr(10).join(f"- {r}" for r in dissenting_reasons) or "None"}
"""
    return consolidated.strip()
```

**Acceptance Criteria**:
- [x] Winning reasons included
- [x] Dissenting views shown
- [x] Readable format

---

### T13-03-06: Write Unit Tests

**Objective**: Test voting mode.

**Files to Create**:
- [x] `tests/unit/adapters/agents/test_voting_mode.py`

**Test Cases**:
- [x] Unanimous vote
- [x] Majority vote meets threshold
- [x] Vote fails threshold
- [x] Tie-breaking
- [x] Confidence weighting
- [x] Reasoning consolidation
- [x] No consensus handling

**Acceptance Criteria**:
- [x] All voting scenarios tested
- [x] Edge cases covered

---

## 3. Task Dependencies

```
T13-03-01 (Coordinator) ──→ T13-03-02 (Collection) ──→ T13-03-03 (Tally)
                                                            │
                                                            ↓
                                                    T13-03-04 (Consensus)
                                                            │
                                                            ↓
                                                    T13-03-05 (Reasoning)
                                                            │
                                                            ↓
                                                    T13-03-06 (Tests)
```

---

## 4. Estimated Effort

| Task | Complexity | Notes |
|------|------------|-------|
| T13-03-01 | Medium | Coordinator setup |
| T13-03-02 | Medium | Parallel collection |
| T13-03-03 | Low | Counting logic |
| T13-03-04 | Low | Threshold check |
| T13-03-05 | Medium | Text formatting |
| T13-03-06 | Medium | Many scenarios |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-11 | Gap Analysis | Initial task breakdown |
| 1.1.0 | 2026-01-11 | Implementation | All tasks completed |
