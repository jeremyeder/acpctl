"""
acpctl Init Command

Initializes a project with constitutional governance framework.
Creates .acp/ directory structure and constitutional template.

Command:
    acpctl init [OPTIONS]

Options:
    --force    Skip confirmation prompt if .acp/ already exists

Architecture:
- Detects existing .acp/ directory (idempotency)
- Prompts for confirmation before overwriting
- Creates directory structure (.acp/templates/, .acp/state/, .acp/memory/)
- Generates constitutional template with example principles
- Rich UI with progress indicators and success messages

Reference: plan.md (User Story 1), spec.md (Scenario 1-3)
"""

import os
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing_extensions import Annotated

from acpctl.cli.ui import Config
from acpctl.storage.constitution import create_constitution_template


def _add_to_gitignore(acp_path: Path, config: Config) -> None:
    """
    Add .acp/ directory to .gitignore file.

    Args:
        acp_path: Path to .acp directory
        config: UI config for printing messages

    Raises:
        IOError: If .gitignore cannot be read or written
    """
    # Get project root (parent of .acp/)
    project_root = acp_path.parent
    gitignore_path = project_root / ".gitignore"

    # Entry to add
    acp_entry = ".acp/"

    # Check if .gitignore exists
    if gitignore_path.exists():
        # Read existing content
        content = gitignore_path.read_text()

        # Check if .acp/ is already in .gitignore
        if acp_entry in content or ".acp" in content:
            config.print_details("[dim].acp/ already in .gitignore[/dim]")
            return

        # Append .acp/ to .gitignore
        with gitignore_path.open("a") as f:
            # Add newline if file doesn't end with one
            if content and not content.endswith("\n"):
                f.write("\n")
            f.write(f"{acp_entry}\n")

        config.print_details("[dim]Added .acp/ to .gitignore[/dim]")
    else:
        # Create new .gitignore with .acp/ entry
        gitignore_path.write_text(f"{acp_entry}\n")
        config.print_details("[dim]Created .gitignore with .acp/ entry[/dim]")


def init_command(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Skip confirmation prompt if .acp/ directory already exists",
        ),
    ] = False,
    acp_dir: Annotated[
        str,
        typer.Option(
            "--acp-dir",
            help="ACP directory path (default: .acp)",
            hidden=True,  # Hidden option for testing
        ),
    ] = ".acp",
) -> None:
    """
    Initialize project with constitutional governance.

    Creates .acp/ directory structure and constitutional template.
    Constitutional template includes sections for Core Principles,
    Enterprise Requirements, and Quality Standards.

    [bold]Examples:[/bold]

        # Initialize new project
        $ acpctl init

        # Force overwrite existing setup
        $ acpctl init --force

    [bold]Created Structure:[/bold]

        .acp/
        ├── templates/
        │   └── constitution.md    # Governing principles
        ├── state/                 # Workflow checkpoints
        └── memory/                # Agent memory (Phase 2+)

    [bold]Next Steps:[/bold]

        1. Review and customize .acp/templates/constitution.md
        2. Run 'acpctl specify "your feature"' to start development
    """
    config = Config.get_instance()

    # Convert acp_dir to absolute path for display
    acp_path = Path(acp_dir).resolve()
    constitution_path = acp_path / "templates" / "constitution.md"

    # T019: Check for existing .acp/ directory (idempotency)
    if acp_path.exists():
        config.print_warning(f"Existing .acp/ directory found at: {acp_path}")

        if not force:
            # Prompt for confirmation using Rich
            response = typer.confirm(
                "Do you want to overwrite the existing configuration?",
                default=False,
            )

            if not response:
                config.print_progress("[yellow]Initialization cancelled.[/yellow]")
                raise typer.Exit(0)
        else:
            config.print_details(
                "[dim]--force flag set, skipping confirmation[/dim]"
            )

    # T018 & T020: Create directory structure with Rich progress indicators
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=config.console,
            transient=True,  # Progress disappears after completion
        ) as progress:
            if config.should_show_progress():
                task = progress.add_task(
                    "Creating .acp/ directory structure...",
                    total=None,
                )

            # Create main .acp directory
            acp_path.mkdir(exist_ok=True)
            config.print_details(f"[dim]Created: {acp_path}[/dim]")

            # Create templates subdirectory
            templates_path = acp_path / "templates"
            templates_path.mkdir(exist_ok=True)
            config.print_details(f"[dim]Created: {templates_path}[/dim]")

            # Create state subdirectory
            state_path = acp_path / "state"
            state_path.mkdir(exist_ok=True)
            config.print_details(f"[dim]Created: {state_path}[/dim]")

            # Create memory subdirectory (Phase 2+, but create now)
            memory_path = acp_path / "memory"
            memory_path.mkdir(exist_ok=True)
            config.print_details(f"[dim]Created: {memory_path}[/dim]")

    except OSError as e:
        config.print_error(f"Failed to create directory structure: {e}")
        raise typer.Exit(1)

    # T017: Create constitutional template
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=config.console,
            transient=True,
        ) as progress:
            if config.should_show_progress():
                task = progress.add_task(
                    "Creating constitutional template...",
                    total=None,
                )

            # Get project name from current directory
            project_name = Path.cwd().name

            # Create constitution template
            created_path = create_constitution_template(
                acp_dir=str(acp_path),
                project_name=project_name,
                overwrite=True,  # We already confirmed above
            )

            config.print_details(
                f"[dim]Created constitutional template at: {created_path}[/dim]"
            )

    except Exception as e:
        config.print_error(f"Failed to create constitutional template: {e}")
        raise typer.Exit(1)

    # T082: Add .acp/ to .gitignore
    try:
        _add_to_gitignore(acp_path, config)
    except Exception as e:
        # Non-fatal error - just log it
        config.print_details(f"[dim]Note: Could not update .gitignore: {e}[/dim]")

    # T020: Success message with Rich Panel
    success_message = f"""[bold green]Project initialized successfully![/bold green]

[bold]Created:[/bold]
  • .acp/templates/constitution.md  - Governing principles
  • .acp/state/                     - Workflow checkpoints
  • .acp/memory/                    - Agent memory (Phase 2+)

[bold]Next Steps:[/bold]
  1. Review and customize: [cyan]{constitution_path}[/cyan]
  2. Run: [cyan]acpctl specify "your feature"[/cyan] to start development

[dim]Constitutional governance is now active for this project.[/dim]"""

    if config.should_show_progress():
        config.console.print(
            Panel(
                success_message,
                title="Initialization Complete",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        # Quiet mode: just confirmation
        config.print_minimal("[green]✓[/green] Project initialized successfully")


# Export command for registration
__all__ = ["init_command"]
