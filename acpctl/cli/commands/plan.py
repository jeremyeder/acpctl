"""
acpctl Plan Command

Generates implementation plan with architecture validation from specification.
Implements planning workflow with Phase 0 (Research) and Phase 1 (Design).

Command:
    acpctl plan [FEATURE_ID] [OPTIONS]

Options:
    --force         Bypass governance violations (dangerous)
    --mock          Use mock LLM responses (for testing)

Architecture:
- Phase 0: Research technical approach (research.md)
- Phase 1: Design implementation plan (plan.md, data-model.md, contracts/, quickstart.md)
- Governance validation after planning
- Interactive violation remediation if needed
- Checkpoint saved after successful completion
- Rich UI with progress indicators

Reference: spec.md (User Story 4), plan.md (Phase 6)
"""

import json
import os
from pathlib import Path
from typing import List, Optional

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table
from typing_extensions import Annotated

from acpctl.agents.architect import ArchitectAgent, create_architect_agent
from acpctl.agents.governance import GovernanceAgent, create_governance_agent
from acpctl.cli.ui import Config
from acpctl.core.checkpoint import load_checkpoint, save_checkpoint
from acpctl.core.state import ACPState
from acpctl.core.workflow import (
    WorkflowBuilder,
    create_governance_error_handler,
    route_planning_governance,
)
from acpctl.storage.artifacts import (
    get_feature_path,
    list_features,
    write_artifact,
)
from acpctl.storage.constitution import constitution_exists, load_constitution


def plan_command(
    feature_id: Annotated[
        Optional[str],
        typer.Argument(help="Feature ID to plan (default: latest)"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Bypass governance violations (dangerous, requires explicit confirmation)",
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
    Generate implementation plan with architecture validation.

    Creates technical design documents from specification including research,
    implementation plan, data models, and API contracts. All artifacts validated
    against constitutional principles.

    [bold]Examples:[/bold]

        # Generate plan for latest feature
        $ acpctl plan

        # Generate plan for specific feature
        $ acpctl plan 001-oauth2-auth

        # Use mock mode for testing
        $ acpctl plan --mock

    [bold]Workflow:[/bold]

        1. Phase 0: Research technical approach (research.md)
        2. Phase 1: Design implementation plan (plan.md, data-model.md, contracts/)
        3. Constitutional validation (governance gate)
        4. Violation remediation (if needed)
        5. Save planning artifacts and checkpoint

    [bold]Output:[/bold]

        specs/NNN-feature/
        ├── spec.md         # Feature specification (existing)
        ├── research.md     # Phase 0: Technical research
        ├── plan.md         # Phase 1: Implementation plan
        ├── data-model.md   # Data entities (if applicable)
        ├── quickstart.md   # Usage guide
        └── contracts/      # API contracts (if applicable)
            └── *.yaml

        .acp/state/
        └── NNN-feature.json    # Updated checkpoint
    """
    config = Config.get_instance()

    # T059: Check if .acp/ exists
    if not constitution_exists(acp_dir):
        config.print_error(
            "Constitutional framework not initialized. Run 'acpctl init' first."
        )
        raise typer.Exit(1)

    # T059: Auto-detect feature ID if not provided
    if feature_id is None:
        feature_id = detect_latest_feature(specs_dir, config)
        if not feature_id:
            config.print_error(
                "No features found. Run 'acpctl specify' to create a specification first."
            )
            raise typer.Exit(1)

        config.print_details(f"[dim]Using latest feature: {feature_id}[/dim]")

    # T059: Check if feature exists
    feature_dir = get_feature_path(feature_id, base_dir=specs_dir)
    if not feature_dir.exists():
        config.print_error(f"Feature '{feature_id}' not found in {specs_dir}/")
        raise typer.Exit(1)

    # T059: Check if spec.md exists
    spec_path = feature_dir / "spec.md"
    if not spec_path.exists():
        config.print_error(
            f"Specification not found at {spec_path}. Run 'acpctl specify' first."
        )
        raise typer.Exit(1)

    # Load spec.md
    try:
        spec_content = spec_path.read_text()
        config.print_details(f"[dim]Loaded specification from {spec_path}[/dim]")
    except Exception as e:
        config.print_error(f"Failed to read specification: {e}")
        raise typer.Exit(1)

    # Load checkpoint (should have spec already)
    checkpoint_path = Path(acp_dir) / "state" / f"{feature_id}.json"
    checkpoint_state = None
    checkpoint_metadata = None

    if checkpoint_path.exists():
        try:
            checkpoint_state, checkpoint_metadata = load_checkpoint(str(checkpoint_path))
            config.print_details(f"[dim]Loaded checkpoint from {checkpoint_path}[/dim]")

            # Check if planning already done
            phases_completed = checkpoint_metadata.phases_completed
            if "plan" in phases_completed or "planning" in phases_completed:
                config.print_warning(
                    f"Planning already completed for feature '{feature_id}'"
                )
                if not Confirm.ask(
                    "Do you want to regenerate the plan?",
                    default=False,
                    console=config.console,
                ):
                    config.print_progress("Planning cancelled")
                    raise typer.Exit(0)

        except FileNotFoundError:
            # No checkpoint exists - this is expected for new features
            config.print_details("[dim]No existing checkpoint found[/dim]")
        except ValueError as e:
            # Checkpoint validation failed - likely corrupted or incompatible
            config.print_error(
                f"Checkpoint file is corrupted or incompatible: {e}\n"
                f"This may happen when switching between --mock and non-mock modes.\n"
                f"\nTo fix (choose one):\n"
                f"  1. Run with {'--mock' if not mock else 'non-mock'} mode\n"
                f"  2. Delete checkpoint: rm {checkpoint_path}\n"
                f"  3. Start fresh: acpctl specify \"description\""
            )
            raise typer.Exit(1)
        except Exception as e:
            # Unexpected error
            config.print_error(
                f"Unexpected error loading checkpoint: {e}\n"
                f"Checkpoint path: {checkpoint_path}"
            )
            if config.is_verbose():
                import traceback
                traceback.print_exc()
            raise typer.Exit(1)
    else:
        config.print_details("[dim]No existing checkpoint found[/dim]")

    # Load constitution
    try:
        constitution = load_constitution(acp_dir)
        config.print_details("[dim]Loaded constitutional principles[/dim]")
    except Exception as e:
        config.print_error(f"Failed to load constitution: {e}")
        raise typer.Exit(1)

    # Initialize state
    if checkpoint_state:
        # Resume from checkpoint
        initial_state = checkpoint_state
        # Ensure we have spec
        if not initial_state.get("spec"):
            initial_state["spec"] = spec_content
        # Update constitution (may have changed)
        initial_state["constitution"] = constitution
        # Reset governance for new phase
        initial_state["governance_passes"] = False
    else:
        # Create new state with feature_description
        # Try to extract feature description from spec or use feature_id as fallback
        feature_description = feature_id  # Fallback

        for line in spec_content.split('\n'):
            if line.startswith('# ') and 'Feature:' in line:
                feature_description = line.split('Feature:')[-1].strip()
                break

        from acpctl.core.state import create_test_state

        initial_state = create_test_state(
            phase="specify",  # Coming from specification phase
            constitution=constitution,
            spec=spec_content,
            feature_description=feature_description,
            governance_passes=True,  # Spec phase passed
        )

    config.print_details("[dim]Initialized workflow state[/dim]")

    # T059: Create agents
    config.print_details("[dim]Initializing AI agents...[/dim]")

    # Use mock mode if --mock flag set or if no LLM configured
    use_mock = mock or not has_llm_configured()

    if use_mock:
        config.print_warning(
            "Using mock mode (no LLM configured or --mock flag set)"
        )

    architect_agent = create_architect_agent(
        llm=None,  # LLM integration will be added later
        mock_mode=use_mock,
    )

    governance_agent = create_governance_agent(
        llm=None,
        mock_mode=use_mock,
    )

    # T059-T061: Execute planning workflow
    config.print_progress("\n[bold]Starting planning workflow...[/bold]")

    # Create violation handler for interactive remediation
    def handle_violations(state: ACPState, violations_data: list) -> ACPState:
        """Interactive handler for constitutional violations."""
        return handle_planning_violations(
            state,
            violations_data,
            architect_agent,
            governance_agent,
            force,
            config,
        )

    # Execute workflow
    try:
        final_state = execute_planning_workflow(
            initial_state,
            architect_agent,
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

    # Verify we have planning artifacts
    if not final_state.get("plan"):
        config.print_error("Workflow completed but no plan was generated")
        raise typer.Exit(1)

    # T059: Write planning artifacts
    try:
        # Write research.md
        if final_state.get("research"):
            research_path = write_artifact(
                feature_id=feature_id,
                artifact_type="research",
                content=final_state["research"],
                base_dir=specs_dir,
            )
            config.print_details(f"[dim]Wrote research to: {research_path}[/dim]")

        # Write plan.md
        plan_path = write_artifact(
            feature_id=feature_id,
            artifact_type="plan",
            content=final_state["plan"],
            base_dir=specs_dir,
        )
        config.print_details(f"[dim]Wrote plan to: {plan_path}[/dim]")

        # Write data-model.md (if applicable)
        if final_state.get("data_model"):
            data_model_path = write_artifact(
                feature_id=feature_id,
                artifact_type="data_model",
                content=final_state["data_model"],
                base_dir=specs_dir,
            )
            config.print_details(f"[dim]Wrote data model to: {data_model_path}[/dim]")

        # Write quickstart.md
        quickstart = final_state.get("code_artifacts", {}).get("quickstart.md", "")
        if quickstart:
            quickstart_path = write_artifact(
                feature_id=feature_id,
                artifact_type="quickstart",
                content=quickstart,
                base_dir=specs_dir,
            )
            config.print_details(f"[dim]Wrote quickstart to: {quickstart_path}[/dim]")

        # Write contracts (if applicable)
        contracts = final_state.get("contracts", {})
        if contracts:
            contracts_dir = feature_dir / "contracts"
            contracts_dir.mkdir(exist_ok=True)

            for filename, content in contracts.items():
                contract_path = contracts_dir / filename
                contract_path.write_text(content)
                config.print_details(f"[dim]Wrote contract to: {contract_path}[/dim]")

    except Exception as e:
        config.print_error(f"Failed to write planning artifacts: {e}")
        raise typer.Exit(1)

    # T059: Save checkpoint
    try:
        # Update checkpoint metadata
        if checkpoint_metadata:
            feature_name = checkpoint_metadata.feature_name or feature_id
            thread_id = checkpoint_metadata.thread_id
            existing_phases = checkpoint_metadata.phases_completed
        else:
            feature_name = feature_id
            thread_id = "plan_" + feature_id
            existing_phases = ["init", "specify"]

        # Add planning to completed phases
        phases_completed = existing_phases.copy()
        if "plan" not in phases_completed and "planning" not in phases_completed:
            phases_completed.append("planning")

        save_checkpoint(
            state=final_state,
            filepath=str(checkpoint_path),
            feature_id=feature_id,
            thread_id=thread_id,
            status="completed",
            phases_completed=phases_completed,
            feature_name=feature_name,
            spec_path=str(feature_dir),
        )
        config.print_details(f"[dim]Saved checkpoint: {checkpoint_path}[/dim]")
    except Exception as e:
        config.print_warning(f"Failed to save checkpoint: {e}")
        # Don't fail command if checkpoint save fails

    # Success message
    display_success_message(
        feature_id, feature_dir, final_state.get("contracts", {}), config
    )


# ============================================================
# WORKFLOW EXECUTION (T060-T061)
# ============================================================


def execute_planning_workflow(
    initial_state: ACPState,
    architect_agent: ArchitectAgent,
    gov_agent: GovernanceAgent,
    violation_handler: callable,
    config: Config,
) -> ACPState:
    """
    Execute planning workflow with Phase 0 and Phase 1.

    Args:
        initial_state: Initial workflow state
        architect_agent: Architect agent
        gov_agent: Governance agent
        violation_handler: Function to handle violations
        config: UI configuration

    Returns:
        Final workflow state

    Raises:
        WorkflowAbortedError: If user aborts workflow
    """
    # T060: Phase 0: Research with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=config.console,
        transient=False,
    ) as progress:
        task_research = progress.add_task(
            "[cyan]Phase 0: Researching technical approach...", total=None
        )

        # Run research phase
        config.print_details("[dim]Running Architect Agent (Research)...[/dim]")

        # T061: Verbose mode - show agent reasoning
        if config.is_verbose():
            display_agent_reasoning_table(
                "Research Phase",
                [
                    ("Input", "Specification"),
                    ("Process", "Analyzing technical challenges"),
                    ("Output", "Research document with recommendations"),
                ],
                config,
            )

        state_after_research = architect_agent.run_research(initial_state)

        progress.update(
            task_research,
            completed=True,
            description="[green]✓[/green] Phase 0: Research complete",
        )

        # T060: Phase 1: Design with progress indicator
        task_design = progress.add_task(
            "[cyan]Phase 1: Designing implementation plan...", total=None
        )

        # Run design phase
        config.print_details("[dim]Running Architect Agent (Design)...[/dim]")

        # T061: Verbose mode - show agent reasoning
        if config.is_verbose():
            display_agent_reasoning_table(
                "Design Phase",
                [
                    ("Input", "Specification + Research"),
                    ("Process", "Creating plan, data model, contracts"),
                    ("Output", "Complete planning artifacts"),
                ],
                config,
            )

        state_after_design = architect_agent.run_design(state_after_research)

        progress.update(
            task_design,
            completed=True,
            description="[green]✓[/green] Phase 1: Design complete",
        )

        # Constitutional validation
        task_gov = progress.add_task(
            "[cyan]Validating against constitution...", total=None
        )

        config.print_details("[dim]Running Governance Agent...[/dim]")

        # T061: Verbose mode - show agent reasoning
        if config.is_verbose():
            display_agent_reasoning_table(
                "Governance Validation",
                [
                    ("Input", "Planning artifacts + Constitution"),
                    ("Process", "Checking compliance with principles"),
                    ("Output", "Pass/Fail with violations"),
                ],
                config,
            )

        state_after_gov = gov_agent(state_after_design)

        progress.update(
            task_gov,
            completed=True,
            description="[green]✓[/green] Constitutional validation complete",
        )

    # Check if governance passed
    if state_after_gov.get("governance_passes"):
        config.print_progress("\n[green]✓[/green] Constitutional validation passed\n")
        return state_after_gov
    else:
        # Handle violations
        config.print_progress("\n[yellow]![/yellow] Constitutional violations detected\n")
        final_state = violation_handler(state_after_gov, [])
        return final_state


# T061: Verbose mode agent reasoning display
def display_agent_reasoning_table(
    phase_name: str,
    reasoning_steps: List[tuple],
    config: Config,
) -> None:
    """
    Display agent reasoning in verbose mode.

    Args:
        phase_name: Name of the phase
        reasoning_steps: List of (step, description) tuples
        config: UI configuration
    """
    table = Table(title=f"[bold]{phase_name}[/bold]", show_header=True)
    table.add_column("Step", style="cyan")
    table.add_column("Description", style="white")

    for step, description in reasoning_steps:
        table.add_row(step, description)

    config.console.print(table)
    config.console.print()  # Blank line


# ============================================================
# VIOLATION REMEDIATION
# ============================================================


class WorkflowAbortedError(Exception):
    """Raised when user aborts workflow."""

    pass


def handle_planning_violations(
    state: ACPState,
    violations_data: list,
    architect_agent: ArchitectAgent,
    gov_agent: GovernanceAgent,
    force_ignore: bool,
    config: Config,
) -> ACPState:
    """
    Handle constitutional violations interactively.

    Prompts user with: [R]egenerate, [E]dit constitution, [A]bort, [I]gnore

    Args:
        state: Current state with violations
        violations_data: List of violation dictionaries
        architect_agent: Architect agent for regeneration
        gov_agent: Governance agent for revalidation
        force_ignore: If True, automatically ignore violations
        config: UI configuration

    Returns:
        Updated state after remediation

    Raises:
        WorkflowAbortedError: If user aborts
    """
    # Extract violations from state
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

    # Display violations
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
    config.console.print("  [R] Regenerate plan (fix violations)")
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
        # Regenerate plan
        config.print_progress("\n[cyan]Regenerating plan...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=config.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Regenerating with fixes...", total=None)

            # Run architect agent again
            state = architect_agent.run_design(state)

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
            return handle_planning_violations(
                state, violations_data, architect_agent, gov_agent, force_ignore, config
            )

    elif choice == "E":
        # Edit constitution
        config.print_progress("\n[cyan]Opening constitution for editing...[/cyan]")

        from acpctl.storage.constitution import get_constitution_path

        const_path = get_constitution_path()

        # Open in editor
        editor = os.environ.get("EDITOR", "nano")
        try:
            import subprocess

            subprocess.run([editor, str(const_path)], check=True)

            # Reload constitution
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
                return handle_planning_violations(
                    state, violations_data, architect_agent, gov_agent, force_ignore, config
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
            return handle_planning_violations(
                state, violations_data, architect_agent, gov_agent, force_ignore, config
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
# HELPER FUNCTIONS
# ============================================================


def detect_latest_feature(specs_dir: str, config: Config) -> Optional[str]:
    """
    Detect the latest feature ID from specs directory.

    Args:
        specs_dir: Base directory for specs
        config: UI configuration

    Returns:
        Latest feature ID or None if no features found
    """
    features = list_features(base_dir=specs_dir)

    if not features:
        return None

    # Sort by ID (numeric part)
    import re

    def get_numeric_id(feature_dict):
        match = re.match(r"^(\d+)-", feature_dict["id"])
        return int(match.group(1)) if match else 0

    features_sorted = sorted(features, key=get_numeric_id, reverse=True)

    return features_sorted[0]["id"]


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


def display_success_message(
    feature_id: str,
    feature_dir: Path,
    contracts: dict,
    config: Config,
) -> None:
    """
    Display success message with Rich panel.

    Args:
        feature_id: Feature ID
        feature_dir: Feature directory path
        contracts: Generated contracts dictionary
        config: UI configuration
    """
    success_parts = [
        "[bold green]Implementation plan generated successfully![/bold green]\n",
        "[bold]Created:[/bold]",
        f"  • {feature_dir}/research.md  - Phase 0: Technical research",
        f"  • {feature_dir}/plan.md  - Phase 1: Implementation plan",
        f"  • {feature_dir}/data-model.md  - Data entities (if applicable)",
        f"  • {feature_dir}/quickstart.md  - Usage guide",
    ]

    if contracts:
        success_parts.append(
            f"  • {feature_dir}/contracts/  - API contracts ({len(contracts)} file(s))"
        )

    success_parts.append(f"  • .acp/state/{feature_id}.json  - Updated checkpoint")

    success_parts.extend(
        [
            "\n[bold]Next Steps:[/bold]",
            f"  1. Review the plan: [cyan]cat {feature_dir}/plan.md[/cyan]",
            "  2. Generate code: [cyan]acpctl implement[/cyan]",
            "\n[dim]Planning workflow checkpoint saved - you can resume anytime.[/dim]",
        ]
    )

    success_message = "\n".join(success_parts)

    if config.should_show_progress():
        config.console.print(
            Panel(
                success_message,
                title="Planning Complete",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        config.print_minimal(f"[green]✓[/green] Plan generated: {feature_dir}/plan.md")


# Export command
__all__ = ["plan_command"]
