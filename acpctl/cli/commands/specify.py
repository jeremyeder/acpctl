"""
acpctl Specify Command

Generates feature specification with pre-flight questionnaire and constitutional validation.
Implements the core specification workflow with governance gates.

Command:
    acpctl specify DESCRIPTION [OPTIONS]

Options:
    --force         Bypass governance violations (dangerous)
    --no-branch     Skip git branch creation
    --mock          Use mock LLM responses (for testing)

Architecture:
- Pre-flight questionnaire collects ALL clarifications upfront
- Workflow executes: specification → governance → error_handler (if needed)
- Interactive violation remediation: [R]egenerate, [E]dit, [A]bort, [I]gnore
- Git branch creation when repository detected
- Checkpoint saved after successful completion
- Rich UI with progress indicators and panels

Reference: spec.md (User Story 2), plan.md (Phase 4)
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from typing_extensions import Annotated

from acpctl.agents.governance import GovernanceAgent, create_governance_agent
from acpctl.agents.specification import SpecificationAgent, create_specification_agent
from acpctl.cli.ui import Config
from acpctl.core.checkpoint import save_checkpoint
from acpctl.core.state import ACPState, create_test_state
from acpctl.core.workflow import (
    WorkflowBuilder,
    create_governance_error_handler,
    route_governance,
)
from acpctl.storage.artifacts import (
    create_feature_directory,
    list_features,
    write_artifact,
)
from acpctl.storage.constitution import constitution_exists, load_constitution


def specify_command(
    description: Annotated[
        str,
        typer.Argument(help="Natural language feature description"),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Bypass governance violations (dangerous, requires explicit confirmation)",
        ),
    ] = False,
    no_branch: Annotated[
        bool,
        typer.Option(
            "--no-branch",
            help="Skip automatic git branch creation",
        ),
    ] = False,
    mock: Annotated[
        bool,
        typer.Option(
            "--mock",
            help="Use mock LLM responses (for testing/development)",
            hidden=True,
        ),
    ] = False,
    acp_dir: Annotated[
        str,
        typer.Option(
            "--acp-dir",
            help="ACP directory path (default: .acp)",
            hidden=True,
        ),
    ] = ".acp",
    specs_dir: Annotated[
        str,
        typer.Option(
            "--specs-dir",
            help="Specs directory path (default: specs)",
            hidden=True,
        ),
    ] = "specs",
) -> None:
    """
    Generate feature specification with pre-flight questions.

    Creates a complete specification document from natural language description.
    Includes upfront clarification questionnaire and constitutional validation.

    [bold]Examples:[/bold]

        # Generate specification with interactive Q&A
        $ acpctl specify "Add OAuth2 authentication"

        # Use mock mode for testing
        $ acpctl specify "Add OAuth2 authentication" --mock

        # Skip git branch creation
        $ acpctl specify "Add OAuth2 authentication" --no-branch

    [bold]Workflow:[/bold]

        1. Pre-flight questionnaire (collect all clarifications upfront)
        2. Specification generation (WHAT and WHY, no HOW)
        3. Constitutional validation (governance gate)
        4. Violation remediation (if needed): [R]egenerate, [E]dit, [A]bort, [I]gnore
        5. Save spec.md and checkpoint

    [bold]Output:[/bold]

        specs/NNN-feature/
        └── spec.md    # Feature specification

        .acp/state/
        └── NNN-feature.json    # Workflow checkpoint
    """
    config = Config.get_instance()

    # T030: Check if .acp/ exists (constitution required)
    if not constitution_exists(acp_dir):
        config.print_error(
            "Constitutional framework not initialized. Run 'acpctl init' first."
        )
        raise typer.Exit(1)

    # T033: Generate feature ID (find next sequential number)
    feature_id = generate_feature_id(specs_dir)
    config.print_details(f"[dim]Generated feature ID: {feature_id}[/dim]")

    # T035: Create git branch if repository detected and not disabled
    branch_created = False
    if not no_branch and is_git_repository():
        branch_name = generate_branch_name(feature_id, description)
        branch_created = create_git_branch(branch_name, config)
        if branch_created:
            config.print_progress(f"Created git branch: [cyan]{branch_name}[/cyan]")

    # T034: Create feature directory
    try:
        feature_dir = create_feature_directory(feature_id, base_dir=specs_dir)
        config.print_details(f"[dim]Created feature directory: {feature_dir}[/dim]")
    except Exception as e:
        config.print_error(f"Failed to create feature directory: {e}")
        raise typer.Exit(1)

    # Load constitution
    try:
        constitution = load_constitution(acp_dir)
        config.print_details("[dim]Loaded constitutional principles[/dim]")
    except Exception as e:
        config.print_error(f"Failed to load constitution: {e}")
        raise typer.Exit(1)

    # T022: Create agents
    config.print_details("[dim]Initializing AI agents...[/dim]")

    # Use mock mode if --mock flag set or if no LLM configured
    use_mock = mock or not has_llm_configured()

    if use_mock:
        config.print_warning(
            "Using mock mode (no LLM configured or --mock flag set)"
        )

    specification_agent = create_specification_agent(
        llm=None,  # LLM integration will be added later
        max_questions=10,
        mock_mode=use_mock,
    )

    governance_agent = create_governance_agent(
        llm=None,
        mock_mode=use_mock,
    )

    # T024: Pre-flight questionnaire (collect ALL clarifications upfront)
    clarifications = conduct_preflight_questionnaire(
        specification_agent, description, config
    )

    # Initialize state
    initial_state = create_test_state(
        phase="init",
        constitution=constitution,
        feature_description=description,
        clarifications=clarifications,
        governance_passes=True,  # Constitution loaded, init phase passes
    )

    config.print_details("[dim]Initialized workflow state[/dim]")

    # T026-T029: Build workflow with specification + governance + error_handler nodes
    config.print_progress("\n[bold]Starting specification workflow...[/bold]")

    # Create violation handler for interactive remediation
    def handle_violations(state: ACPState, violations_data: list) -> ACPState:
        """Interactive handler for constitutional violations."""
        return handle_governance_violations(
            state,
            violations_data,
            specification_agent,
            governance_agent,
            force,
            config,
        )

    # T036: Execute workflow
    try:
        final_state = execute_specification_workflow(
            initial_state,
            specification_agent,
            governance_agent,
            handle_violations,
            config,
        )
    except WorkflowAbortedError as e:
        config.print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        config.print_error(f"Workflow execution failed: {e}")
        if config.is_verbose():
            import traceback

            config.console.print_exception()
        raise typer.Exit(1)

    # Verify we have a spec
    if not final_state.get("spec"):
        config.print_error("Workflow completed but no specification was generated")
        raise typer.Exit(1)

    # Write spec.md to feature directory
    try:
        spec_path = write_artifact(
            feature_id=feature_id,
            artifact_type="spec",
            content=final_state["spec"],
            base_dir=specs_dir,
        )
        config.print_details(f"[dim]Wrote specification to: {spec_path}[/dim]")
    except Exception as e:
        config.print_error(f"Failed to write specification: {e}")
        raise typer.Exit(1)

    # T036: Save checkpoint
    try:
        checkpoint_path = Path(acp_dir) / "state" / f"{feature_id}.json"

        # Generate feature name from description (slugified)
        import re
        feature_name = description.lower()
        feature_name = re.sub(r"[^\w\s-]", "", feature_name)
        feature_name = re.sub(r"[-\s]+", "-", feature_name)
        feature_name = feature_name[:50]  # Limit length

        save_checkpoint(
            state=final_state,
            filepath=str(checkpoint_path),
            feature_id=feature_id,
            thread_id="specify_" + feature_id,
            status="completed",
            phases_completed=["init", "specify"],
            feature_name=feature_name,
            spec_path=str(feature_dir),
        )
        config.print_details(f"[dim]Saved checkpoint: {checkpoint_path}[/dim]")
    except Exception as e:
        config.print_warning(f"Failed to save checkpoint: {e}")
        # Don't fail command if checkpoint save fails

    # Success message
    display_success_message(
        feature_id, spec_path, branch_created, branch_name if branch_created else None, config
    )


# ============================================================
# PRE-FLIGHT QUESTIONNAIRE (T024, T031)
# ============================================================


def conduct_preflight_questionnaire(
    agent: SpecificationAgent,
    description: str,
    config: Config,
) -> List[str]:
    """
    Conduct pre-flight questionnaire to collect clarifications.

    Args:
        agent: Specification agent
        description: Feature description
        config: UI configuration

    Returns:
        List of clarification answers (Q&A pairs formatted as strings)
    """
    config.print_progress("\n[bold]Pre-flight Questionnaire[/bold]")
    config.print_progress(
        "[dim]Analyzing feature description for ambiguities...[/dim]\n"
    )

    # Generate questions
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=config.console,
        transient=True,
    ) as progress:
        if config.should_show_progress():
            task = progress.add_task("Generating questions...", total=None)

        questions = agent.generate_preflight_questions(description)

    if not questions:
        config.print_progress(
            "[green]✓[/green] Feature description is clear, no clarifications needed\n"
        )
        return []

    config.print_progress(
        f"[yellow]![/yellow] Found {len(questions)} ambiguities requiring clarification\n"
    )

    # Display questions and collect answers
    clarifications = []

    for i, question in enumerate(questions, 1):
        # Display question with Rich formatting
        config.console.print(
            f"[bold cyan]Question {i}/{len(questions)}:[/bold cyan] {question}"
        )

        # Get answer from user
        answer = Prompt.ask("[dim]Your answer[/dim]", console=config.console)

        # Store as Q&A pair
        clarification = f"Q: {question}\nA: {answer}"
        clarifications.append(clarification)

        config.console.print()  # Blank line

    config.print_progress(
        f"[green]✓[/green] Collected {len(clarifications)} clarifications\n"
    )

    return clarifications


# ============================================================
# WORKFLOW EXECUTION (T026-T029, T036)
# ============================================================


def execute_specification_workflow(
    initial_state: ACPState,
    spec_agent: SpecificationAgent,
    gov_agent: GovernanceAgent,
    violation_handler: callable,
    config: Config,
) -> ACPState:
    """
    Execute specification workflow with governance validation.

    Args:
        initial_state: Initial workflow state
        spec_agent: Specification agent
        gov_agent: Governance agent
        violation_handler: Function to handle violations
        config: UI configuration

    Returns:
        Final workflow state

    Raises:
        WorkflowAbortedError: If user aborts workflow
    """
    # Build workflow
    builder = WorkflowBuilder(use_checkpointer=False)  # We handle checkpoints ourselves

    # Add nodes
    builder.add_node("specification", spec_agent)
    builder.add_node("governance", gov_agent)

    # Create error handler with custom violation handling
    error_handler = create_governance_error_handler(on_violation=violation_handler)
    builder.add_node("error_handler", error_handler)

    # Add edges
    from langgraph.graph import END, START

    builder.add_edge(START, "specification")
    builder.add_edge("specification", "governance")

    # Conditional routing after governance
    builder.add_conditional_edges(
        "governance",
        route_governance,
        {
            "passed": END,
            "failed": "error_handler",
        },
    )

    # After error handler, either regenerate or end
    builder.add_conditional_edges(
        "error_handler",
        lambda state: "regenerate" if not state.get("governance_passes") else "complete",
        {
            "regenerate": "specification",
            "complete": END,
        },
    )

    # Compile workflow
    workflow = builder.compile()

    # Execute with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=config.console,
        transient=False,
    ) as progress:
        task_spec = progress.add_task("[cyan]Generating specification...", total=None)

        # Run specification agent
        config.print_details("[dim]Running Specification Agent...[/dim]")
        state_after_spec = spec_agent(initial_state)

        progress.update(task_spec, completed=True)
        task_gov = progress.add_task("[cyan]Validating against constitution...", total=None)

        # Run governance agent
        config.print_details("[dim]Running Governance Agent...[/dim]")
        state_after_gov = gov_agent(state_after_spec)

        progress.update(task_gov, completed=True)

    # Check if governance passed
    if state_after_gov.get("governance_passes"):
        config.print_progress("[green]✓[/green] Constitutional validation passed\n")
        return state_after_gov
    else:
        # Handle violations
        config.print_progress("[yellow]![/yellow] Constitutional violations detected\n")
        final_state = violation_handler(state_after_gov, [])
        return final_state


# ============================================================
# VIOLATION REMEDIATION (T029, T032)
# ============================================================


class WorkflowAbortedError(Exception):
    """Raised when user aborts workflow."""

    pass


def handle_governance_violations(
    state: ACPState,
    violations_data: list,
    spec_agent: SpecificationAgent,
    gov_agent: GovernanceAgent,
    force_ignore: bool,
    config: Config,
) -> ACPState:
    """
    Handle constitutional violations interactively.

    Prompts user with: [R]egenerate, [E]dit constitution, [A]bort, [I]gnore

    Args:
        state: Current state with violations
        violations_data: List of violation dictionaries (passed in from error handler)
        spec_agent: Specification agent for regeneration
        gov_agent: Governance agent for revalidation
        force_ignore: If True, automatically ignore violations
        config: UI configuration

    Returns:
        Updated state after remediation

    Raises:
        WorkflowAbortedError: If user aborts
    """
    # Extract violations from state (stored as JSON string)
    import json

    violations_json = (
        state.get("code_artifacts", {}).get("_governance_violations.json", "[]")
    )

    try:
        violations_data = json.loads(violations_json)
    except (json.JSONDecodeError, TypeError):
        violations_data = []

    if not violations_data:
        # No violations, pass governance
        state["governance_passes"] = True
        return state

    # Display violations in Rich panel
    display_violations(violations_data, config)

    # If force flag set, prompt for confirmation
    if force_ignore:
        config.print_warning(
            "[bold yellow]--force flag set: Ignoring constitutional violations[/bold yellow]"
        )
        if not Confirm.ask(
            "Are you sure you want to proceed with violations?",
            default=False,
            console=config.console,
        ):
            raise WorkflowAbortedError("User declined to force-ignore violations")

        state["governance_passes"] = True
        return state

    # Interactive remediation
    config.console.print("\n[bold]How would you like to proceed?[/bold]")
    config.console.print("  [R] Regenerate specification (fix violations)")
    config.console.print("  [E] Edit constitution (modify principles)")
    config.console.print("  [A] Abort workflow (cancel operation)")
    config.console.print("  [I] Ignore violations (proceed anyway, not recommended)\n")

    choice = Prompt.ask(
        "Your choice",
        choices=["R", "r", "E", "e", "A", "a", "I", "i"],
        default="R",
        console=config.console,
    ).upper()

    if choice == "R":
        # Regenerate specification
        config.print_progress("\n[cyan]Regenerating specification...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=config.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Regenerating with fixes...", total=None)

            # Run spec agent again (keeps existing clarifications)
            state = spec_agent(state)

            # Run governance again
            state = gov_agent(state)

        # Check if passes now
        if state.get("governance_passes"):
            config.print_progress(
                "[green]✓[/green] Regeneration successful, violations resolved\n"
            )
            return state
        else:
            # Still has violations, recurse
            config.print_warning("Violations still present after regeneration")
            return handle_governance_violations(
                state, violations_data, spec_agent, gov_agent, force_ignore, config
            )

    elif choice == "E":
        # Edit constitution
        config.print_progress("\n[cyan]Opening constitution for editing...[/cyan]")

        # Get constitution path
        from acpctl.storage.constitution import get_constitution_path

        const_path = get_constitution_path()

        # Open in editor
        editor = os.environ.get("EDITOR", "nano")
        try:
            subprocess.run([editor, str(const_path)], check=True)

            # Reload constitution
            from acpctl.storage.constitution import load_constitution

            state["constitution"] = load_constitution()

            config.print_progress("[green]✓[/green] Constitution updated\n")

            # Re-run governance with new constitution
            config.print_progress("[cyan]Re-validating with updated constitution...[/cyan]")
            state = gov_agent(state)

            if state.get("governance_passes"):
                config.print_progress(
                    "[green]✓[/green] Validation passed with updated constitution\n"
                )
                return state
            else:
                # Still fails, recurse
                return handle_governance_violations(
                    state, violations_data, spec_agent, gov_agent, force_ignore, config
                )

        except Exception as e:
            config.print_error(f"Failed to edit constitution: {e}")
            raise WorkflowAbortedError("Constitution edit failed")

    elif choice == "A":
        # Abort
        config.print_progress("\n[yellow]Workflow aborted by user[/yellow]")
        raise WorkflowAbortedError("User aborted workflow")

    elif choice == "I":
        # Ignore (with warning)
        config.print_warning(
            "[bold yellow]Ignoring violations - this is not recommended![/bold yellow]"
        )

        if not Confirm.ask(
            "Are you absolutely sure?",
            default=False,
            console=config.console,
        ):
            # User reconsidered, show menu again
            return handle_governance_violations(
                state, violations_data, spec_agent, gov_agent, force_ignore, config
            )

        state["governance_passes"] = True
        config.print_warning("Proceeding with constitutional violations ignored\n")
        return state

    return state


def display_violations(violations_data: list, config: Config) -> None:
    """
    Display constitutional violations in Rich panel.

    Args:
        violations_data: List of violation dictionaries
        config: UI configuration
    """
    # Create table for violations
    table = Table(show_header=True, header_style="bold red", border_style="red")
    table.add_column("Principle", style="cyan", no_wrap=False)
    table.add_column("Location", style="yellow")
    table.add_column("Explanation", style="white", no_wrap=False)
    table.add_column("Suggestion", style="green", no_wrap=False)

    for v in violations_data:
        table.add_row(
            v.get("principle", "Unknown"),
            v.get("location", "Unknown"),
            v.get("explanation", "No explanation"),
            v.get("suggestion", "No suggestion"),
        )

    # Wrap in panel
    panel = Panel(
        table,
        title=f"[bold red]Constitutional Violations ({len(violations_data)})[/bold red]",
        border_style="red",
        padding=(1, 2),
    )

    config.console.print(panel)


# ============================================================
# FEATURE ID GENERATION (T033)
# ============================================================


def generate_feature_id(specs_dir: str = "specs") -> str:
    """
    Generate next sequential feature ID.

    Args:
        specs_dir: Base directory for specs

    Returns:
        Feature ID in format "NNN-feature" (e.g., "002-oauth2")

    Example:
        >>> feature_id = generate_feature_id()
        >>> print(feature_id)
        '002-feature'
    """
    features = list_features(base_dir=specs_dir)

    if not features:
        return "001-feature"

    # Extract numeric IDs
    max_id = 0
    for feature in features:
        match = re.match(r"^(\d+)-", feature["id"])
        if match:
            feature_num = int(match.group(1))
            max_id = max(max_id, feature_num)

    # Next ID
    next_id = max_id + 1
    return f"{next_id:03d}-feature"


# ============================================================
# GIT INTEGRATION (T035)
# ============================================================


def is_git_repository() -> bool:
    """Check if current directory is a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def generate_branch_name(feature_id: str, description: str) -> str:
    """
    Generate git branch name from feature ID and description.

    Args:
        feature_id: Feature ID (e.g., "001-feature")
        description: Feature description

    Returns:
        Branch name (e.g., "001-add-oauth2-authentication")

    Example:
        >>> name = generate_branch_name("001-feature", "Add OAuth2 authentication")
        >>> print(name)
        '001-add-oauth2-authentication'
    """
    # Extract numeric ID
    numeric_id = feature_id.split("-")[0]

    # Slugify description
    slug = description.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    slug = slug[:50]  # Limit length

    return f"{numeric_id}-{slug}"


def create_git_branch(branch_name: str, config: Config) -> bool:
    """
    Create and checkout git branch.

    Args:
        branch_name: Branch name to create
        config: UI configuration

    Returns:
        True if branch created successfully, False otherwise
    """
    try:
        # Check if branch already exists
        result = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            config.print_warning(f"Branch '{branch_name}' already exists, skipping creation")
            return False

        # Create and checkout branch
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            capture_output=True,
            text=True,
            check=True,
        )

        return True

    except subprocess.CalledProcessError as e:
        config.print_warning(f"Failed to create git branch: {e.stderr}")
        return False
    except FileNotFoundError:
        config.print_warning("git command not found")
        return False


# ============================================================
# LLM CONFIGURATION CHECK
# ============================================================


def has_llm_configured() -> bool:
    """
    Check if LLM is configured (API key available).

    Returns:
        True if OPENAI_API_KEY or other LLM env var is set
    """
    return (
        os.environ.get("OPENAI_API_KEY") is not None
        or os.environ.get("ANTHROPIC_API_KEY") is not None
        or os.environ.get("AZURE_OPENAI_API_KEY") is not None
    )


# ============================================================
# SUCCESS MESSAGE (T031)
# ============================================================


def display_success_message(
    feature_id: str,
    spec_path: Path,
    branch_created: bool,
    branch_name: Optional[str],
    config: Config,
) -> None:
    """
    Display success message with Rich panel.

    Args:
        feature_id: Feature ID
        spec_path: Path to spec file
        branch_created: Whether git branch was created
        branch_name: Git branch name (if created)
        config: UI configuration
    """
    success_parts = [
        "[bold green]Specification generated successfully![/bold green]\n",
        "[bold]Created:[/bold]",
        f"  • {spec_path}  - Feature specification",
        f"  • .acp/state/{feature_id}.json  - Workflow checkpoint",
    ]

    if branch_created:
        success_parts.append(f"  • Git branch: [cyan]{branch_name}[/cyan]")

    success_parts.extend(
        [
            "\n[bold]Next Steps:[/bold]",
            "  1. Review the specification: [cyan]cat " + str(spec_path) + "[/cyan]",
            "  2. Generate implementation plan: [cyan]acpctl plan[/cyan]",
            "\n[dim]Feature workflow checkpoint saved - you can resume anytime.[/dim]",
        ]
    )

    success_message = "\n".join(success_parts)

    if config.should_show_progress():
        config.console.print(
            Panel(
                success_message,
                title="Specification Complete",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        config.print_minimal(f"[green]✓[/green] Specification generated: {spec_path}")


# Export command
__all__ = ["specify_command"]
