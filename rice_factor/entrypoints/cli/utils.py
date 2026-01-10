"""CLI utilities and Rich console helpers.

This module provides shared utilities for CLI commands including:
- Rich console singleton for consistent output
- Helper functions for success/warning/error/info messages
- Confirmation prompts for destructive operations
- Error handling and dry-run decorators
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rice_factor.domain.failures import (
    ArtifactNotFoundError,
    ArtifactStatusError,
    ArtifactValidationError,
)

# Rich console singleton
console = Console()

# Type variable for decorator return types
F = TypeVar("F", bound=Callable[..., Any])


def success(message: str) -> None:
    """Display success message with green checkmark.

    Args:
        message: The success message to display
    """
    console.print(f"[green][bold]✓[/bold][/green] {message}")


def warning(message: str) -> None:
    """Display warning message with yellow warning icon.

    Args:
        message: The warning message to display
    """
    console.print(f"[yellow][bold]⚠[/bold][/yellow] {message}")


def error(message: str) -> None:
    """Display error message with red X.

    Args:
        message: The error message to display
    """
    console.print(f"[red][bold]✗[/bold][/red] {message}")


def info(message: str) -> None:
    """Display info message with blue info icon.

    Args:
        message: The info message to display
    """
    console.print(f"[blue][bold]i[/bold][/blue] {message}")


def confirm(message: str, default: bool = False) -> bool:
    """Prompt for confirmation.

    Args:
        message: The confirmation message to display
        default: Default value if user just presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    return typer.confirm(message, default=default)


def confirm_destructive(action: str, target: str) -> bool:
    """Prompt for confirmation of a destructive action.

    Displays a warning and requires explicit confirmation.

    Args:
        action: Description of the action (e.g., "overwrite", "delete")
        target: The target of the action (e.g., file path, artifact name)

    Returns:
        True if user confirms, False otherwise
    """
    console.print(
        f"[yellow][bold]Warning:[/bold][/yellow] This will {action} [bold]{target}[/bold]"
    )
    return typer.confirm("Are you sure?", default=False)


def display_error(title: str, message: str, hint: str | None = None) -> None:
    """Display an error in a Rich panel.

    Args:
        title: The error title
        message: The error message
        hint: Optional hint for resolving the error
    """
    content = f"[red]{message}[/red]"
    if hint:
        content += f"\n\n[dim]Hint: {hint}[/dim]"
    console.print(Panel(content, title=f"[red]{title}[/red]", border_style="red"))


def display_panel(title: str, content: str, style: str = "blue") -> None:
    """Display content in a Rich panel.

    Args:
        title: The panel title
        content: The panel content
        style: Border style color (default: blue)
    """
    console.print(Panel(content, title=f"[{style}]{title}[/{style}]", border_style=style))


def display_table(
    title: str, columns: list[str], rows: list[list[str]], show_header: bool = True
) -> None:
    """Display data in a Rich table.

    Args:
        title: The table title
        columns: List of column names
        rows: List of row data (each row is a list of strings)
        show_header: Whether to show the header row
    """
    table = Table(title=title, show_header=show_header)
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def handle_errors(f: F) -> F:
    """Decorator to convert exceptions to user-friendly CLI errors.

    Catches common exceptions and displays them in a user-friendly format
    before exiting with appropriate error codes.

    Args:
        f: The function to wrap

    Returns:
        Wrapped function with error handling
    """
    # Import here to avoid circular imports
    from rice_factor.domain.failures.cli_errors import (
        CLIError,
        ConfirmationRequired,
        MissingPrerequisiteError,
        PhaseError,
    )

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except PhaseError as e:
            display_error(
                "Phase Error",
                str(e),
                hint="Run 'rice-factor --help' to see available commands for your current phase.",
            )
            raise typer.Exit(1) from None
        except MissingPrerequisiteError as e:
            display_error(
                "Missing Prerequisite",
                str(e),
                hint="Complete the required steps before running this command.",
            )
            raise typer.Exit(1) from None
        except ConfirmationRequired as e:
            display_error("Confirmation Required", str(e))
            raise typer.Exit(1) from None
        except ArtifactNotFoundError as e:
            display_error(
                "Artifact Not Found",
                str(e),
                hint="Check the artifact path or run 'rice-factor plan' to create it.",
            )
            raise typer.Exit(1) from None
        except ArtifactValidationError as e:
            display_error("Validation Error", str(e))
            raise typer.Exit(1) from None
        except ArtifactStatusError as e:
            display_error(
                "Status Error",
                str(e),
                hint="Check the artifact's current status before attempting this operation.",
            )
            raise typer.Exit(1) from None
        except CLIError as e:
            display_error("CLI Error", str(e))
            raise typer.Exit(1) from None
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user.[/yellow]")
            raise typer.Exit(130) from None

    return wrapper  # type: ignore[return-value]


def supports_dry_run(f: F) -> F:
    """Decorator to handle dry-run mode for commands.

    When dry_run=True is passed to the wrapped function, it will display
    a message indicating what would be done without actually executing.

    Note: The wrapped function must accept a 'dry_run' keyword argument.

    Args:
        f: The function to wrap

    Returns:
        Wrapped function with dry-run support
    """

    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        dry_run = kwargs.get("dry_run", False)
        if dry_run:
            info("[Dry-run mode] The following would be executed:")
        return f(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
