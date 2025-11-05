"""
acpctl Status Command

Display current workflow state and checkpoint information.
Shows feature ID, status, current phase, completed phases, and timestamps.

Command:
    acpctl status [FEATURE_ID]

Options:
    FEATURE_ID: Optional feature ID to check (defaults to latest workflow)

Architecture:
- Loads checkpoint metadata from .acp/state/
- Displays formatted status using Rich Table
- Auto-detects latest workflow if no feature ID provided
- Shows phase completion with checkmarks

Reference: spec.md (User Story 3), plan.md (Phase 5)
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table
from typing_extensions import Annotated

from acpctl.cli.ui import Config
from acpctl.core.checkpoint import get_checkpoint_by_feature_id, get_latest_checkpoint, load_checkpoint


def status_command(
    feature_id: Annotated[
        Optional[str],
        typer.Argument(help="Feature ID to check status (defaults to latest)"),
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
    Show current workflow state and checkpoint information.

    Displays feature ID, status, current phase, completed phases, and timestamps.
    If no feature ID is provided, shows status of the most recent workflow.

    [bold]Examples:[/bold]

        # Show status of latest workflow
        $ acpctl status

        # Show status of specific workflow
        $ acpctl status 001-oauth2-authentication

    [bold]Output:[/bold]

        Feature: 001-oauth2-authentication
        Status: in_progress
        Current Phase: specification
        Completed Phases: ✓ specification
        Last Updated: 2025-11-05 10:30:00
    """
    config = Config.get_instance()

    # Determine which checkpoint to display
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
            config.print_error("No workflows found")
            config.print_progress("\nRun [cyan]acpctl init[/cyan] to start a new workflow")
            raise typer.Exit(1)

        config.print_details(f"[dim]Auto-detected latest workflow[/dim]")

    # Load checkpoint
    try:
        state, metadata = load_checkpoint(checkpoint_path)
    except Exception as e:
        config.print_error(f"Failed to load checkpoint: {e}")
        raise typer.Exit(1)

    # Display status
    display_workflow_status(metadata, config)


def display_workflow_status(metadata, config: Config) -> None:
    """
    Display workflow status in Rich panel format.

    Args:
        metadata: CLIMetadata from checkpoint
        config: UI configuration
    """
    # Determine status color
    status_colors = {
        "in_progress": "yellow",
        "completed": "green",
        "failed": "red",
        "pending": "dim",
    }
    status_color = status_colors.get(metadata.status, "white")

    # Format phases completed
    all_phases = ["init", "specify", "plan", "implement"]
    phases_display = []
    for phase in all_phases:
        if phase in metadata.phases_completed:
            phases_display.append(f"[green]✓[/green] {phase}")
        elif phase == metadata.current_phase:
            phases_display.append(f"[yellow]→[/yellow] {phase}")
        else:
            phases_display.append(f"[dim]○[/dim] {phase}")

    # Format timestamps
    try:
        started = datetime.fromisoformat(metadata.started_at)
        started_str = started.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        started_str = metadata.started_at or "Unknown"

    try:
        updated = datetime.fromisoformat(metadata.updated_at)
        updated_str = updated.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        updated_str = metadata.updated_at or "Unknown"

    # Build status table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Feature ID", metadata.feature_id)
    if metadata.feature_name:
        table.add_row("Feature Name", metadata.feature_name)
    table.add_row("Status", f"[{status_color}]{metadata.status}[/{status_color}]")
    table.add_row("Current Phase", f"[bold]{metadata.current_phase}[/bold]")
    table.add_row("Phases", "\n".join(phases_display))
    if metadata.spec_path:
        table.add_row("Spec Path", metadata.spec_path)
    table.add_row("Started", started_str)
    table.add_row("Last Updated", updated_str)
    table.add_row("Thread ID", f"[dim]{metadata.thread_id}[/dim]")

    # Wrap in panel
    panel = Panel(
        table,
        title=f"[bold]Workflow Status[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )

    config.console.print(panel)

    # Show next steps based on current phase
    if metadata.status == "completed":
        config.print_progress(
            "\n[green]✓[/green] Workflow completed successfully!"
        )
    elif metadata.status == "in_progress":
        next_steps = {
            "init": "Run [cyan]acpctl specify[/cyan] to generate specification",
            "specify": "Run [cyan]acpctl plan[/cyan] to generate implementation plan",
            "plan": "Run [cyan]acpctl implement[/cyan] to generate code",
            "implement": "Review and test the generated code",
        }
        next_step = next_steps.get(metadata.current_phase)
        if next_step:
            config.print_progress(f"\n[bold]Next Step:[/bold] {next_step}")


# Export command
__all__ = ["status_command"]
