"""
acpctl History Command

List all workflow runs with status, phases, and timestamps.
Displays comprehensive workflow history from checkpoint metadata.

Command:
    acpctl history

Options:
    None (displays all workflows)

Architecture:
- Scans .acp/state/ for all checkpoint files
- Loads metadata from each checkpoint
- Displays in Rich Table format
- Sorted by most recent first
- Color-coded status indicators

Reference: spec.md (User Story 3), plan.md (Phase 5)
"""

from datetime import datetime
from typing import List

import typer
from rich.table import Table
from typing_extensions import Annotated

from acpctl.cli.ui import Config
from acpctl.core.checkpoint import list_checkpoints


def history_command(
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
    List all workflows with status and timestamps.

    Displays comprehensive workflow history including feature IDs, names,
    status, current phase, and timestamps. Workflows are sorted by most
    recent first.

    [bold]Examples:[/bold]

        # List all workflows
        $ acpctl history

    [bold]Output:[/bold]

        ┌─────────┬──────────────┬─────────────┬───────────────┬─────────────────────┐
        │ ID      │ Name         │ Status      │ Current Phase │ Updated             │
        ├─────────┼──────────────┼─────────────┼───────────────┼─────────────────────┤
        │ 002     │ user-auth    │ in_progress │ planning      │ 2025-11-05 10:30:00 │
        │ 001     │ oauth2-auth  │ completed   │ implementation│ 2025-11-05 09:00:00 │
        └─────────┴──────────────┴─────────────┴───────────────┴─────────────────────┘

    [bold]Status Colors:[/bold]

        • [green]completed[/green]   - Workflow finished successfully
        • [yellow]in_progress[/yellow] - Workflow currently active
        • [red]failed[/red]       - Workflow encountered errors
        • [dim]pending[/dim]      - Workflow not started
    """
    config = Config.get_instance()

    # Load all checkpoints
    checkpoints = list_checkpoints(state_dir=f"{acp_dir}/state")

    if not checkpoints:
        config.print_error("No workflows found")
        config.print_progress("\nRun [cyan]acpctl init[/cyan] to start your first workflow")
        raise typer.Exit(0)

    # Display workflow history
    display_workflow_history(checkpoints, config)


def display_workflow_history(checkpoints: List[dict], config: Config) -> None:
    """
    Display workflow history in Rich Table format.

    Args:
        checkpoints: List of checkpoint metadata dictionaries
        config: UI configuration
    """
    # Create table
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        title="[bold]Workflow History[/bold]",
        title_style="bold cyan",
    )

    # Add columns
    table.add_column("Feature ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white", no_wrap=False)
    table.add_column("Status", style="white", no_wrap=True)
    table.add_column("Current Phase", style="white", no_wrap=True)
    table.add_column("Started", style="dim", no_wrap=True)
    table.add_column("Updated", style="white", no_wrap=True)

    # Status color mapping
    status_colors = {
        "in_progress": "yellow",
        "completed": "green",
        "failed": "red",
        "pending": "dim",
    }

    # Add rows
    for checkpoint in checkpoints:
        feature_id = checkpoint.get("feature_id", "Unknown")
        feature_name = checkpoint.get("feature_name", "")
        status = checkpoint.get("status", "unknown")
        current_phase = checkpoint.get("current_phase", "unknown")
        started_at = checkpoint.get("started_at", "")
        updated_at = checkpoint.get("updated_at", "")

        # Format timestamps
        started_str = format_timestamp(started_at, short=True)
        updated_str = format_timestamp(updated_at, short=False)

        # Apply status color
        status_color = status_colors.get(status, "white")
        status_display = f"[{status_color}]{status}[/{status_color}]"

        # Truncate feature name if too long
        if len(feature_name) > 20:
            feature_name = feature_name[:17] + "..."

        table.add_row(
            feature_id,
            feature_name or "[dim]—[/dim]",
            status_display,
            current_phase,
            started_str,
            updated_str,
        )

    # Display table
    config.console.print(table)

    # Show summary
    total_count = len(checkpoints)
    completed_count = sum(1 for cp in checkpoints if cp.get("status") == "completed")
    in_progress_count = sum(1 for cp in checkpoints if cp.get("status") == "in_progress")
    failed_count = sum(1 for cp in checkpoints if cp.get("status") == "failed")

    config.print_progress(
        f"\n[bold]Total:[/bold] {total_count} workflows  "
        f"([green]{completed_count} completed[/green], "
        f"[yellow]{in_progress_count} in progress[/yellow]"
    )
    if failed_count > 0:
        config.print_progress(f", [red]{failed_count} failed[/red])", end="")
    config.print_progress(")")

    # Show next steps hint
    if in_progress_count > 0:
        config.print_progress(
            "\n[dim]Use[/dim] [cyan]acpctl resume[/cyan] [dim]to continue an in-progress workflow[/dim]"
        )
    config.print_progress(
        "[dim]Use[/dim] [cyan]acpctl status <feature-id>[/cyan] [dim]to view detailed status[/dim]"
    )


def format_timestamp(timestamp: str, short: bool = False) -> str:
    """
    Format ISO timestamp for display.

    Args:
        timestamp: ISO 8601 timestamp string
        short: If True, show only date; if False, show date and time

    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "[dim]—[/dim]"

    try:
        dt = datetime.fromisoformat(timestamp)
        if short:
            return dt.strftime("%Y-%m-%d")
        else:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return timestamp


# Export command
__all__ = ["history_command"]
