"""Run mode configuration for multi-agent orchestration.

This module handles loading and validating run mode configurations from YAML files.
Run mode is chosen before execution and cannot change mid-run.
"""

import contextlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from rice_factor.domain.models.agent import AgentCapability, AgentConfig, AgentRole


class RunMode(str, Enum):
    """Available run modes for agent coordination.

    Each mode defines a different topology for agent collaboration.
    """

    # Mode A - Single agent with full authority
    SOLO = "solo"

    # Mode B - Orchestrator delegates to sub-agents
    ORCHESTRATOR = "orchestrator"

    # Mode C - Multiple agents vote on proposals
    VOTING = "voting"

    # Mode D - Specialized agents with fixed roles
    ROLE_LOCKED = "role_locked"

    # Mode E - Combination of modes
    HYBRID = "hybrid"


class CoordinationRule(str, Enum):
    """Rules that govern agent coordination."""

    # Authority rules
    ONLY_PRIMARY_EMITS_ARTIFACTS = "only_primary_emits_artifacts"
    SINGLE_AUTHORITY = "single_authority"

    # Review rules
    CRITICS_MUST_REVIEW_BEFORE_APPROVAL = "critics_must_review_before_approval"
    MANDATORY_CRITIC_REVIEW = "mandatory_critic_review"

    # Interaction rules
    SPECIALISTS_ANSWER_ONLY_WHEN_ASKED = "specialists_answer_only_when_asked"
    NO_FREE_FORM_CHAT = "no_free_form_chat"

    # Voting rules
    MAJORITY_WINS = "majority_wins"
    CONSENSUS_REQUIRED = "consensus_required"


@dataclass(frozen=True)
class RunModeConfig:
    """Configuration for a run mode session.

    This is loaded from a YAML file and frozen for the duration of execution.

    Attributes:
        mode: The run mode to use.
        authority_agent: ID of the agent with authority to emit artifacts.
        agents: Configuration for all participating agents.
        rules: Coordination rules in effect.
        voting_threshold: Threshold for consensus in voting mode (0.0-1.0).
        max_rounds: Maximum coordination rounds before timeout.
        phase_modes: For hybrid mode, mapping of phases to modes.
    """

    mode: RunMode
    authority_agent: str
    agents: tuple[AgentConfig, ...]
    rules: frozenset[CoordinationRule] = field(
        default_factory=lambda: frozenset({CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS})
    )
    voting_threshold: float = 0.5
    max_rounds: int = 10
    phase_modes: dict[str, RunMode] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration."""
        # Ensure authority agent exists
        agent_ids = {a.agent_id for a in self.agents}
        if self.authority_agent not in agent_ids:
            raise ValueError(
                f"Authority agent '{self.authority_agent}' not found in agents list"
            )

        # Ensure authority agent can emit artifacts
        authority = self.get_agent(self.authority_agent)
        if authority and not authority.can_emit_artifacts():
            raise ValueError(
                f"Authority agent '{self.authority_agent}' does not have "
                "EMIT_ARTIFACTS capability"
            )

        # Validate voting threshold
        if not 0.0 <= self.voting_threshold <= 1.0:
            raise ValueError(
                f"Voting threshold must be between 0.0 and 1.0, got {self.voting_threshold}"
            )

    def get_agent(self, agent_id: str) -> AgentConfig | None:
        """Get an agent configuration by ID.

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            AgentConfig if found, None otherwise.
        """
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None

    def get_agents_by_role(self, role: AgentRole) -> list[AgentConfig]:
        """Get all agents with a specific role.

        Args:
            role: The role to filter by.

        Returns:
            List of matching agent configurations.
        """
        return [a for a in self.agents if a.role == role]

    def has_rule(self, rule: CoordinationRule) -> bool:
        """Check if a coordination rule is active.

        Args:
            rule: The rule to check.

        Returns:
            True if the rule is in effect.
        """
        return rule in self.rules

    @classmethod
    def solo_mode(cls, model: str = "default") -> "RunModeConfig":
        """Create a default solo mode configuration.

        Args:
            model: The LLM model to use.

        Returns:
            RunModeConfig for solo mode.
        """
        primary = AgentConfig(
            agent_id="primary",
            role=AgentRole.PRIMARY,
            model=model,
        )
        return cls(
            mode=RunMode.SOLO,
            authority_agent="primary",
            agents=(primary,),
            rules=frozenset({CoordinationRule.SINGLE_AUTHORITY}),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunModeConfig":
        """Create configuration from a dictionary.

        Args:
            data: Configuration dictionary (typically from YAML).

        Returns:
            RunModeConfig instance.

        Raises:
            ValueError: If configuration is invalid.
        """
        mode_str = data.get("mode", "solo")
        try:
            mode = RunMode(mode_str)
        except ValueError as e:
            raise ValueError(f"Unknown run mode: {mode_str}") from e

        # Parse agents
        agents_data = data.get("agents", {})
        agents: list[AgentConfig] = []

        for agent_id, agent_data in agents_data.items():
            if isinstance(agent_data, dict):
                role_str = agent_data.get("role", "primary")
                try:
                    role = AgentRole(role_str)
                except ValueError as e:
                    raise ValueError(f"Unknown agent role: {role_str}") from e

                # Parse capabilities if provided
                capabilities: set[AgentCapability] = set()
                for cap_str in agent_data.get("capabilities", []):
                    try:
                        capabilities.add(AgentCapability(cap_str))
                    except ValueError as e:
                        raise ValueError(f"Unknown capability: {cap_str}") from e

                agents.append(
                    AgentConfig(
                        agent_id=agent_id,
                        role=role,
                        model=agent_data.get("model", "default"),
                        capabilities=frozenset(capabilities) if capabilities else frozenset(),
                        scope=agent_data.get("scope"),
                        system_prompt=agent_data.get("system_prompt"),
                    )
                )

        # Default to solo mode if no agents defined
        if not agents:
            agents = [
                AgentConfig(
                    agent_id="primary",
                    role=AgentRole.PRIMARY,
                )
            ]

        # Parse authority
        authority_data = data.get("authority", {})
        authority_agent = authority_data.get("agent", "primary")

        # Parse rules (skip unknown rules silently)
        rules: set[CoordinationRule] = set()
        for rule_str in data.get("rules", []):
            with contextlib.suppress(ValueError):
                rules.add(CoordinationRule(rule_str))

        # Default rule
        if not rules:
            rules.add(CoordinationRule.ONLY_PRIMARY_EMITS_ARTIFACTS)

        # Parse phase modes for hybrid
        phase_modes: dict[str, RunMode] = {}
        for phase, phase_mode_str in data.get("phase_modes", {}).items():
            try:
                phase_modes[phase] = RunMode(phase_mode_str)
            except ValueError as e:
                raise ValueError(f"Unknown mode for phase {phase}: {phase_mode_str}") from e

        return cls(
            mode=mode,
            authority_agent=authority_agent,
            agents=tuple(agents),
            rules=frozenset(rules),
            voting_threshold=data.get("voting_threshold", 0.5),
            max_rounds=data.get("max_rounds", 10),
            phase_modes=phase_modes,
        )

    @classmethod
    def from_file(cls, path: Path) -> "RunModeConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            RunModeConfig instance.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the configuration is invalid.
        """
        if not path.exists():
            raise FileNotFoundError(f"Run mode config not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid run mode config: expected dict, got {type(data)}")

        return cls.from_dict(data)

    @classmethod
    def from_project(cls, project_root: Path | None = None) -> "RunModeConfig":
        """Load configuration from the project's .project directory.

        Looks for .project/run_mode.yaml. Falls back to solo mode if not found.

        Args:
            project_root: Root of the project. Defaults to current directory.

        Returns:
            RunModeConfig instance.
        """
        root = project_root or Path.cwd()
        config_path = root / ".project" / "run_mode.yaml"

        if config_path.exists():
            return cls.from_file(config_path)

        # Fall back to solo mode
        return cls.solo_mode()

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary representation suitable for YAML serialization.
        """
        agents_dict: dict[str, dict[str, Any]] = {}
        for agent in self.agents:
            agent_data: dict[str, Any] = {
                "role": agent.role.value,
            }
            if agent.model != "default":
                agent_data["model"] = agent.model
            if agent.capabilities:
                agent_data["capabilities"] = [c.value for c in agent.capabilities]
            if agent.scope:
                agent_data["scope"] = agent.scope
            if agent.system_prompt:
                agent_data["system_prompt"] = agent.system_prompt

            agents_dict[agent.agent_id] = agent_data

        result: dict[str, Any] = {
            "mode": self.mode.value,
            "authority": {"agent": self.authority_agent},
            "agents": agents_dict,
            "rules": [r.value for r in self.rules],
        }

        if self.voting_threshold != 0.5:
            result["voting_threshold"] = self.voting_threshold
        if self.max_rounds != 10:
            result["max_rounds"] = self.max_rounds
        if self.phase_modes:
            result["phase_modes"] = {p: m.value for p, m in self.phase_modes.items()}

        return result

    def to_yaml(self) -> str:
        """Serialize configuration to YAML string.

        Returns:
            YAML representation of the configuration.
        """
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
