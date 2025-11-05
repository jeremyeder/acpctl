"""
acpctl Resume Command

Resume interrupted workflow from last checkpoint.
Loads saved state, skips completed phases, continues execution.

Command:
    acpctl resume [FEATURE_ID]

Options:
    FEATURE_ID: Optional feature ID to resume (defaults to latest workflow)

Architecture:
- Loads checkpoint from .acp/state/
- Restores LangGraph thread_id and state
- Determines completed phases from metadata
- Displays skip message for completed phases
- Continues workflow from next incomplete phase
- Saves updated checkpoint after each phase

Reference: spec.md (User Story 3), plan.md (Phase 5)
"""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated

from acpctl.cli.ui import Config
from acpctl.core.checkpoint import (
    get_checkpoint_by_feature_id,
    get_latest_checkpoint,
    load_checkpoint,
    save_checkpoint,
)


def resume_command(
    feature_id: Annotated[
        Optional[str],
        typer.Argument(help="Feature ID to resume (defaults to latest)"),
    ] = None,
    acp_dir: Annotated[
        str,
        typer.Option(
            "--acp-dir",
            help="ACP directory path (default: .acp)",
            hidden=True,
        ),
    ] = ".acp",
) -> None:
    """
    Resume interrupted workflow from last checkpoint.

    Loads saved state from checkpoint, skips completed phases, and continues
    execution from the next incomplete phase. Workflow state is automatically
    restored including LangGraph thread ID and all agent context.

    [bold]Examples:[/bold]

        # Resume latest workflow
        $ acpctl resume

        # Resume specific workflow
        $ acpctl resume 001-oauth2-authentication

    [bold]Workflow:[/bold]

        1. Load checkpoint and metadata
        2. Display workflow summary
        3. Skip completed phases
        4. Continue from next incomplete phase
        5. Save checkpoint after each phase completion

    [bold]Phase Progression:[/bold]

        init → specify → plan → implement → complete

        The system automatically determines which phase to resume from
        based on the phases_completed list in the checkpoint metadata.
    """
    config = Config.get_instance()

    # Determine which checkpoint to resume
    if feature_id:
        # Check specific feature ID
        checkpoint_path = get_checkpoint_by_feature_id(feature_id, state_dir=f"{acp_dir}/state")

        if not checkpoint_path:
            config.print_error(f"Workflow '{feature_id}' not found")
            config.print_progress("\nUse [cyan]acpctl history[/cyan] to list all workflows")
            raise typer.Exit(1)
    else:
        # Auto-detect latest workflow
        checkpoint_path = get_latest_checkpoint(state_dir=f"{acp_dir}/state")

        if not checkpoint_path:
            config.print_error("No workflows found to resume")
            config.print_progress("\nRun [cyan]acpctl init[/cyan] to start a new workflow")
            raise typer.Exit(1)

        config.print_details(f"[dim]Auto-detected latest workflow[/dim]")

    # Load checkpoint
    try:
        state, metadata = load_checkpoint(checkpoint_path)
        config.print_details(f"[dim]Loaded checkpoint: {checkpoint_path}[/dim]")
    except Exception as e:
        config.print_error(f"Failed to load checkpoint: {e}")
        raise typer.Exit(1)

    # Display resume summary
    display_resume_summary(metadata, config)

    # Check if workflow is already complete
    if metadata.status == "completed":
        config.print_progress(
            "\n[green]✓[/green] Workflow is already completed. Nothing to resume."
        )
        config.print_progress(
            "\n[dim]To view results, check the spec directory:[/dim]"
        )
        if metadata.spec_path:
            config.print_progress(f"  [cyan]{metadata.spec_path}[/cyan]")
        raise typer.Exit(0)

    # Determine next phase to execute
    next_phase = determine_next_phase(metadata.phases_completed, metadata.current_phase)

    if not next_phase:
        config.print_error("Unable to determine next phase")
        config.print_progress(
            "\n[dim]Current phase:[/dim] " + metadata.current_phase
        )
        config.print_progress(
            f"[dim]Completed phases:[/dim] {', '.join(metadata.phases_completed)}"
        )
        raise typer.Exit(1)

    # Display skip message
    display_phase_skip_message(metadata.phases_completed, next_phase, config)

    # Execute next phase based on workflow progression
    if next_phase == "specify":
        execute_specify_phase(state, metadata, checkpoint_path, acp_dir, config)
    elif next_phase == "plan":
        execute_plan_phase(state, metadata, checkpoint_path, acp_dir, config)
    elif next_phase == "implement":
        execute_implement_phase(state, metadata, checkpoint_path, acp_dir, config)
    else:
        config.print_error(f"Unknown phase: {next_phase}")
        raise typer.Exit(1)


def display_resume_summary(metadata, config: Config) -> None:
    """
    Display resume workflow summary.

    Args:
        metadata: CLIMetadata from checkpoint
        config: UI configuration
    """
    summary_lines = [
        f"[bold]Feature:[/bold] {metadata.feature_id}",
        f"[bold]Status:[/bold] {metadata.status}",
        f"[bold]Current Phase:[/bold] {metadata.current_phase}",
    ]

    if metadata.feature_name:
        summary_lines.insert(1, f"[bold]Name:[/bold] {metadata.feature_name}")

    summary = "\n".join(summary_lines)

    panel = Panel(
        summary,
        title="[bold cyan]Resuming Workflow[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )

    config.console.print(panel)


def display_phase_skip_message(phases_completed: list, next_phase: str, config: Config) -> None:
    """
    Display message about skipped phases.

    Args:
        phases_completed: List of completed phase names
        next_phase: Next phase to execute
        config: UI configuration
    """
    if phases_completed:
        skip_message = (
            f"[green]✓[/green] Skipping completed phases: "
            f"[dim]{', '.join(phases_completed)}[/dim]"
        )
        config.print_progress(skip_message)

    config.print_progress(f"[yellow]→[/yellow] Starting phase: [bold]{next_phase}[/bold]\n")


def determine_next_phase(phases_completed: list, current_phase: str) -> Optional[str]:
    """
    Determine next phase to execute based on completed phases.

    Args:
        phases_completed: List of completed phase names
        current_phase: Current phase from metadata

    Returns:
        Next phase name or None if unable to determine

    Phase progression: init → specify → plan → implement → complete
    """
    # Define phase order
    phase_order = ["init", "specify", "plan", "implement", "complete"]

    # Normalize phases_completed (handle aliases: "planning" → "plan", "implementation" → "implement")
    normalized_completed = []
    for phase in phases_completed:
        if phase == "planning":
            normalized_completed.append("plan")
        elif phase == "implementation":
            normalized_completed.append("implement")
        else:
            normalized_completed.append(phase)

    # If current phase is complete, we're done
    if current_phase == "complete":
        return None

    # Find the next incomplete phase
    for phase in phase_order:
        if phase not in normalized_completed:
            return phase

    # All phases complete
    return None


def execute_specify_phase(state, metadata, checkpoint_path: str, acp_dir: str, config: Config) -> None:
    """
    Execute specify phase (placeholder for now).

    Args:
        state: Workflow state
        metadata: CLI metadata
        checkpoint_path: Path to checkpoint file
        acp_dir: ACP directory path
        config: UI configuration
    """
    config.print_warning(
        "[yellow]Specify phase execution not yet implemented in resume command[/yellow]"
    )
    config.print_progress(
        "\n[dim]To continue this workflow, run:[/dim] [cyan]acpctl specify[/cyan]"
    )
    raise typer.Exit(0)


def execute_plan_phase(state, metadata, checkpoint_path: str, acp_dir: str, config: Config) -> None:
    """
    Execute plan phase by calling plan command.

    Args:
        state: Workflow state
        metadata: CLI metadata
        checkpoint_path: Path to checkpoint file
        acp_dir: ACP directory path
        config: UI configuration
    """
    config.print_progress(
        "[cyan]Resuming at planning phase...[/cyan]\n"
    )

    # Import plan command
    from acpctl.cli.commands.plan import plan_command

    try:
        # Call plan command with feature_id from metadata
        # The plan command will handle everything (load checkpoint, run workflow, save)
        plan_command(
            feature_id=metadata.feature_id,
            force=False,
            mock=False,
            acp_dir=acp_dir,
            specs_dir="specs",  # Default
        )

        config.print_progress(
            "\n[green]✓[/green] Planning phase completed successfully"
        )

    except typer.Exit as e:
        # Plan command handles its own exit codes
        raise e
    except Exception as e:
        config.print_error(f"Planning phase failed: {e}")
        if config.is_verbose():
            config.console.print_exception()
        raise typer.Exit(1)


def execute_implement_phase(state, metadata, checkpoint_path: str, acp_dir: str, config: Config) -> None:
    """
    Execute implement phase by calling implement command.

    Args:
        state: Workflow state
        metadata: CLI metadata
        checkpoint_path: Path to checkpoint file
        acp_dir: ACP directory path
        config: UI configuration
    """
    config.print_progress(
        "[cyan]Resuming at implementation phase...[/cyan]\n"
    )

    # Import implement command
    from acpctl.cli.commands.implement import implement_command

    try:
        # Call implement command with feature_id from metadata
        # The implement command will handle everything (load checkpoint, run workflow, save)
        implement_command(
            feature_id=metadata.feature_id,
            force=False,
            mock=False,
            no_tests=False,
            acp_dir=acp_dir,
            specs_dir="specs",  # Default
            output_dir=".",  # Default
        )

        config.print_progress(
            "\n[green]✓[/green] Implementation phase completed successfully"
        )

    except typer.Exit as e:
        # Implement command handles its own exit codes
        raise e
    except Exception as e:
        config.print_error(f"Implementation phase failed: {e}")
        if config.is_verbose():
            config.console.print_exception()
        raise typer.Exit(1)


# Export command
__all__ = ["resume_command"]
