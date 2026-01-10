"""Rice-Factor CLI entry point."""

import typer
from rich.console import Console

from rice_factor import __version__

app = typer.Typer(
    name="rice-factor",
    help="LLM-Assisted Development System - Artifacts as IR, LLMs as Compilers",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool) -> None:
    """Display version and exit."""
    if value:
        console.print(f"rice-factor version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Rice-Factor: LLM-Assisted Development System."""
    pass


# Import and register command modules
from rice_factor.entrypoints.cli.commands import (
    apply,
    approve,
    impl,
    init,
    lock,
    plan,
    refactor,
    resume,
    scaffold,
    test,
    validate,
)

app.add_typer(init.app, name="init")
app.command(name="plan")(plan.plan)
app.command(name="scaffold")(scaffold.scaffold)
app.command(name="impl")(impl.impl)
app.command(name="apply")(apply.apply)
app.command(name="test")(test.test)
app.command(name="approve")(approve.approve)
app.command(name="lock")(lock.lock)
app.command(name="refactor")(refactor.refactor)
app.command(name="validate")(validate.validate)
app.command(name="resume")(resume.resume)


if __name__ == "__main__":
    app()
