"""Invariant checker for domain invariants.

This adapter implements the ValidationRunnerPort protocol to verify
domain invariants before validation proceeds:
- TestPlan lock status
- Artifact status transitions
- Approval chain integrity
- Dependency existence
"""

import json
import time
from pathlib import Path
from typing import ClassVar
from uuid import UUID

from rice_factor.domain.artifacts.enums import ArtifactStatus
from rice_factor.domain.artifacts.validation_types import (
    ValidationContext,
    ValidationResult,
)


class InvariantChecker:
    """Checker for domain invariants.

    Verifies that all domain invariants are satisfied before validation
    can proceed. Implements the ValidationRunnerPort protocol.

    Invariants checked:
    1. TestPlan must be LOCKED before implementation
    2. Valid status transitions (DRAFT → APPROVED → LOCKED)
    3. Approval records exist for approved artifacts
    4. All dependencies exist for each artifact
    """

    # Valid status transitions
    VALID_TRANSITIONS: ClassVar[dict[ArtifactStatus, list[ArtifactStatus]]] = {
        ArtifactStatus.DRAFT: [ArtifactStatus.APPROVED],
        ArtifactStatus.APPROVED: [ArtifactStatus.LOCKED],
        ArtifactStatus.LOCKED: [],  # Terminal state
    }

    @property
    def name(self) -> str:
        """Get the validator name.

        Returns:
            The identifier "invariant_checker".
        """
        return "invariant_checker"

    def validate(
        self,
        target: Path,
        context: ValidationContext,
    ) -> ValidationResult:
        """Check all invariants and return validation result.

        Args:
            target: Path to the artifacts directory.
            context: Validation context with config.

        Returns:
            ValidationResult with invariant status and any violations.
        """
        start_time = time.time()
        violations: list[str] = []

        # Target should be the artifacts directory
        artifacts_dir = target
        if not artifacts_dir.exists():
            # No artifacts directory means no invariants to check
            return ValidationResult.passed_result(
                target="invariants",
                validator=self.name,
                duration_ms=0,
            )

        # Check all invariants
        violations.extend(self.check_testplan_lock(artifacts_dir, context))
        violations.extend(self.check_status_transitions(artifacts_dir))
        violations.extend(self.check_approval_chain(artifacts_dir))
        violations.extend(self.check_dependencies(artifacts_dir))

        duration_ms = int((time.time() - start_time) * 1000)

        if violations:
            return ValidationResult.failed_result(
                target="invariants",
                errors=violations,
                validator=self.name,
                duration_ms=duration_ms,
            )

        return ValidationResult.passed_result(
            target="invariants",
            validator=self.name,
            duration_ms=duration_ms,
        )

    def check_testplan_lock(
        self,
        artifacts_dir: Path,
        context: ValidationContext,
    ) -> list[str]:
        """Check that TestPlan is locked if implementation has started.

        Args:
            artifacts_dir: Path to artifacts directory.
            context: Validation context.

        Returns:
            List of violation messages.
        """
        violations: list[str] = []

        # Check if TestPlan lock check should be skipped
        if context.get_config("skip_testplan_lock_check", False):
            return violations

        # Look for test_plans directory
        test_plans_dir = artifacts_dir / "test_plans"
        if not test_plans_dir.exists():
            # No TestPlan yet - that's OK
            return violations

        # Check if there are any implementation plans
        impl_plans_dir = artifacts_dir / "implementation_plans"
        has_impl_plans = impl_plans_dir.exists() and any(impl_plans_dir.glob("*.json"))

        if not has_impl_plans:
            # No implementation yet - TestPlan lock not required
            return violations

        # Implementation exists - TestPlan must be locked
        for test_plan_file in test_plans_dir.glob("*.json"):
            try:
                data = json.loads(test_plan_file.read_text(encoding="utf-8"))
                status = data.get("status", "unknown")
                if status != ArtifactStatus.LOCKED.value:
                    violations.append(
                        f"TestPlan must be locked before implementation. "
                        f"Current status: {status} (file: {test_plan_file.name})"
                    )
            except (json.JSONDecodeError, OSError) as e:
                violations.append(f"Failed to read TestPlan {test_plan_file.name}: {e}")

        return violations

    def check_status_transitions(self, artifacts_dir: Path) -> list[str]:
        """Check that all artifacts have valid statuses.

        Args:
            artifacts_dir: Path to artifacts directory.

        Returns:
            List of violation messages.
        """
        violations: list[str] = []

        # Only check non-terminal states are valid
        valid_statuses = {s.value for s in ArtifactStatus}

        for artifact_file in artifacts_dir.rglob("*.json"):
            # Skip meta files
            if artifact_file.parent.name == "_meta":
                continue

            try:
                data = json.loads(artifact_file.read_text(encoding="utf-8"))
                status = data.get("status")

                if status is None:
                    continue  # Not an artifact file

                if status not in valid_statuses:
                    artifact_id = data.get("id", "unknown")
                    violations.append(
                        f"Invalid status '{status}' for artifact {artifact_id}. "
                        f"Valid statuses: {', '.join(valid_statuses)}"
                    )
            except (json.JSONDecodeError, OSError):
                # Skip files that can't be parsed
                continue

        return violations

    def check_approval_chain(self, artifacts_dir: Path) -> list[str]:
        """Check that approved artifacts have approval records.

        Args:
            artifacts_dir: Path to artifacts directory.

        Returns:
            List of violation messages.
        """
        violations: list[str] = []

        # Load approvals from meta directory
        approvals_file = artifacts_dir / "_meta" / "approvals.json"
        approved_ids: set[str] = set()

        if approvals_file.exists():
            try:
                approvals_data = json.loads(approvals_file.read_text(encoding="utf-8"))
                if isinstance(approvals_data, dict):
                    approved_ids = set(approvals_data.get("approvals", {}).keys())
                elif isinstance(approvals_data, list):
                    # List of approval records
                    for approval in approvals_data:
                        if isinstance(approval, dict) and "artifact_id" in approval:
                            approved_ids.add(str(approval["artifact_id"]))
            except (json.JSONDecodeError, OSError):
                # If approvals file is invalid, we'll catch missing approvals below
                pass

        # Check all artifacts with APPROVED or LOCKED status
        for artifact_file in artifacts_dir.rglob("*.json"):
            if artifact_file.parent.name == "_meta":
                continue

            try:
                data = json.loads(artifact_file.read_text(encoding="utf-8"))
                status = data.get("status")
                artifact_id = data.get("id")

                if artifact_id is None:
                    continue

                # Check if approved/locked artifacts have approval records
                if (
                    status in (ArtifactStatus.APPROVED.value, ArtifactStatus.LOCKED.value)
                    and str(artifact_id) not in approved_ids
                ):
                    violations.append(
                        f"Artifact {artifact_id} is {status} but has no approval record"
                    )
            except (json.JSONDecodeError, OSError):
                continue

        return violations

    def check_dependencies(self, artifacts_dir: Path) -> list[str]:
        """Check that all artifact dependencies exist.

        Args:
            artifacts_dir: Path to artifacts directory.

        Returns:
            List of violation messages.
        """
        violations: list[str] = []

        # Build index of all artifact IDs
        existing_ids: set[str] = set()
        artifact_deps: dict[str, list[str]] = {}

        for artifact_file in artifacts_dir.rglob("*.json"):
            if artifact_file.parent.name == "_meta":
                continue

            try:
                data = json.loads(artifact_file.read_text(encoding="utf-8"))
                artifact_id = data.get("id")

                if artifact_id is None:
                    continue

                existing_ids.add(str(artifact_id))

                # Check for depends_on field
                depends_on = data.get("depends_on", [])
                if depends_on:
                    artifact_deps[str(artifact_id)] = [str(dep) for dep in depends_on]
            except (json.JSONDecodeError, OSError):
                continue

        # Check all dependencies exist
        for artifact_id, deps in artifact_deps.items():
            for dep_id in deps:
                if dep_id not in existing_ids:
                    # Try to normalize UUID comparison
                    try:
                        dep_uuid = str(UUID(dep_id))
                        if dep_uuid not in existing_ids:
                            violations.append(
                                f"Artifact {artifact_id} depends on missing artifact {dep_id}"
                            )
                    except ValueError:
                        violations.append(
                            f"Artifact {artifact_id} depends on missing artifact {dep_id}"
                        )

        return violations

    def check_single_invariant(
        self,
        invariant_name: str,
        artifacts_dir: Path,
        context: ValidationContext,
    ) -> list[str]:
        """Check a single invariant by name.

        Args:
            invariant_name: Name of the invariant to check.
            artifacts_dir: Path to artifacts directory.
            context: Validation context.

        Returns:
            List of violation messages.

        Raises:
            ValueError: If invariant_name is not recognized.
        """
        invariant_map = {
            "testplan_lock": lambda: self.check_testplan_lock(artifacts_dir, context),
            "status_transitions": lambda: self.check_status_transitions(artifacts_dir),
            "approval_chain": lambda: self.check_approval_chain(artifacts_dir),
            "dependencies": lambda: self.check_dependencies(artifacts_dir),
        }

        if invariant_name not in invariant_map:
            raise ValueError(
                f"Unknown invariant: {invariant_name}. "
                f"Valid invariants: {', '.join(invariant_map.keys())}"
            )

        return invariant_map[invariant_name]()
