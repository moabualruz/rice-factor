"""Initialize a new rice-factor project."""

from pathlib import Path

import typer
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from rice_factor.adapters.audit.trail import AuditTrail
from rice_factor.domain.services.init_service import InitService
from rice_factor.domain.services.questionnaire import (
    INIT_QUESTIONS,
    Question,
    QuestionnaireResponse,
    QuestionnaireRunner,
)
from rice_factor.entrypoints.cli.utils import (
    console,
    display_panel,
    error,
    handle_errors,
    info,
    success,
    supports_dry_run,
    warning,
)

app = typer.Typer(help="Initialize a new rice-factor project")


def _rich_prompt(prompt: str, multiline: bool, hint: str | None) -> str:
    """Prompt for input using Rich.

    Args:
        prompt: The question to ask
        multiline: Whether multiline input is allowed
        hint: Optional hint text

    Returns:
        User's response
    """
    # Display hint if provided
    if hint:
        console.print(f"[dim]{hint}[/dim]")

    if multiline:
        console.print(f"[bold]{prompt}[/bold]")
        console.print("[dim](Enter a blank line to finish)[/dim]")
        lines: list[str] = []
        while True:
            line = Prompt.ask("", default="")
            if not line and lines:
                break
            lines.append(line)
        return "\n".join(lines)
    else:
        return Prompt.ask(f"[bold]{prompt}[/bold]", default="")


def _display_welcome() -> None:
    """Display welcome message for init command."""
    welcome_text = (
        "Welcome to Rice-Factor!\n\n"
        "This wizard will help you set up your project by creating the "
        "[bold].project/[/bold] directory with template files.\n\n"
        "You'll be asked a few questions to customize the templates. "
        "[bold]All questions are required.[/bold]"
    )
    display_panel("Project Initialization", welcome_text, style="blue")


def _display_summary(
    created_files: list[Path],
    service: InitService,
) -> None:
    """Display summary of created files and directories.

    Args:
        created_files: List of files that were created
        service: The init service with directory paths
    """
    # Display directories created
    console.print()
    console.print("[bold]Directories created:[/bold]")
    console.print("  [cyan].project/[/cyan] - Project intake files")
    console.print("  [cyan]artifacts/[/cyan] - Artifact storage")
    console.print("  [cyan]audit/[/cyan] - Audit trail")

    # Display files table
    table = Table(title="Intake Files", show_header=True, header_style="bold")
    table.add_column("File", style="cyan")
    table.add_column("Description", style="dim")

    descriptions = {
        "requirements.md": "Project requirements and success criteria",
        "constraints.md": "Technical constraints and allowed technologies",
        "glossary.md": "Domain-specific terminology",
        "non_goals.md": "Explicit non-goals and out-of-scope items",
        "risks.md": "Risk register and unacceptable failures",
    }

    for file_path in created_files:
        desc = descriptions.get(file_path.name, "Template file")
        table.add_row(str(file_path.relative_to(service.project_root)), desc)

    console.print()
    console.print(table)
    console.print()
    success(f"Project initialized at {service.project_dir}")
    warning("Edit the intake files in .project/ before running 'rice-factor plan'")
    info("Required files: requirements.md, constraints.md, glossary.md")


def _run_questionnaire(questions: list[Question]) -> QuestionnaireResponse:
    """Run the interactive questionnaire.

    Args:
        questions: List of questions to ask

    Returns:
        Collected responses
    """
    console.print()
    console.print("[bold]Please answer the following questions:[/bold]")
    console.print()

    runner = QuestionnaireRunner(questions=questions, prompt_func=_rich_prompt)
    return runner.run()


def _display_dry_run_preview(service: InitService, responses: QuestionnaireResponse) -> None:
    """Display what would be created in dry-run mode.

    Args:
        service: The init service
        responses: Questionnaire responses
    """
    console.print()
    console.print(Panel(
        f"Would create directory: [cyan]{service.project_dir}[/cyan]",
        title="Dry Run Preview",
        border_style="yellow",
    ))

    for filename in service.TEMPLATE_FILES:
        content = service.get_template_content(filename, responses)
        preview = content[:200] + "..." if len(content) > 200 else content
        console.print()
        console.print(f"[bold]Would create:[/bold] {service.project_dir / filename}")
        console.print(Panel(preview, border_style="dim"))


@app.callback(invoke_without_command=True)
@handle_errors
@supports_dry_run
def init(
    ctx: typer.Context,
    path: str = typer.Option(
        ".",
        "--path",
        "-p",
        help="Path to initialize project in",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing .project/ directory",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be created without making changes",
    ),
    skip_questionnaire: bool = typer.Option(
        False,
        "--skip-questionnaire",
        "-s",
        help="Skip interactive questionnaire (use defaults)",
    ),
) -> None:
    """Initialize a new rice-factor project in the specified directory.

    Creates a .project/ directory containing template files for:
    - requirements.md: Project requirements
    - constraints.md: Technical constraints
    - glossary.md: Domain glossary
    - non_goals.md: Non-goals and out-of-scope items
    - risks.md: Risk register
    """
    if ctx.invoked_subcommand is not None:
        return

    project_root = Path(path).resolve()
    service = InitService(project_root=project_root)

    # Check if already initialized
    if service.is_initialized() and not force and not dry_run:
        error(f"Project already initialized at {service.project_dir}")
        warning("Use --force to overwrite existing files")
        raise typer.Exit(1)

    # Display welcome
    _display_welcome()

    # Run questionnaire or use empty responses
    if skip_questionnaire:
        info("Skipping questionnaire (using default templates)")
        responses = QuestionnaireResponse()
    else:
        responses = _run_questionnaire(INIT_QUESTIONS)

    # Handle dry-run mode
    if dry_run:
        _display_dry_run_preview(service, responses)
        info("No changes made (dry-run mode)")
        return

    # Perform initialization
    try:
        created_files = service.initialize(responses=responses, force=force)
    except FileExistsError as e:
        error(str(e))
        raise typer.Exit(1) from None

    # Record in audit trail
    audit_trail = AuditTrail(project_root=project_root)
    audit_trail.record_init(files_created=[str(f) for f in created_files])

    # Display summary
    _display_summary(created_files, service)
