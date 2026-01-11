"""Fixtures for integration tests."""

from pathlib import Path

import pytest

from rice_factor.adapters.llm.stub import StubLLMAdapter
from rice_factor.adapters.storage.approvals import ApprovalsTracker
from rice_factor.adapters.storage.filesystem import FilesystemStorageAdapter
from rice_factor.domain.artifacts.enums import ArtifactStatus, ArtifactType, CreatedBy
from rice_factor.domain.artifacts.envelope import ArtifactEnvelope
from rice_factor.domain.services.artifact_service import ArtifactService


@pytest.fixture
def mvp_project(tmp_path: Path) -> Path:
    """Create a minimal project structure for MVP tests.

    Returns:
        Path to the project root with .project directory.
    """
    project_dir = tmp_path / "mvp_project"
    project_dir.mkdir()

    # Create .project directory with intake files
    project_config = project_dir / ".project"
    project_config.mkdir()

    # Create all 6 required intake files with minimal content
    (project_config / "requirements.md").write_text(
        "# Requirements\n\n- Feature 1: Basic functionality\n"
    )
    (project_config / "constraints.md").write_text(
        "# Constraints\n\n- Must use Python 3.11+\n"
    )
    (project_config / "glossary.md").write_text(
        "# Glossary\n\n| Term | Definition |\n|------|------------|\n| API | Application Programming Interface |\n"
    )
    (project_config / "non_goals.md").write_text(
        "# Non-Goals\n\nNot in scope for this project.\n"
    )
    (project_config / "risks.md").write_text(
        "# Risks\n\nNo major risks identified.\n"
    )
    (project_config / "decisions.md").write_text(
        "# Decisions\n\nNo decisions recorded yet.\n"
    )

    # Create artifacts directory
    (project_dir / "artifacts").mkdir()

    # Create audit directory
    (project_dir / "audit").mkdir()

    return project_dir


@pytest.fixture
def stub_llm() -> StubLLMAdapter:
    """Return a stub LLM adapter for testing.

    Returns:
        StubLLMAdapter instance.
    """
    return StubLLMAdapter()


@pytest.fixture
def artifact_service(mvp_project: Path) -> ArtifactService:
    """Create an artifact service for the test project.

    Args:
        mvp_project: Path to the test project.

    Returns:
        ArtifactService instance.
    """
    artifacts_dir = mvp_project / "artifacts"
    storage = FilesystemStorageAdapter(artifacts_dir=artifacts_dir)
    approvals = ApprovalsTracker(artifacts_dir=artifacts_dir)
    return ArtifactService(storage=storage, approvals=approvals)


@pytest.fixture
def approved_project_plan(
    _mvp_project: Path, stub_llm: StubLLMAdapter, artifact_service: ArtifactService
) -> ArtifactEnvelope:
    """Create and approve a ProjectPlan artifact.

    Args:
        mvp_project: Path to the test project.
        stub_llm: Stub LLM adapter.
        artifact_service: Artifact service.

    Returns:
        Approved ProjectPlan artifact.
    """
    payload = stub_llm.generate_project_plan()
    artifact = ArtifactEnvelope(
        artifact_type=ArtifactType.PROJECT_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=payload,
    )
    # Save and approve
    artifact_service.save(artifact)
    artifact_service.approve(artifact.id)
    return artifact_service.load(artifact.id)


@pytest.fixture
def locked_test_plan(
    _mvp_project: Path, stub_llm: StubLLMAdapter, artifact_service: ArtifactService
) -> ArtifactEnvelope:
    """Create and lock a TestPlan artifact.

    Args:
        mvp_project: Path to the test project.
        stub_llm: Stub LLM adapter.
        artifact_service: Artifact service.

    Returns:
        Locked TestPlan artifact.
    """
    payload = stub_llm.generate_test_plan()
    artifact = ArtifactEnvelope(
        artifact_type=ArtifactType.TEST_PLAN,
        status=ArtifactStatus.DRAFT,
        created_by=CreatedBy.LLM,
        payload=payload,
    )
    # Save, approve, and lock
    artifact_service.save(artifact)
    artifact_service.approve(artifact.id)
    artifact_service.lock(artifact.id)
    return artifact_service.load(artifact.id)
