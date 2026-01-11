"""CI validation commands.

This module provides CLI commands for CI pipeline validation:
- rice-factor ci validate: Run full CI validation pipeline
- rice-factor ci validate-artifacts: Run artifact validation only
- rice-factor ci validate-approvals: Run approval verification only
- rice-factor ci validate-invariants: Run invariant enforcement only
- rice-factor ci validate-audit: Run audit verification only
"""

import json
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.ci import (
    ApprovalVerificationAdapter,
    ArtifactValidationAdapter,
    AuditVerificationAdapter,
    InvariantEnforcementAdapter,
)
from rice_factor.domain.ci import (
    CIPipeline,
    CIPipelineConfig,
    CIPipelineResult,
    CIStage,
)
from rice_factor.entrypoints.cli.utils import console, error, info, success

app = typer.Typer(
    name="ci",
    help="CI/CD validation commands.",
    no_args_is_help=True,
)


def _find_project_root(path: Path | None) -> Path:
    """Find the project root directory.

    Args:
        path: Starting path to search from. If None, uses CWD.

    Returns:
        Path to the project root (directory containing .project/).
    """
    start = path or Path.cwd()

    # Walk up looking for .project/
    current = start
    for _ in range(10):  # Max depth
        if (current / ".project").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent

    # No .project/ found, use starting path
    return start


def _create_pipeline(
    stages: list[CIStage] | None = None,
    stop_on_failure: bool = True,
    base_branch: str = "main",
) -> CIPipeline:
    """Create a CI pipeline with appropriate validators.

    Args:
        stages: Specific stages to run, or None for all.
        stop_on_failure: Whether to stop on first failure.
        base_branch: Base branch for comparing locked artifact changes.

    Returns:
        Configured CIPipeline instance.
    """
    config = CIPipelineConfig(
        stop_on_failure=stop_on_failure,
        stages_to_run=stages,
    )
    pipeline = CIPipeline(config=config)

    # Register available validators
    pipeline.register_stage(
        CIStage.ARTIFACT_VALIDATION,
        ArtifactValidationAdapter(base_branch=base_branch),
    )
    pipeline.register_stage(
        CIStage.APPROVAL_VERIFICATION,
        ApprovalVerificationAdapter(),
    )
    pipeline.register_stage(
        CIStage.INVARIANT_ENFORCEMENT,
        InvariantEnforcementAdapter(base_branch=base_branch),
    )
    pipeline.register_stage(
        CIStage.AUDIT_VERIFICATION,
        AuditVerificationAdapter(),
    )

    # Note: TEST_EXECUTION stage is handled by existing test runner infrastructure
    # and is not a CI validation stage

    return pipeline


def _display_result(result: CIPipelineResult, as_json: bool = False) -> None:
    """Display pipeline result.

    Args:
        result: The pipeline result to display.
        as_json: If True, output JSON. Otherwise, human-readable.
    """
    if as_json:
        # Use plain print() for JSON to avoid Rich formatting
        print(result.to_json())
        return

    # Human-readable output
    console.print()

    # Status header
    if result.passed:
        console.print(
            Panel(
                "[green]✓ CI Pipeline PASSED[/green]",
                style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[red]✗ CI Pipeline FAILED[/red]",
                style="red",
            )
        )

    # Stage results table
    table = Table(title="Stage Results")
    table.add_column("Stage", style="cyan")
    table.add_column("Status")
    table.add_column("Failures")
    table.add_column("Duration")

    for stage_result in result.stage_results:
        if stage_result.skipped:
            status = f"[dim]SKIPPED ({stage_result.skip_reason})[/dim]"
            failures = "-"
        elif stage_result.passed:
            status = "[green]PASSED[/green]"
            failures = "0"
        else:
            status = "[red]FAILED[/red]"
            failures = f"[red]{len(stage_result.failures)}[/red]"

        table.add_row(
            stage_result.stage.value.replace("_", " ").title(),
            status,
            failures,
            f"{stage_result.duration_ms:.0f}ms",
        )

    console.print(table)

    # Failure details
    if result.failure_count > 0:
        console.print()
        console.print(f"[red]Failures ({result.failure_count} total):[/red]")
        for stage_result in result.stage_results:
            for failure in stage_result.failures:
                console.print()
                console.print(f"  [bold red][{failure.code.value}][/bold red]")
                console.print(f"    {failure.message}")
                if failure.file_path:
                    console.print(f"    [dim]File: {failure.file_path}[/dim]")
                remediation = failure.remediation or failure.code.remediation
                console.print(f"    [cyan]Remediation:[/cyan] {remediation}")

    # Summary
    console.print()
    console.print(f"[dim]Total Duration: {result.total_duration_ms:.0f}ms[/dim]")


@app.command()
def validate(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON.",
    ),
    continue_on_failure: bool = typer.Option(
        False,
        "--continue-on-failure",
        help="Run all stages even if earlier stages fail.",
    ),
) -> None:
    """Run full CI validation pipeline.

    Executes all validation stages in order:
    1. Artifact Validation - Check artifact status and schema
    2. Approval Verification - Check all required approvals
    3. Invariant Enforcement - Check test locks, architecture rules
    4. Test Execution - Run tests
    5. Audit Verification - Verify audit trail integrity

    Exit code is 0 on success, 1 on failure.
    """
    project_root = _find_project_root(path)

    if not output_json:
        info(f"Running CI validation pipeline on {project_root}")

    pipeline = _create_pipeline(stop_on_failure=not continue_on_failure)
    result = pipeline.run(repo_root=project_root)

    _display_result(result, as_json=output_json)

    if not result.passed:
        raise typer.Exit(1)


@app.command(name="validate-artifacts")
def validate_artifacts(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON.",
    ),
) -> None:
    """Run artifact validation stage only.

    Validates:
    - No draft artifacts present
    - All artifacts pass schema validation
    - Locked artifacts not modified
    - Artifact hashes match content
    """
    project_root = _find_project_root(path)

    if not output_json:
        info("Running artifact validation stage")

    pipeline = _create_pipeline(stages=[CIStage.ARTIFACT_VALIDATION])
    result = pipeline.run(repo_root=project_root)

    _display_result(result, as_json=output_json)

    if not result.passed:
        raise typer.Exit(1)


@app.command(name="validate-approvals")
def validate_approvals(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON.",
    ),
) -> None:
    """Run approval verification stage only.

    Validates:
    - All required artifacts are approved
    - Approval metadata is complete
    - Approvals are not expired
    """
    project_root = _find_project_root(path)

    if not output_json:
        info("Running approval verification stage")

    pipeline = _create_pipeline(stages=[CIStage.APPROVAL_VERIFICATION])
    result = pipeline.run(repo_root=project_root)

    _display_result(result, as_json=output_json)

    if not result.passed:
        raise typer.Exit(1)


@app.command(name="validate-invariants")
def validate_invariants(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON.",
    ),
) -> None:
    """Run invariant enforcement stage only.

    Validates:
    - Tests not modified after lock
    - No unplanned code changes
    - Architecture rules not violated
    """
    project_root = _find_project_root(path)

    if not output_json:
        info("Running invariant enforcement stage")

    pipeline = _create_pipeline(stages=[CIStage.INVARIANT_ENFORCEMENT])
    result = pipeline.run(repo_root=project_root)

    _display_result(result, as_json=output_json)

    if not result.passed:
        raise typer.Exit(1)


@app.command(name="validate-audit")
def validate_audit(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output results as JSON.",
    ),
) -> None:
    """Run audit verification stage only.

    Validates:
    - Audit trail integrity
    - No missing entries
    - Hash chain is intact
    """
    project_root = _find_project_root(path)

    if not output_json:
        info("Running audit verification stage")

    pipeline = _create_pipeline(stages=[CIStage.AUDIT_VERIFICATION])
    result = pipeline.run(repo_root=project_root)

    _display_result(result, as_json=output_json)

    if not result.passed:
        raise typer.Exit(1)


@app.command(name="init")
def init_ci(
    path: Path = typer.Option(
        None,
        "--path",
        "-p",
        help="Project root path. Defaults to current directory.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing workflow file.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be created without writing files.",
    ),
) -> None:
    """Initialize CI configuration for the project.

    Creates a GitHub Actions workflow file at .github/workflows/rice-factor.yml
    that runs all rice-factor CI validation stages.
    """
    from importlib.resources import files

    project_root = _find_project_root(path)
    workflows_dir = project_root / ".github" / "workflows"
    target_file = workflows_dir / "rice-factor.yml"

    # Check if file already exists
    if target_file.exists() and not force:
        error(f"Workflow file already exists: {target_file}")
        info("Use --force to overwrite")
        raise typer.Exit(1)

    # Load template using modern importlib.resources API
    try:
        template_content = (
            files("rice_factor.templates.ci")
            .joinpath("github-actions.yml")
            .read_text(encoding="utf-8")
        )
    except Exception as e:
        error(f"Failed to load template: {e}")
        raise typer.Exit(1)

    if dry_run:
        info(f"Would create: {target_file}")
        console.print()
        console.print("[dim]--- Template content ---[/dim]")
        console.print(template_content)
        return

    # Create directories and write file
    workflows_dir.mkdir(parents=True, exist_ok=True)
    target_file.write_text(template_content, encoding="utf-8")

    success(f"Created CI workflow: {target_file}")
    info("Push to GitHub to trigger the workflow")