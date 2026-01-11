"""Message models for agent communication.

This module defines the structured message types used for agent coordination.
Agents communicate only via structured messages, not free-form chat.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    """Types of messages in agent coordination."""

    # Task lifecycle
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    TASK_DELEGATION = "task_delegation"

    # Artifact-related
    ARTIFACT_PROPOSAL = "artifact_proposal"
    ARTIFACT_CRITIQUE = "artifact_critique"
    ARTIFACT_APPROVAL = "artifact_approval"

    # Analysis
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESPONSE = "analysis_response"

    # Voting
    VOTE_REQUEST = "vote_request"
    VOTE_CAST = "vote_cast"
    VOTE_RESULT = "vote_result"

    # Coordination
    QUERY = "query"
    RESPONSE = "response"
    HANDOFF = "handoff"
    SYNTHESIS = "synthesis"


class MessagePriority(str, Enum):
    """Priority levels for messages."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class AgentMessage:
    """A structured message between agents.

    All agent communication happens via these messages.
    Messages are immutable and timestamped.

    Attributes:
        message_id: Unique identifier for this message.
        message_type: The type of message.
        sender_id: ID of the sending agent.
        recipient_id: ID of the recipient agent (None for broadcast).
        content: The message payload (type depends on message_type).
        priority: Message priority level.
        timestamp: When the message was created.
        correlation_id: Optional ID linking related messages.
        metadata: Additional context for the message.
    """

    message_id: str
    message_type: MessageType
    sender_id: str
    content: dict[str, Any]
    recipient_id: str | None = None
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_broadcast(self) -> bool:
        """Check if this is a broadcast message.

        Returns:
            True if no specific recipient is set.
        """
        return self.recipient_id is None


@dataclass(frozen=True)
class AgentResponse:
    """Response from an agent to a task or query.

    Attributes:
        response_id: Unique identifier for this response.
        agent_id: ID of the responding agent.
        message_id: ID of the message being responded to.
        success: Whether the agent successfully processed the request.
        result: The response payload.
        errors: Any errors encountered.
        warnings: Any warnings to surface.
        reasoning: Optional explanation of the agent's reasoning.
        timestamp: When the response was created.
    """

    response_id: str
    agent_id: str
    message_id: str
    success: bool
    result: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reasoning: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class Vote:
    """A vote cast by an agent in voting mode.

    Attributes:
        agent_id: ID of the voting agent.
        choice: The option being voted for.
        confidence: Confidence level (0.0 to 1.0).
        reasoning: Explanation for the vote.
        timestamp: When the vote was cast.
    """

    agent_id: str
    choice: str
    confidence: float
    reasoning: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate confidence is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


@dataclass(frozen=True)
class VoteResult:
    """Result of a voting round.

    Attributes:
        votes: All votes cast.
        winner: The winning choice (None if no consensus).
        vote_counts: Counts per choice.
        total_confidence: Sum of confidence for winning choice.
        consensus_reached: Whether threshold was met.
        threshold: The threshold that was required.
    """

    votes: tuple[Vote, ...]
    winner: str | None
    vote_counts: dict[str, int]
    total_confidence: float
    consensus_reached: bool
    threshold: float

    @classmethod
    def from_votes(
        cls,
        votes: list[Vote],
        threshold: float = 0.5,
    ) -> "VoteResult":
        """Create a VoteResult from a list of votes.

        Args:
            votes: List of votes to tally.
            threshold: Minimum vote ratio for consensus.

        Returns:
            VoteResult with tallied results.
        """
        vote_counts: dict[str, int] = {}
        confidence_sums: dict[str, float] = {}

        for vote in votes:
            vote_counts[vote.choice] = vote_counts.get(vote.choice, 0) + 1
            confidence_sums[vote.choice] = confidence_sums.get(vote.choice, 0.0) + vote.confidence

        total_votes = len(votes)
        winner = None
        total_confidence = 0.0
        consensus_reached = False

        if total_votes > 0:
            # Find the choice with most votes
            max_choice = max(vote_counts, key=lambda c: vote_counts[c])
            max_votes = vote_counts[max_choice]

            # Check if threshold is met
            if max_votes / total_votes >= threshold:
                winner = max_choice
                total_confidence = confidence_sums[max_choice]
                consensus_reached = True

        return cls(
            votes=tuple(votes),
            winner=winner,
            vote_counts=vote_counts,
            total_confidence=total_confidence,
            consensus_reached=consensus_reached,
            threshold=threshold,
        )


@dataclass(frozen=True)
class CoordinationResult:
    """Result of a multi-agent coordination session.

    Attributes:
        session_id: Unique identifier for the coordination session.
        success: Whether coordination succeeded.
        artifact_id: ID of the produced artifact (if any).
        participating_agents: IDs of agents that participated.
        messages_exchanged: Count of messages during coordination.
        votes: Optional vote result if voting was used.
        final_decision: The decision that was reached.
        reasoning: Combined reasoning from agents.
        errors: Any errors that occurred.
        duration_ms: How long coordination took.
    """

    session_id: str
    success: bool
    participating_agents: tuple[str, ...]
    messages_exchanged: int
    artifact_id: str | None = None
    votes: VoteResult | None = None
    final_decision: str | None = None
    reasoning: str | None = None
    errors: tuple[str, ...] = field(default_factory=tuple)
    duration_ms: int = 0
