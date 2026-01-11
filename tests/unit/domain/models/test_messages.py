"""Unit tests for message models."""

from datetime import UTC, datetime

import pytest

from rice_factor.domain.models.messages import (
    AgentMessage,
    AgentResponse,
    CoordinationResult,
    MessagePriority,
    MessageType,
    Vote,
    VoteResult,
)


class TestMessageType:
    """Tests for MessageType enum."""

    def test_task_types(self) -> None:
        """Test task-related message types."""
        assert MessageType.TASK_ASSIGNMENT.value == "task_assignment"
        assert MessageType.TASK_RESULT.value == "task_result"
        assert MessageType.TASK_DELEGATION.value == "task_delegation"

    def test_artifact_types(self) -> None:
        """Test artifact-related message types."""
        assert MessageType.ARTIFACT_PROPOSAL.value == "artifact_proposal"
        assert MessageType.ARTIFACT_CRITIQUE.value == "artifact_critique"

    def test_voting_types(self) -> None:
        """Test voting-related message types."""
        assert MessageType.VOTE_REQUEST.value == "vote_request"
        assert MessageType.VOTE_CAST.value == "vote_cast"
        assert MessageType.VOTE_RESULT.value == "vote_result"


class TestMessagePriority:
    """Tests for MessagePriority enum."""

    def test_priorities(self) -> None:
        """Test priority values."""
        assert MessagePriority.LOW.value == "low"
        assert MessagePriority.NORMAL.value == "normal"
        assert MessagePriority.HIGH.value == "high"
        assert MessagePriority.CRITICAL.value == "critical"


class TestAgentMessage:
    """Tests for AgentMessage dataclass."""

    def test_minimal_message(self) -> None:
        """Test creating message with minimal arguments."""
        msg = AgentMessage(
            message_id="msg-001",
            message_type=MessageType.TASK_ASSIGNMENT,
            sender_id="orchestrator",
            content={"task": "analyze code"},
        )
        assert msg.message_id == "msg-001"
        assert msg.message_type == MessageType.TASK_ASSIGNMENT
        assert msg.sender_id == "orchestrator"
        assert msg.content == {"task": "analyze code"}
        assert msg.recipient_id is None
        assert msg.priority == MessagePriority.NORMAL

    def test_full_message(self) -> None:
        """Test creating message with all arguments."""
        ts = datetime.now(UTC)
        msg = AgentMessage(
            message_id="msg-002",
            message_type=MessageType.ARTIFACT_CRITIQUE,
            sender_id="critic",
            recipient_id="primary",
            content={"issues": ["missing tests"]},
            priority=MessagePriority.HIGH,
            timestamp=ts,
            correlation_id="session-123",
            metadata={"phase": "review"},
        )
        assert msg.recipient_id == "primary"
        assert msg.priority == MessagePriority.HIGH
        assert msg.timestamp == ts
        assert msg.correlation_id == "session-123"
        assert msg.metadata == {"phase": "review"}

    def test_is_broadcast_no_recipient(self) -> None:
        """Test that message without recipient is broadcast."""
        msg = AgentMessage(
            message_id="msg-003",
            message_type=MessageType.VOTE_REQUEST,
            sender_id="orchestrator",
            content={"options": ["A", "B"]},
        )
        assert msg.is_broadcast() is True

    def test_is_broadcast_with_recipient(self) -> None:
        """Test that message with recipient is not broadcast."""
        msg = AgentMessage(
            message_id="msg-004",
            message_type=MessageType.QUERY,
            sender_id="primary",
            recipient_id="specialist",
            content={"question": "What is X?"},
        )
        assert msg.is_broadcast() is False


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_success_response(self) -> None:
        """Test creating a success response."""
        response = AgentResponse(
            response_id="resp-001",
            agent_id="planner",
            message_id="msg-001",
            success=True,
            result={"plan": ["step1", "step2"]},
        )
        assert response.success is True
        assert response.result == {"plan": ["step1", "step2"]}
        assert response.errors == []

    def test_failure_response(self) -> None:
        """Test creating a failure response."""
        response = AgentResponse(
            response_id="resp-002",
            agent_id="analyst",
            message_id="msg-002",
            success=False,
            errors=["Cannot analyze: missing context"],
            reasoning="Insufficient data provided.",
        )
        assert response.success is False
        assert len(response.errors) == 1
        assert response.reasoning == "Insufficient data provided."

    def test_response_with_warnings(self) -> None:
        """Test response with warnings."""
        response = AgentResponse(
            response_id="resp-003",
            agent_id="critic",
            message_id="msg-003",
            success=True,
            result={"approved": True},
            warnings=["Minor style issues found"],
        )
        assert response.success is True
        assert len(response.warnings) == 1


class TestVote:
    """Tests for Vote dataclass."""

    def test_create_vote(self) -> None:
        """Test creating a vote."""
        vote = Vote(
            agent_id="agent-1",
            choice="option_a",
            confidence=0.85,
            reasoning="Best fit for requirements",
        )
        assert vote.agent_id == "agent-1"
        assert vote.choice == "option_a"
        assert vote.confidence == 0.85
        assert vote.reasoning == "Best fit for requirements"

    def test_vote_without_reasoning(self) -> None:
        """Test vote without reasoning."""
        vote = Vote(
            agent_id="agent-2",
            choice="option_b",
            confidence=0.6,
        )
        assert vote.reasoning is None

    def test_vote_confidence_validation_too_high(self) -> None:
        """Test that confidence > 1.0 raises error."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            Vote(
                agent_id="agent-1",
                choice="x",
                confidence=1.5,
            )

    def test_vote_confidence_validation_negative(self) -> None:
        """Test that negative confidence raises error."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            Vote(
                agent_id="agent-1",
                choice="x",
                confidence=-0.1,
            )

    def test_vote_boundary_values(self) -> None:
        """Test confidence at boundaries."""
        vote_low = Vote(agent_id="a", choice="x", confidence=0.0)
        vote_high = Vote(agent_id="b", choice="y", confidence=1.0)
        assert vote_low.confidence == 0.0
        assert vote_high.confidence == 1.0


class TestVoteResult:
    """Tests for VoteResult dataclass."""

    def test_from_votes_clear_winner(self) -> None:
        """Test tallying votes with clear winner."""
        votes = [
            Vote(agent_id="a", choice="option_1", confidence=0.9),
            Vote(agent_id="b", choice="option_1", confidence=0.8),
            Vote(agent_id="c", choice="option_2", confidence=0.7),
        ]
        result = VoteResult.from_votes(votes, threshold=0.5)

        assert result.consensus_reached is True
        assert result.winner == "option_1"
        assert result.vote_counts["option_1"] == 2
        assert result.vote_counts["option_2"] == 1
        assert abs(result.total_confidence - 1.7) < 0.001  # 0.9 + 0.8

    def test_from_votes_no_consensus(self) -> None:
        """Test tallying votes without consensus."""
        votes = [
            Vote(agent_id="a", choice="option_1", confidence=0.9),
            Vote(agent_id="b", choice="option_2", confidence=0.8),
            Vote(agent_id="c", choice="option_3", confidence=0.7),
        ]
        result = VoteResult.from_votes(votes, threshold=0.5)

        assert result.consensus_reached is False
        assert result.winner is None

    def test_from_votes_high_threshold(self) -> None:
        """Test with high threshold not met."""
        votes = [
            Vote(agent_id="a", choice="option_1", confidence=0.9),
            Vote(agent_id="b", choice="option_1", confidence=0.8),
            Vote(agent_id="c", choice="option_2", confidence=0.7),
        ]
        result = VoteResult.from_votes(votes, threshold=0.8)

        assert result.consensus_reached is False
        assert result.winner is None

    def test_from_votes_unanimous(self) -> None:
        """Test unanimous vote."""
        votes = [
            Vote(agent_id="a", choice="option_1", confidence=0.9),
            Vote(agent_id="b", choice="option_1", confidence=0.85),
            Vote(agent_id="c", choice="option_1", confidence=0.95),
        ]
        result = VoteResult.from_votes(votes, threshold=0.5)

        assert result.consensus_reached is True
        assert result.winner == "option_1"
        assert result.vote_counts["option_1"] == 3
        assert result.total_confidence == 2.7

    def test_from_votes_empty(self) -> None:
        """Test with no votes."""
        result = VoteResult.from_votes([], threshold=0.5)

        assert result.consensus_reached is False
        assert result.winner is None
        assert result.vote_counts == {}

    def test_vote_result_threshold_stored(self) -> None:
        """Test that threshold is stored in result."""
        votes = [Vote(agent_id="a", choice="x", confidence=1.0)]
        result = VoteResult.from_votes(votes, threshold=0.75)
        assert result.threshold == 0.75


class TestCoordinationResult:
    """Tests for CoordinationResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful coordination result."""
        result = CoordinationResult(
            session_id="session-001",
            success=True,
            participating_agents=("primary", "critic", "planner"),
            messages_exchanged=15,
            artifact_id="artifact-123",
            final_decision="Implement feature X",
            reasoning="All agents agreed on approach.",
            duration_ms=5000,
        )
        assert result.success is True
        assert len(result.participating_agents) == 3
        assert result.artifact_id == "artifact-123"
        assert result.duration_ms == 5000

    def test_failure_result(self) -> None:
        """Test failed coordination result."""
        result = CoordinationResult(
            session_id="session-002",
            success=False,
            participating_agents=("primary",),
            messages_exchanged=3,
            errors=("Timeout waiting for agents", "Critic unavailable"),
            duration_ms=30000,
        )
        assert result.success is False
        assert len(result.errors) == 2

    def test_result_with_votes(self) -> None:
        """Test result including vote results."""
        votes = [
            Vote(agent_id="a", choice="X", confidence=0.9),
            Vote(agent_id="b", choice="X", confidence=0.8),
        ]
        vote_result = VoteResult.from_votes(votes)

        result = CoordinationResult(
            session_id="session-003",
            success=True,
            participating_agents=("a", "b"),
            messages_exchanged=10,
            votes=vote_result,
            final_decision="X",
        )
        assert result.votes is not None
        assert result.votes.winner == "X"
