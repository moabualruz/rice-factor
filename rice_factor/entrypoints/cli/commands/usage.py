"""LLM usage tracking commands.

This module provides CLI commands for viewing and managing LLM usage:
- rice-factor usage show: Display usage statistics
- rice-factor usage export: Export usage in various formats
- rice-factor usage clear: Reset usage tracking
"""

import json
from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.llm.usage_tracker import (
    ProviderStats,
    get_usage_tracker,
)
from rice_factor.entrypoints.cli.utils import console, error, info, success, warning

app = typer.Typer(
    name="usage",
    help="LLM usage tracking commands.",
    no_args_is_help=True,
)


def _format_tokens(count: int) -> str:
    """Format token count for display.

    Args:
        count: Token count.

    Returns:
        Formatted string.
    """
    if count >= 1_000_000:
        return f"{count / 1_000_000:.2f}M"
    if count >= 1_000:
        return f"{count / 1_000:.2f}K"
    return str(count)


def _format_cost(cost: float) -> str:
    """Format cost for display.

    Args:
        cost: Cost in USD.

    Returns:
        Formatted string.
    """
    if cost == 0:
        return "[green]$0.00[/green]"
    if cost < 0.01:
        return f"[yellow]${cost:.4f}[/yellow]"
    return f"[red]${cost:.2f}[/red]"


def _format_latency(ms: float) -> str:
    """Format latency for display.

    Args:
        ms: Latency in milliseconds.

    Returns:
        Formatted string.
    """
    if ms == float("inf"):
        return "-"
    if ms >= 1000:
        return f"{ms / 1000:.2f}s"
    return f"{ms:.0f}ms"


def _create_provider_table(stats: dict[str, ProviderStats]) -> Table:
    """Create a table showing provider statistics.

    Args:
        stats: Dictionary of provider name to stats.

    Returns:
        Rich Table object.
    """
    table = Table(title="Usage by Provider")
    table.add_column("Provider", style="bold cyan")
    table.add_column("Requests", justify="right")
    table.add_column("Success", justify="right")
    table.add_column("Input Tokens", justify="right")
    table.add_column("Output Tokens", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Avg Latency", justify="right")

    for provider, s in sorted(stats.items()):
        success_rate = (
            f"{s.successful_requests}/{s.total_requests}"
            if s.total_requests > 0
            else "-"
        )
        table.add_row(
            provider,
            str(s.total_requests),
            success_rate,
            _format_tokens(s.total_input_tokens),
            _format_tokens(s.total_output_tokens),
            _format_cost(s.total_cost_usd),
            _format_latency(s.avg_latency_ms),
        )

    return table


def _create_model_table(by_model: dict[str, float]) -> Table:
    """Create a table showing cost by model.

    Args:
        by_model: Dictionary of model name to cost.

    Returns:
        Rich Table object.
    """
    table = Table(title="Cost by Model")
    table.add_column("Model", style="bold")
    table.add_column("Cost", justify="right")

    for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True):
        table.add_row(model, _format_cost(cost))

    return table


@app.command("show")
def show_usage(
    provider: str = typer.Option(
        None, "--provider", "-p", help="Filter by provider"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """Display current usage statistics.

    Shows token usage, costs, and latency metrics for all providers.

    Examples:
        rice-factor usage show
        rice-factor usage show --provider claude
        rice-factor usage show --json
    """
    tracker = get_usage_tracker()

    if json_output:
        data = tracker.export_json()
        console.print(json.dumps(data, indent=2))
        return

    console.print()
    console.print(
        Panel(
            "[bold]Rice-Factor Usage Statistics[/bold]\n\n"
            "Shows LLM usage metrics including tokens, costs, and latency.",
            border_style="blue",
        )
    )
    console.print()

    stats = tracker.by_provider()

    if provider:
        stats = {k: v for k, v in stats.items() if k.lower() == provider.lower()}

    if not stats:
        warning("No usage data collected yet")
        info("Usage is tracked when LLM requests are made")
        return

    # Show provider table
    console.print(_create_provider_table(stats))
    console.print()

    # Show model breakdown
    by_model = tracker.by_model()
    if by_model:
        console.print(_create_model_table(by_model))
        console.print()

    # Summary
    total_cost = tracker.total_cost()
    input_tokens, output_tokens = tracker.total_tokens()

    console.print(
        Panel(
            f"Total Input Tokens: {_format_tokens(input_tokens)}\n"
            f"Total Output Tokens: {_format_tokens(output_tokens)}\n"
            f"Total Cost: {_format_cost(total_cost)}",
            title="Summary",
        )
    )


@app.command("export")
def export_usage(
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path. If not specified, outputs to stdout.",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json or prometheus.",
    ),
) -> None:
    """Export usage data in various formats.

    Formats:
      - json: JSON format with all usage details
      - prometheus: Prometheus text exposition format

    Examples:
        rice-factor usage export --format json > usage.json
        rice-factor usage export --format prometheus -o usage.prom
    """
    tracker = get_usage_tracker()

    if format.lower() == "json":
        content = json.dumps(tracker.export_json(), indent=2)
    elif format.lower() == "prometheus":
        content = tracker.export_prometheus()
    else:
        error(f"Unknown format: {format}. Use 'json' or 'prometheus'.")
        raise typer.Exit(1)

    if output:
        output.write_text(content, encoding="utf-8")
        success(f"Exported usage data to {output}")
    else:
        console.print(content)


@app.command("clear")
def clear_usage(
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation prompt"
    ),
) -> None:
    """Clear all usage tracking data.

    This action cannot be undone.

    Examples:
        rice-factor usage clear
        rice-factor usage clear --force
    """
    tracker = get_usage_tracker()

    # Get current count
    records = tracker.get_records()
    if not records:
        info("No usage data to clear")
        return

    if not force:
        confirm = typer.confirm(
            f"Are you sure you want to clear {len(records)} usage records?"
        )
        if not confirm:
            info("Cancelled")
            return

    count = tracker.clear()
    success(f"Cleared {count} usage records")
