"""Migrate command for artifact schema migrations.

This module provides the CLI command for migrating artifacts between
schema versions.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel
from rich.table import Table

from rice_factor.entrypoints.cli.utils import console, error, info, success, warning


app = typer.Typer(help="Artifact schema migration commands.")


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


@app.command("status")
def migration_status(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Path to project root."),
    ] = None,
) -> None:
    """Show migration status and pending migrations."""
    from rice_factor.domain.services.artifact_migrator import ArtifactMigrator

    project_root = _find_project_root(path)
    info(f"Scanning artifacts in {project_root}")

    migrator = ArtifactMigrator(repo_root=project_root)
    summary = migrator.get_migration_summary()

    # Show summary panel
    if summary["total_pending"] == 0:
        success("All artifacts are up to date!")
        return

    warning(f"Found {summary['total_pending']} artifact(s) needing migration")

    # Show by type
    if summary["by_type"]:
        table = Table(title="Pending Migrations by Type")
        table.add_column("Artifact Type", style="cyan")
        table.add_column("Count", justify="right", style="yellow")

        for atype, count in sorted(summary["by_type"].items()):
            table.add_row(atype, str(count))

        console.print(table)

    # Show by version
    if summary["by_version"]:
        table = Table(title="Pending Migrations by Version")
        table.add_column("Current Version", style="cyan")
        table.add_column("Count", justify="right", style="yellow")

        for version, count in sorted(summary["by_version"].items()):
            table.add_row(version, str(count))

        console.print(table)

    # Show backups
    if summary["backups_available"] > 0:
        info(f"\n{summary['backups_available']} backup(s) available")


@app.command("plan")
def migration_plan(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Path to project root."),
    ] = None,
    artifact_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by artifact type."),
    ] = None,
    target_version: Annotated[
        str | None,
        typer.Option("--version", "-v", help="Target version."),
    ] = None,
) -> None:
    """Generate a migration plan (dry run)."""
    from rice_factor.domain.services.artifact_migrator import ArtifactMigrator

    project_root = _find_project_root(path)
    info(f"Generating migration plan for {project_root}")

    migrator = ArtifactMigrator(repo_root=project_root)
    plan = migrator.create_migration_plan(
        target_version=target_version,
        artifact_type=artifact_type,
        dry_run=True,
    )

    if plan.artifact_count == 0:
        success("No migrations needed!")
        return

    table = Table(title=f"Migration Plan ({plan.artifact_count} artifact(s))")
    table.add_column("Artifact", style="cyan")
    table.add_column("Type", style="blue")
    table.add_column("Current", style="yellow")
    table.add_column("Target", style="green")

    for artifact in plan.artifacts_to_migrate:
        table.add_row(
            artifact["relative_path"],
            artifact["artifact_type"],
            artifact["current_version"],
            artifact["target_version"],
        )

    console.print(table)
    console.print(f"\nRun 'rice-factor migrate run' to execute this plan.")


@app.command("run")
def migration_run(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Path to project root."),
    ] = None,
    artifact_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by artifact type."),
    ] = None,
    target_version: Annotated[
        str | None,
        typer.Option("--version", "-v", help="Target version."),
    ] = None,
    no_backup: Annotated[
        bool,
        typer.Option("--no-backup", help="Skip creating backup."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Execute artifact migrations."""
    from rice_factor.domain.services.artifact_migrator import (
        ArtifactMigrator,
        MigrationStatus,
    )

    project_root = _find_project_root(path)
    info(f"Preparing migrations for {project_root}")

    migrator = ArtifactMigrator(repo_root=project_root)
    plan = migrator.create_migration_plan(
        target_version=target_version,
        artifact_type=artifact_type,
        dry_run=False,
        create_backup=not no_backup,
    )

    if plan.artifact_count == 0:
        success("No migrations needed!")
        return

    warning(f"Will migrate {plan.artifact_count} artifact(s)")

    if not yes:
        confirm = typer.confirm("Proceed with migration?")
        if not confirm:
            info("Migration cancelled.")
            return

    # Execute migration
    info("Executing migrations...")
    result = migrator.execute_migration(plan)

    # Show results
    if result.all_succeeded:
        success(f"Successfully migrated {result.migrated_count} artifact(s)")
    else:
        warning(f"Migrated: {result.migrated_count}, Failed: {result.failed_count}")

    if result.backup_directory:
        info(f"Backup created at: {result.backup_directory}")

    # Show details table
    if result.failed_count > 0:
        table = Table(title="Migration Results")
        table.add_column("Artifact", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Error", style="red")

        for r in result.results:
            status_color = "green" if r.status == MigrationStatus.COMPLETED else "red"
            table.add_row(
                r.artifact_path,
                f"[{status_color}]{r.status.value}[/{status_color}]",
                r.error or "",
            )

        console.print(table)


@app.command("rollback")
def migration_rollback(
    backup: Annotated[
        str | None,
        typer.Argument(help="Backup directory path to rollback from."),
    ] = None,
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Path to project root."),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Rollback migrations from a backup."""
    from rice_factor.domain.services.artifact_migrator import (
        ArtifactMigrator,
        MigrationStatus,
    )

    project_root = _find_project_root(path)
    migrator = ArtifactMigrator(repo_root=project_root)

    # If no backup specified, list available and let user choose
    if backup is None:
        backups = migrator.list_backups()
        if not backups:
            error("No backups available.")
            return

        info("Available backups:")
        for i, b in enumerate(backups, 1):
            console.print(f"  {i}. {b['name']} ({b['artifact_count']} artifacts)")

        choice = typer.prompt("Enter backup number", type=int)
        if choice < 1 or choice > len(backups):
            error("Invalid selection.")
            return

        backup = backups[choice - 1]["path"]

    info(f"Rolling back from: {backup}")

    if not yes:
        confirm = typer.confirm("Proceed with rollback?")
        if not confirm:
            info("Rollback cancelled.")
            return

    result = migrator.rollback_migration(backup)

    if result.all_succeeded:
        success(f"Successfully rolled back {result.migrated_count} artifact(s)")
    else:
        warning(f"Rolled back: {result.migrated_count}, Failed: {result.failed_count}")


@app.command("backups")
def list_backups(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Path to project root."),
    ] = None,
) -> None:
    """List available migration backups."""
    from rice_factor.domain.services.artifact_migrator import ArtifactMigrator
    from datetime import datetime

    project_root = _find_project_root(path)
    migrator = ArtifactMigrator(repo_root=project_root)

    backups = migrator.list_backups()

    if not backups:
        info("No backups available.")
        return

    table = Table(title="Migration Backups")
    table.add_column("Name", style="cyan")
    table.add_column("Artifacts", justify="right", style="yellow")
    table.add_column("Created", style="dim")

    for b in backups:
        created = datetime.fromtimestamp(b["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        table.add_row(b["name"], str(b["artifact_count"]), created)

    console.print(table)


@app.command("delete-backup")
def delete_backup(
    backup: Annotated[
        str,
        typer.Argument(help="Backup directory name or path to delete."),
    ],
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Path to project root."),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation prompt."),
    ] = False,
) -> None:
    """Delete a migration backup."""
    from rice_factor.domain.services.artifact_migrator import ArtifactMigrator

    project_root = _find_project_root(path)
    migrator = ArtifactMigrator(repo_root=project_root)

    # Resolve backup path
    if not Path(backup).is_absolute():
        backup_path = project_root / "audit" / "migration_backups" / backup
        if not backup_path.exists():
            backup_path = Path(backup)
    else:
        backup_path = Path(backup)

    if not backup_path.exists():
        error(f"Backup not found: {backup}")
        return

    if not yes:
        confirm = typer.confirm(f"Delete backup {backup_path.name}?")
        if not confirm:
            info("Deletion cancelled.")
            return

    if migrator.delete_backup(str(backup_path)):
        success(f"Deleted backup: {backup_path.name}")
    else:
        error("Failed to delete backup.")
