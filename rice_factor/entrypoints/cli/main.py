"""Rice-Factor CLI entry point."""

import typer

from rice_factor import __version__
from rice_factor.entrypoints.cli.utils import console, info

app = typer.Typer(
    name="rice-factor",
    help="LLM-Assisted Development System - Artifacts as IR, LLMs as Compilers",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Global state for verbose/quiet modes
_verbose: bool = False
_quiet: bool = False


def get_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return _verbose


def get_quiet() -> bool:
    """Check if quiet mode is enabled."""
    return _quiet


def version_callback(value: bool) -> None:
    """Display version and exit."""
    if value:
        console.print(f"rice-factor version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    _version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose output.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-essential output.",
    ),
) -> None:
    """Rice-Factor: LLM-Assisted Development System."""
    global _verbose, _quiet
    _verbose = verbose
    _quiet = quiet

    if verbose and not quiet:
        info("Verbose mode enabled")


# Import and register command modules
from rice_factor.entrypoints.cli.commands import (
    apply,
    approve,
    audit,
    ci,
    diagnose,
    impl,
    init,
    lock,
    override,
    plan,
    reconcile,
    refactor,
    resume,
    review,
    scaffold,
    test,
    validate,
)

app.add_typer(init.app, name="init")
app.add_typer(plan.app, name="plan")
app.command(name="scaffold")(scaffold.scaffold)
app.command(name="impl")(impl.impl)
app.command(name="review")(review.review)
app.command(name="apply")(apply.apply)
app.command(name="test")(test.test)
app.command(name="diagnose")(diagnose.diagnose)
app.command(name="approve")(approve.approve)
app.command(name="lock")(lock.lock)
app.add_typer(refactor.app, name="refactor")
app.command(name="validate")(validate.validate)
app.command(name="resume")(resume.resume)
app.add_typer(override.app, name="override")
app.add_typer(ci.app, name="ci")
app.add_typer(audit.app, name="audit")
app.command(name="reconcile")(reconcile.reconcile)


if __name__ == "__main__":
    app()
