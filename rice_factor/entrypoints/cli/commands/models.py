"""Show registered LLM models and their capabilities."""

import json

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.domain.services.model_registry import (
    ModelCapability,
    ModelInfo,
    get_model_registry,
)
from rice_factor.entrypoints.cli.utils import (
    console,
    handle_errors,
    info,
    success,
    warning,
)


def _format_capabilities(capabilities: list[ModelCapability]) -> str:
    """Format capabilities list for display.

    Args:
        capabilities: List of model capabilities.

    Returns:
        Formatted string.
    """
    if not capabilities:
        return "-"
    return ", ".join(c.value for c in capabilities)


def _format_cost(cost_input: float, cost_output: float) -> str:
    """Format cost per 1K tokens.

    Args:
        cost_input: Cost per 1K input tokens.
        cost_output: Cost per 1K output tokens.

    Returns:
        Formatted cost string.
    """
    if cost_input == 0 and cost_output == 0:
        return "[green]Free[/green]"
    return f"${cost_input:.4f}/{cost_output:.4f}"


def _create_models_table(models: list[ModelInfo]) -> Table:
    """Create a table showing model information.

    Args:
        models: List of ModelInfo objects.

    Returns:
        Rich Table object.
    """
    table = Table(title="Registered LLM Models")
    table.add_column("Model ID", style="bold cyan")
    table.add_column("Provider", style="dim")
    table.add_column("Context", justify="right")
    table.add_column("Capabilities")
    table.add_column("Cost (in/out)", justify="right")
    table.add_column("Status")

    for model in sorted(models, key=lambda m: (m.provider, m.id)):
        status = "[green]Available[/green]" if model.available else "[red]Unavailable[/red]"
        context = f"{model.context_length:,}"
        capabilities = _format_capabilities(model.capabilities)
        cost = _format_cost(model.cost_per_1k_input, model.cost_per_1k_output)

        # Add local indicator
        provider = model.provider
        if model.is_local:
            provider = f"{provider} [dim](local)[/dim]"

        table.add_row(
            model.id,
            provider,
            context,
            capabilities,
            cost,
            status,
        )

    return table


def _filter_models(
    models: list[ModelInfo],
    provider: str | None,
    capability: str | None,
    local_only: bool,
    cloud_only: bool,
    available_only: bool,
) -> list[ModelInfo]:
    """Filter models based on criteria.

    Args:
        models: List of all models.
        provider: Filter by provider name.
        capability: Filter by capability.
        local_only: Show only local models.
        cloud_only: Show only cloud models.
        available_only: Show only available models.

    Returns:
        Filtered list of models.
    """
    result = models

    if provider:
        result = [m for m in result if m.provider.lower() == provider.lower()]

    if capability:
        try:
            cap = ModelCapability(capability.lower())
            result = [m for m in result if cap in m.capabilities]
        except ValueError:
            # Invalid capability, return empty
            return []

    if local_only:
        result = [m for m in result if m.is_local]

    if cloud_only:
        result = [m for m in result if not m.is_local]

    if available_only:
        result = [m for m in result if m.available]

    return result


@handle_errors
def models(
    provider: str = typer.Option(
        None, "--provider", "-p", help="Filter by provider (e.g., claude, ollama)"
    ),
    capability: str = typer.Option(
        None,
        "--capability",
        "-c",
        help="Filter by capability (code, chat, reasoning, vision, function_calling, json_mode)",
    ),
    local_only: bool = typer.Option(
        False, "--local", "-l", help="Show only local models"
    ),
    cloud_only: bool = typer.Option(
        False, "--cloud", help="Show only cloud-hosted models"
    ),
    available_only: bool = typer.Option(
        False, "--available", "-a", help="Show only available models"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """Show registered LLM models and their capabilities.

    Lists all models in the registry with their context length,
    capabilities, and cost information.

    Examples:
        rice-factor models                     # List all models
        rice-factor models --provider ollama   # Filter by provider
        rice-factor models --capability code   # Filter by capability
        rice-factor models --local             # Show only local models
    """
    registry = get_model_registry()
    all_models = registry.get_all()

    # Apply filters
    filtered = _filter_models(
        all_models,
        provider=provider,
        capability=capability,
        local_only=local_only,
        cloud_only=cloud_only,
        available_only=available_only,
    )

    if json_output:
        output = {
            "models": [
                {
                    "id": m.id,
                    "provider": m.provider,
                    "context_length": m.context_length,
                    "capabilities": [c.value for c in m.capabilities],
                    "strengths": m.strengths,
                    "cost_per_1k_input": m.cost_per_1k_input,
                    "cost_per_1k_output": m.cost_per_1k_output,
                    "is_local": m.is_local,
                    "available": m.available,
                }
                for m in filtered
            ],
            "count": len(filtered),
            "total": len(all_models),
        }
        console.print(json.dumps(output, indent=2))
        return

    console.print()
    console.print(
        Panel(
            "[bold]Rice-Factor Model Registry[/bold]\n\n"
            "Shows all registered LLM models with their capabilities.\n"
            "Use filters to narrow down the list.",
            border_style="blue",
        )
    )
    console.print()

    if not filtered:
        warning("No models match the specified filters")
        return

    console.print(_create_models_table(filtered))
    console.print()

    # Summary
    local_count = sum(1 for m in filtered if m.is_local)
    cloud_count = len(filtered) - local_count
    available_count = sum(1 for m in filtered if m.available)

    info(f"Showing {len(filtered)}/{len(all_models)} models")
    info(f"Local: {local_count}, Cloud: {cloud_count}, Available: {available_count}")

    # List available capabilities
    if capability and capability.lower() not in [c.value for c in ModelCapability]:
        warning(f"Unknown capability: {capability}")
        info(f"Valid capabilities: {', '.join(c.value for c in ModelCapability)}")
