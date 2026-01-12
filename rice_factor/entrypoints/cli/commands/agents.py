"""CLI agent management commands.

This module provides CLI commands for managing coding agents:
- rice-factor agents detect: Detect available CLI agents
- rice-factor agents list: List all configured agents
"""

import json

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.adapters.llm.cli.detector import CLIAgentDetector, DetectedAgent
from rice_factor.entrypoints.cli.utils import (
    console,
    handle_errors,
    info,
    success,
    warning,
)

app = typer.Typer(
    name="agents",
    help="CLI coding agent management commands.",
    no_args_is_help=True,
)


def _create_agents_table(agents: list[DetectedAgent]) -> Table:
    """Create a table showing agent information.

    Args:
        agents: List of DetectedAgent objects.

    Returns:
        Rich Table object.
    """
    table = Table(title="CLI Coding Agents")
    table.add_column("Agent", style="bold cyan")
    table.add_column("Command", style="dim")
    table.add_column("Status")
    table.add_column("Version")
    table.add_column("Path", style="dim")

    for agent in sorted(agents, key=lambda a: a.name):
        status = (
            "[green]Available[/green]" if agent.available else "[red]Not installed[/red]"
        )
        version = agent.version or "-"
        path = agent.path or "-"

        # Truncate path if too long
        if len(path) > 40:
            path = "..." + path[-37:]

        table.add_row(
            agent.name,
            agent.command,
            status,
            version,
            path,
        )

    return table


@app.command("detect")
def detect_agents(
    refresh: bool = typer.Option(
        False, "--refresh", "-r", help="Force re-detection (no cache)"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """Detect available CLI coding agents on the system.

    Scans the system PATH for known CLI coding tools (Claude Code, Codex,
    Gemini CLI, Aider, etc.) and reports their availability.

    Examples:
        rice-factor agents detect
        rice-factor agents detect --json
    """
    detector = CLIAgentDetector()
    agents = detector.detect_all()

    if json_output:
        output = detector.to_dict()
        output["summary"] = {
            "total": len(agents),
            "available": sum(1 for a in agents if a.available),
        }
        console.print(json.dumps(output, indent=2))
        return

    console.print()
    console.print(
        Panel(
            "[bold]CLI Agent Detection[/bold]\n\n"
            "Scans for installed CLI coding agents.\n"
            "Install missing agents to enable additional execution modes.",
            border_style="blue",
        )
    )
    console.print()

    console.print(_create_agents_table(agents))
    console.print()

    # Summary
    available = [a for a in agents if a.available]
    if available:
        success(f"Found {len(available)}/{len(agents)} CLI agents installed")
    else:
        warning("No CLI agents detected")
        info("Install one or more agents:")
        info("  - Claude Code: npm install -g @anthropic-ai/claude-code")
        info("  - Codex: npm install -g @openai/codex")
        info("  - Aider: pip install aider-chat")
        info("  - Gemini CLI: npm install -g @google/gemini-cli")


@app.command("list")
def list_agents(
    available_only: bool = typer.Option(
        False, "--available", "-a", help="Show only available agents"
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON"
    ),
) -> None:
    """List all configured CLI coding agents.

    Shows all agents that can be detected, optionally filtering to only
    show those that are currently available.

    Examples:
        rice-factor agents list
        rice-factor agents list --available
    """
    detector = CLIAgentDetector()
    agents = detector.detect_all()

    if available_only:
        agents = [a for a in agents if a.available]

    if json_output:
        output = {
            "agents": [
                {
                    "name": a.name,
                    "command": a.command,
                    "available": a.available,
                    "version": a.version,
                    "path": a.path,
                }
                for a in agents
            ],
            "count": len(agents),
        }
        console.print(json.dumps(output, indent=2))
        return

    console.print()

    if not agents:
        if available_only:
            warning("No CLI agents are currently available")
        else:
            warning("No CLI agents configured")
        return

    console.print(_create_agents_table(agents))
    console.print()

    info(f"Total: {len(agents)} agents configured")


@app.command("check")
def check_agent(
    name: str = typer.Argument(..., help="Agent name to check"),
) -> None:
    """Check if a specific CLI agent is available.

    Examples:
        rice-factor agents check claude_code
        rice-factor agents check aider
    """
    detector = CLIAgentDetector()

    if name not in detector.configs:
        warning(f"Unknown agent: {name}")
        info(f"Available agents: {', '.join(detector.configs.keys())}")
        raise typer.Exit(1)

    agent = detector.detect_agent(name, detector.configs[name])

    if agent.available:
        success(f"{name} is available")
        info(f"Command: {agent.command}")
        if agent.version:
            info(f"Version: {agent.version}")
        if agent.path:
            info(f"Path: {agent.path}")
    else:
        warning(f"{name} is not installed")
        info(f"Expected command: {agent.command}")
        raise typer.Exit(1)
