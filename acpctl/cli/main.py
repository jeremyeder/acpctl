"""
acpctl CLI Main Entry Point

Command-line interface for acpctl - Governed Spec-Driven Development CLI.
Built with Typer and Rich for professional terminal UX.

Usage:
    acpctl [OPTIONS] COMMAND [ARGS]...

Commands:
    init        Initialize project with constitutional governance
    specify     Generate feature specification with pre-flight questions
    plan        Generate implementation plan with architecture
    implement   Generate code following TDD approach
    status      Show current workflow state
    resume      Resume interrupted workflow from checkpoint
    history     List all workflows

Global Options:
    --quiet, -q      Minimal output (errors only)
    --verbose, -v    Detailed output (agent reasoning, debug info)
    --version        Show version and exit

Architecture:
- Typer app with global flags for verbosity
- Commands registered from acpctl.cli.commands module
- Rich integration for formatted output
- Config singleton manages UI state
"""

from typing import Optional

import typer
from typing_extensions import Annotated

from acpctl import __version__
from acpctl.cli.ui import Config, ConsoleLevel

# Initialize Typer app
app = typer.Typer(
    name="acpctl",
    help="Governed Spec-Driven Development CLI - AI-powered workflow with constitutional validation",
    add_completion=False,  # Disable shell completion for now
    rich_markup_mode="rich",  # Enable Rich markup in help text
)


def version_callback(value: bool) -> None:
    """
    Print version information and exit.

    Args:
        value: True if --version flag is set
    """
    if value:
        config = Config.get_instance()
        config.console.print(f"[bold]acpctl[/bold] version {__version__}")
        config.console.print("Governed Spec-Driven Development CLI")
        config.console.print("Built with LangGraph, LangChain, Typer, and Rich")
        raise typer.Exit()


@app.callback()
def main(
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Minimal output (errors and critical messages only)",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Detailed output (agent reasoning, debug info, full logs)",
        ),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
) -> None:
    """
    acpctl - Governed Spec-Driven Development CLI

    AI-powered workflow for generating specifications, plans, and code
    with constitutional governance and automatic checkpointing.

    [bold]Progressive Disclosure:[/bold]
    - Default: Standard output (progress, summaries, results)
    - --quiet/-q: Minimal output (errors only)
    - --verbose/-v: Full output (agent reasoning, detailed logs)

    [bold]Examples:[/bold]

        # Initialize project with constitutional template
        $ acpctl init

        # Generate specification with pre-flight questions
        $ acpctl specify "Add OAuth2 authentication"

        # Generate implementation plan
        $ acpctl plan

        # Generate code with TDD approach
        $ acpctl implement

        # Show current workflow status
        $ acpctl status

        # Resume interrupted workflow
        $ acpctl resume

        # List all workflows
        $ acpctl history

    [bold]Workflow Phases:[/bold]
    init → specify → plan → implement → complete

    Each phase includes:
    - Constitutional validation (governance gate)
    - Automatic checkpoint (resume from any phase)
    - Artifact generation (specs/, plans, code)
    """
    # Configure UI verbosity level from flags
    config = Config.get_instance()
    config.set_level_from_flags(quiet=quiet, verbose=verbose)

    # Log verbosity level in verbose mode
    if config.is_verbose():
        config.console.print(
            f"[dim]Console verbosity: {config.level.value}[/dim]", style="dim"
        )


# ============================================================
# COMMAND REGISTRATION
# ============================================================

# Import commands
from acpctl.cli.commands.init import init_command
from acpctl.cli.commands.specify import specify_command
from acpctl.cli.commands.plan import plan_command
from acpctl.cli.commands.implement import implement_command
from acpctl.cli.commands.status import status_command
from acpctl.cli.commands.resume import resume_command
from acpctl.cli.commands.history import history_command

# Register commands
app.command(name="init")(init_command)
app.command(name="specify")(specify_command)
app.command(name="plan")(plan_command)
app.command(name="implement")(implement_command)
app.command(name="status")(status_command)
app.command(name="resume")(resume_command)
app.command(name="history")(history_command)

# ============================================================


def run() -> None:
    """
    Entry point for the acpctl CLI application.

    This function is called by the console_scripts entry point in setup.py.
    """
    app()


if __name__ == "__main__":
    run()
