"""Project management API routes.

Provides endpoints for project information and phase detection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from rice_factor_web.backend.config import get_settings
from rice_factor_web.backend.deps import ServiceAdapter

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/current")
async def get_current_project(
    adapter: ServiceAdapter,
) -> dict[str, Any]:
    """Get information about the current project.

    Returns project root, initialization status, and basic info.

    Args:
        adapter: Service adapter dependency.

    Returns:
        Project information.
    """
    settings = get_settings()
    project_root = Path(settings.project_root).resolve()

    # Check for rice-factor initialization markers
    project_dir = project_root / ".project"
    artifacts_dir = project_root / "artifacts"

    is_initialized = project_dir.exists() or artifacts_dir.exists()

    # Try to get project name from .project/config.yaml or directory name
    project_name = project_root.name

    if project_dir.exists():
        config_file = project_dir / "config.yaml"
        if config_file.exists():
            try:
                import yaml

                with open(config_file) as f:
                    config = yaml.safe_load(f)
                    project_name = config.get("project_name", project_name)
            except Exception:
                pass

    return {
        "name": project_name,
        "root": str(project_root),
        "initialized": is_initialized,
        "has_artifacts": artifacts_dir.exists(),
        "has_project_config": project_dir.exists(),
    }


@router.get("/phase")
async def get_current_phase(
    adapter: ServiceAdapter,
) -> dict[str, Any]:
    """Get the current project phase.

    Detects the current development phase based on existing artifacts.

    Args:
        adapter: Service adapter dependency.

    Returns:
        Phase information including name and description.
    """
    from rice_factor.domain.artifacts.enums import ArtifactType

    # Count artifacts by type to determine phase
    artifact_counts: dict[str, int] = {}
    for atype in ArtifactType:
        try:
            count = len(list(adapter.storage.list_by_type(atype)))
            if count > 0:
                artifact_counts[atype.value] = count
        except Exception:
            pass

    # Determine phase based on what exists
    phase_name = "init"
    phase_description = "Project not initialized"
    available_commands: list[str] = ["init"]

    if not artifact_counts:
        if adapter.is_initialized():
            phase_name = "planning"
            phase_description = "Ready to create project plan"
            available_commands = ["plan project"]
    elif "project_plan" in artifact_counts:
        if "test_plan" not in artifact_counts:
            phase_name = "architecture"
            phase_description = "Project plan created, ready for test planning"
            available_commands = ["plan tests", "scaffold"]
        elif "implementation_plan" not in artifact_counts:
            phase_name = "testing"
            phase_description = "Test plan created, ready for implementation"
            available_commands = ["lock tests", "plan impl"]
        else:
            phase_name = "implementation"
            phase_description = "Implementation in progress"
            available_commands = ["impl", "apply", "test", "plan refactor"]

    return {
        "phase": phase_name,
        "description": phase_description,
        "artifact_counts": artifact_counts,
        "available_commands": available_commands,
    }


@router.get("/config")
async def get_project_config(
    adapter: ServiceAdapter,
) -> dict[str, Any]:
    """Get project configuration from .project/ directory.

    Args:
        adapter: Service adapter dependency.

    Returns:
        Project configuration or empty dict if not found.
    """
    project_dir = adapter.project_root / ".project"

    if not project_dir.exists():
        return {"configured": False, "config": {}}

    config: dict[str, Any] = {"configured": True, "config": {}}

    # Read config.yaml
    config_file = project_dir / "config.yaml"
    if config_file.exists():
        try:
            import yaml

            with open(config_file) as f:
                config["config"] = yaml.safe_load(f) or {}
        except Exception:
            pass

    # Check for other project files
    config["has_decisions"] = (project_dir / "decisions.md").exists()
    config["has_glossary"] = (project_dir / "glossary.yaml").exists()
    config["has_architecture"] = (project_dir / "architecture.md").exists()

    return config


@router.get("")
async def list_projects() -> dict[str, Any]:
    """List known projects.

    Discovers projects from parent directories that have rice-factor markers.

    Returns:
        List of project information.
    """
    settings = get_settings()
    current_root = Path(settings.project_root).resolve()

    projects = []

    # Add current project
    current_project = {
        "root": str(current_root),
        "name": current_root.name,
        "is_current": True,
        "initialized": (current_root / ".project").exists() or (current_root / "artifacts").exists(),
    }
    projects.append(current_project)

    # Look in parent directory for sibling projects
    parent = current_root.parent
    if parent.exists():
        for child in parent.iterdir():
            if child.is_dir() and child != current_root:
                # Check if it's a rice-factor project
                if (child / ".project").exists() or (child / "artifacts").exists():
                    projects.append({
                        "root": str(child),
                        "name": child.name,
                        "is_current": False,
                        "initialized": True,
                    })

    return {
        "projects": projects,
        "current": str(current_root),
    }


@router.post("/switch")
async def switch_project(
    request: dict[str, str],
) -> dict[str, Any]:
    """Switch to a different project.

    Note: This requires restarting the server or reinitializing services.
    For now, this returns information about what would happen.

    Args:
        request: Contains 'root' key with new project path.

    Returns:
        Switch confirmation or error.
    """
    from fastapi import HTTPException, status

    new_root = request.get("root")
    if not new_root:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'root' in request body",
        )

    new_path = Path(new_root).resolve()
    if not new_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project path does not exist: {new_root}",
        )

    # Check if it's a rice-factor project
    is_rf_project = (new_path / ".project").exists() or (new_path / "artifacts").exists()

    return {
        "switched": False,
        "message": "Project switching requires server restart. Set RF_PROJECT_PATH environment variable and restart.",
        "new_root": str(new_path),
        "is_rice_factor_project": is_rf_project,
    }

@router.post("/init")
async def initialize_project(
    request: dict[str, Any] = {},  # noqa: B006
    adapter: ServiceAdapter = None,
) -> dict[str, Any]:
    """Initialize the current project.
    
    Creates .project/ directory and template files.
    """
    from fastapi import HTTPException, status
    from rice_factor.domain.services.init_service import InitService
    from rice_factor.domain.services.questionnaire import QuestionnaireResponse

    settings = get_settings()
    project_root = Path(settings.project_root).resolve()
    service = InitService(project_root=project_root)

    if service.is_initialized():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project already initialized",
        )

    try:
        # Convert request dict to QuestionnaireResponse
        # If request is empty, use defaults
        responses = QuestionnaireResponse(**request.get("responses", {}))
        
        created_files = service.initialize(responses=responses)
        
        return {
            "initialized": True,
            "project_dir": str(service.project_dir),
            "files_created": [str(f.name) for f in created_files],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Initialization failed: {str(e)}",
        )
