"""Agent models for multi-agent orchestration.

This module defines the core agent models used in rice-factor's multi-agent
coordination system. Agents are LLM instances with roles, scopes, and permissions.

Key principle: Only one agent can have authority at a time (emit artifacts).
All other agents support, propose, critique, or analyze.
"""

from dataclasses import dataclass, field
from enum import Enum


class AgentRole(str, Enum):
    """Canonical agent roles as defined in the spec.

    Roles are orthogonal and composable. The PRIMARY role has
    authority to emit artifacts; all others are advisory.
    """

    # Authority role - exactly one per run
    PRIMARY = "primary"

    # Advisory roles
    PLANNER = "planner"
    CRITIC = "critic"
    DOMAIN_SPECIALIST = "domain_specialist"
    REFACTOR_ANALYST = "refactor_analyst"
    TEST_STRATEGIST = "test_strategist"

    # Generic role for voting mode
    GENERIC = "generic"

    # Orchestrator role (can delegate to sub-agents)
    ORCHESTRATOR = "orchestrator"


class AgentCapability(str, Enum):
    """Capabilities that can be assigned to agents.

    These define what actions an agent can perform within the system.
    Note: No agent can write files, execute tools, or approve artifacts directly.
    """

    # Artifact-related
    EMIT_ARTIFACTS = "emit_artifacts"
    PROPOSE_ARTIFACTS = "propose_artifacts"
    REVIEW_ARTIFACTS = "review_artifacts"

    # Planning
    DECOMPOSE_GOALS = "decompose_goals"
    SUGGEST_STRUCTURE = "suggest_structure"

    # Analysis
    IDENTIFY_RISKS = "identify_risks"
    EVALUATE_SAFETY = "evaluate_safety"
    ANALYZE_DOMAIN = "analyze_domain"

    # Test-related
    EVALUATE_TEST_COVERAGE = "evaluate_test_coverage"
    IDENTIFY_MISSING_TESTS = "identify_missing_tests"

    # Coordination
    DELEGATE_TASKS = "delegate_tasks"
    SYNTHESIZE_RESULTS = "synthesize_results"
    VOTE = "vote"


# Role to default capabilities mapping
ROLE_CAPABILITIES: dict[AgentRole, set[AgentCapability]] = {
    AgentRole.PRIMARY: {
        AgentCapability.EMIT_ARTIFACTS,
        AgentCapability.SYNTHESIZE_RESULTS,
    },
    AgentRole.ORCHESTRATOR: {
        AgentCapability.EMIT_ARTIFACTS,
        AgentCapability.DELEGATE_TASKS,
        AgentCapability.SYNTHESIZE_RESULTS,
    },
    AgentRole.PLANNER: {
        AgentCapability.PROPOSE_ARTIFACTS,
        AgentCapability.DECOMPOSE_GOALS,
        AgentCapability.SUGGEST_STRUCTURE,
    },
    AgentRole.CRITIC: {
        AgentCapability.REVIEW_ARTIFACTS,
        AgentCapability.IDENTIFY_RISKS,
    },
    AgentRole.DOMAIN_SPECIALIST: {
        AgentCapability.ANALYZE_DOMAIN,
        AgentCapability.REVIEW_ARTIFACTS,
    },
    AgentRole.REFACTOR_ANALYST: {
        AgentCapability.EVALUATE_SAFETY,
        AgentCapability.IDENTIFY_RISKS,
        AgentCapability.REVIEW_ARTIFACTS,
    },
    AgentRole.TEST_STRATEGIST: {
        AgentCapability.EVALUATE_TEST_COVERAGE,
        AgentCapability.IDENTIFY_MISSING_TESTS,
        AgentCapability.REVIEW_ARTIFACTS,
    },
    AgentRole.GENERIC: {
        AgentCapability.PROPOSE_ARTIFACTS,
        AgentCapability.VOTE,
    },
}


@dataclass(frozen=True)
class AgentConfig:
    """Configuration for a single agent.

    Attributes:
        agent_id: Unique identifier for this agent instance.
        role: The role this agent plays.
        model: The LLM model to use (e.g., "claude-3-opus", "gpt-4").
        capabilities: Set of capabilities. Defaults based on role if not provided.
        scope: Optional scope restriction (e.g., "rust", "security").
        system_prompt: Optional custom system prompt override.
    """

    agent_id: str
    role: AgentRole
    model: str = "default"
    capabilities: frozenset[AgentCapability] = field(default_factory=frozenset)
    scope: str | None = None
    system_prompt: str | None = None

    def __post_init__(self) -> None:
        """Set default capabilities based on role if not provided."""
        if not self.capabilities:
            # Use object.__setattr__ because dataclass is frozen
            object.__setattr__(
                self,
                "capabilities",
                frozenset(ROLE_CAPABILITIES.get(self.role, set())),
            )

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if this agent has a specific capability.

        Args:
            capability: The capability to check for.

        Returns:
            True if the agent has the capability.
        """
        return capability in self.capabilities

    def can_emit_artifacts(self) -> bool:
        """Check if this agent can emit authoritative artifacts.

        Returns:
            True if the agent has artifact emission capability.
        """
        return self.has_capability(AgentCapability.EMIT_ARTIFACTS)


@dataclass(frozen=True)
class Agent:
    """Runtime representation of an agent.

    This combines the static configuration with runtime state.

    Attributes:
        config: The agent's configuration.
        is_active: Whether the agent is currently active.
        task_count: Number of tasks completed by this agent.
    """

    config: AgentConfig
    is_active: bool = True
    task_count: int = 0

    @property
    def agent_id(self) -> str:
        """Get the agent's unique identifier."""
        return self.config.agent_id

    @property
    def role(self) -> AgentRole:
        """Get the agent's role."""
        return self.config.role

    def with_task_completed(self) -> "Agent":
        """Return a new Agent with incremented task count.

        Returns:
            New Agent instance with task_count + 1.
        """
        return Agent(
            config=self.config,
            is_active=self.is_active,
            task_count=self.task_count + 1,
        )

    def deactivate(self) -> "Agent":
        """Return a new Agent that is deactivated.

        Returns:
            New Agent instance with is_active=False.
        """
        return Agent(
            config=self.config,
            is_active=False,
            task_count=self.task_count,
        )
