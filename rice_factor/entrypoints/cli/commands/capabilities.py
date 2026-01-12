"""Show refactoring tool capabilities."""

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.refactoring.capability_detector import (
    CapabilityDetector,
    ToolAvailability,
)
from rice_factor.entrypoints.cli.utils import (
    console,
    handle_errors,
    info,
    success,
    warning,
)


def _format_operations(operations: list[str]) -> str:
    """Format operations list for display.

    Args:
        operations: List of operation names.

    Returns:
        Formatted string.
    """
    if not operations:
        return "-"
    return ", ".join(operations)


def _create_tools_table(tools: dict[str, ToolAvailability]) -> Table:
    """Create a table showing tool availability.

    Args:
        tools: Dictionary of tool names to availability.

    Returns:
        Rich Table object.
    """
    table = Table(title="Refactoring Tool Availability")
    table.add_column("Tool", style="bold")
    table.add_column("Status")
    table.add_column("Version")
    table.add_column("Languages")
    table.add_column("Operations")

    for name, tool in sorted(tools.items()):
        status = "[green]✓ Available[/green]" if tool.available else "[red]✗ Not installed[/red]"
        version = tool.version or "-"
        languages = ", ".join(tool.languages) if tool.languages else "-"
        operations = _format_operations(tool.operations)

        table.add_row(name, status, version, languages, operations)

    return table


def _create_languages_table(detector: CapabilityDetector) -> Table:
    """Create a table showing language capabilities.

    Args:
        detector: The capability detector.

    Returns:
        Rich Table object.
    """
    capabilities = detector.get_language_capabilities()

    table = Table(title="Language Capabilities")
    table.add_column("Language", style="bold")
    table.add_column("Adapter")
    table.add_column("Status")
    table.add_column("rename")
    table.add_column("move")
    table.add_column("extract_if")
    table.add_column("enforce_dep")

    for cap in sorted(capabilities, key=lambda c: c.language):
        status = "[green]✓[/green]" if cap.available else "[red]✗[/red]"

        def op_status(name: str, operations: dict[str, bool] = cap.operations) -> str:
            return "[green]yes[/green]" if operations.get(name, False) else "[dim]-[/dim]"

        table.add_row(
            cap.language,
            cap.adapter,
            status,
            op_status("rename"),
            op_status("move"),
            op_status("extract_interface"),
            op_status("enforce_dependency"),
        )

    return table


@handle_errors
def capabilities(
    refresh: bool = typer.Option(
        False, "--refresh", "-r", help="Refresh cached detection results"
    ),
    tools: bool = typer.Option(
        False, "--tools", "-t", help="Show only tool availability"
    ),
    languages: bool = typer.Option(
        False, "--languages", "-l", help="Show only language capabilities"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """Show available refactoring tools and their capabilities.

    Detects installed refactoring tools (Rope, jscodeshift, gopls, etc.)
    and displays their capabilities for different programming languages.

    Use --refresh to re-detect tools if you've installed something new.
    """
    detector = CapabilityDetector()

    if refresh:
        info("Refreshing capability detection...")
        detector.refresh()
    else:
        detector.detect_all()

    if json_output:
        import json

        all_tools = detector.detect_all()
        output = {
            "tools": {
                name: {
                    "available": tool.available,
                    "version": tool.version,
                    "languages": tool.languages,
                    "operations": tool.operations,
                }
                for name, tool in all_tools.items()
            },
            "languages": [
                {
                    "language": cap.language,
                    "adapter": cap.adapter,
                    "available": cap.available,
                    "operations": cap.operations,
                }
                for cap in detector.get_language_capabilities()
            ],
        }
        console.print(json.dumps(output, indent=2))
        return

    console.print()
    console.print(Panel(
        "[bold]Rice-Factor Refactoring Capabilities[/bold]\n\n"
        "Shows detected refactoring tools and their capabilities.\n"
        "Install missing tools to enable additional refactoring operations.",
        border_style="blue",
    ))
    console.print()

    # Show both by default, or just what was requested
    show_tools = tools or not languages
    show_languages = languages or not tools

    if show_tools:
        all_tools = detector.detect_all()
        console.print(_create_tools_table(all_tools))
        console.print()

    if show_languages:
        console.print(_create_languages_table(detector))
        console.print()

    # Summary
    all_tools = detector.detect_all()
    available = sum(1 for t in all_tools.values() if t.available)
    total = len(all_tools)

    if available == total:
        success(f"All {total} refactoring tools are available!")
    elif available > 0:
        warning(f"{available}/{total} refactoring tools available")
        info("Install missing tools to enable more refactoring capabilities")
    else:
        warning("No refactoring tools detected")
        info("Install one or more tools:")
        info("  - Python: pip install rope")
        info("  - JavaScript: npm install -g jscodeshift")
        info("  - Go: go install golang.org/x/tools/gopls@latest")
        info("  - Rust: rustup component add rust-analyzer")
