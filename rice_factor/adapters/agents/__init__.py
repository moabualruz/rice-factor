"""Agent coordination adapters.

This package contains implementations of the CoordinatorPort protocol
for different run modes.
"""

from rice_factor.adapters.agents.base import BaseCoordinator
from rice_factor.adapters.agents.hybrid_mode import HybridCoordinator
from rice_factor.adapters.agents.orchestrator_mode import OrchestratorCoordinator
from rice_factor.adapters.agents.role_locked_mode import RoleLockedCoordinator
from rice_factor.adapters.agents.solo_mode import SoloCoordinator
from rice_factor.adapters.agents.voting_mode import VotingCoordinator

__all__ = [
    "BaseCoordinator",
    "HybridCoordinator",
    "OrchestratorCoordinator",
    "RoleLockedCoordinator",
    "SoloCoordinator",
    "VotingCoordinator",
]
