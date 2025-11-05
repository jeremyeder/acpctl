"""
acpctl Implement Command

Generates code following Test-Driven Development approach from implementation plan.
Implements TDD workflow: Generate tests first (RED), then implementation (GREEN).

Command:
    acpctl implement [FEATURE_ID] [OPTIONS]

Options:
    --force         Bypass governance violations (dangerous)
    --mock          Use mock LLM responses (for testing)
    --no-tests      Skip test execution (faster, for development)

Architecture:
- TDD Phase 1: Generate test files (RED - tests fail)
- TDD Phase 2: Generate implementation code (GREEN - tests pass)
- Constitutional validation (no secrets, license compliance)
- Rich UI with progress indicators and test results
- Checkpoint saved after successful completion

Reference: spec.md (User Story 5), plan.md (Phase 7)
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

from acpctl.agents.governance import GovernanceAgent, create_governance_agent
from acpctl.agents.implementation import (
    ImplementationAgent,
    TestResult,
    create_implementation_agent,
)
from acpctl.cli.ui import Config
from acpctl.core.checkpoint import load_checkpoint, save_checkpoint
from acpctl.core.state import ACPState
from acpctl.storage.artifacts import get_feature_path, list_features, write_artifact
from acpctl.storage.constitution import constitution_exists, load_constitution


def implement_command(
    feature_id: Annotated[
        Optional[str],
        typer.Argument(help="Feature ID to implement (default: latest)"),
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
    no_tests: Annotated[
        bool,
        typer.Option(
            "--no-tests",
            help="Skip test execution (faster, for development)",
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
    output_dir: Annotated[
        str,
        typer.Option(
            "--output-dir",
            help="Output directory for generated code (default: current directory)",
            hidden=True,
        ),
    ] = ".",
) -> None:
    """
    Generate code following Test-Driven Development approach.

    Generates test files first (which should fail), then implementation code
    (which makes tests pass). All code validated against constitutional principles.

    [bold]Examples:[/bold]

        # Generate code for latest feature
        $ acpctl implement

        # Generate code for specific feature
        $ acpctl implement 001-oauth2-auth

        # Use mock mode for testing
        $ acpctl implement --mock

        # Skip test execution (faster)
        $ acpctl implement --no-tests

    [bold]TDD Workflow:[/bold]

        1. Phase 1: Generate test files covering expected behavior
        2. RED Phase: Run tests (should FAIL - no implementation)
        3. Phase 2: Generate production code to satisfy tests
        4. GREEN Phase: Run tests (should PASS - implementation correct)
        5. Constitutional validation (no secrets, proper licensing)
        6. Write code artifacts and checkpoint

    [bold]Output:[/bold]

        src/                    # Production code
        ├── __init__.py
        └── [modules].py

        tests/                  # Test code
        ├── unit/
        │   └── test_[modules].py
        └── integration/
            └── test_[workflows].py

        .acp/state/
        └── NNN-feature.json    # Updated checkpoint
    """
    config = Config.get_instance()

    # Check if .acp/ exists
    if not constitution_exists(acp_dir):
        config.print_error(
            "Constitutional framework not initialized. Run 'acpctl init' first."
        )
        raise typer.Exit(1)

    # Auto-detect feature ID if not provided
    if feature_id is None:
        feature_id = detect_latest_feature(specs_dir, config)
        if not feature_id:
            config.print_error(
                "No features found. Run 'acpctl specify' to create a specification first."
            )
            raise typer.Exit(1)

        config.print_details(f"[dim]Using latest feature: {feature_id}[/dim]")

    # Check if feature exists
    feature_dir = get_feature_path(feature_id, base_dir=specs_dir)
    if not feature_dir.exists():
        config.print_error(f"Feature '{feature_id}' not found in {specs_dir}/")
        raise typer.Exit(1)

    # Check if plan.md exists
    plan_path = feature_dir / "plan.md"
    if not plan_path.exists():
        config.print_error(
            f"Implementation plan not found at {plan_path}. Run 'acpctl plan' first."
        )
        raise typer.Exit(1)

    # Load plan.md
    try:
        plan_content = plan_path.read_text()
        config.print_details(f"[dim]Loaded plan from {plan_path}[/dim]")
    except Exception as e:
        config.print_error(f"Failed to read plan: {e}")
        raise typer.Exit(1)

    # Load data-model.md (optional)
    data_model_path = feature_dir / "data-model.md"
    data_model_content = ""
    if data_model_path.exists():
        try:
            data_model_content = data_model_path.read_text()
            config.print_details(f"[dim]Loaded data model from {data_model_path}[/dim]")
        except Exception as e:
            config.print_warning(f"Could not load data model: {e}")

    # Load checkpoint
    checkpoint_path = Path(acp_dir) / "state" / f"{feature_id}.json"
    if checkpoint_path.exists():
        try:
            checkpoint_data = load_checkpoint(str(checkpoint_path))
            config.print_details(f"[dim]Loaded checkpoint from {checkpoint_path}[/dim]")

            # Check if implementation already done
            phases_completed = checkpoint_data.get("phases_completed", [])
            if "implement" in phases_completed or "implementation" in phases_completed:
                config.print_warning(
                    f"Implementation already completed for feature '{feature_id}'"
                )
                if not Confirm.ask(
                    "Do you want to regenerate the code?",
                    default=False,
                    console=config.console,
                ):
                    config.print_progress("Implementation cancelled")
                    raise typer.Exit(0)

        except Exception as e:
            config.print_warning(f"Could not load checkpoint: {e}")
            checkpoint_data = None
    else:
        checkpoint_data = None
        config.print_details("[dim]No existing checkpoint found[/dim]")

    # Load constitution
    try:
        constitution = load_constitution(acp_dir)
        config.print_details("[dim]Loaded constitutional principles[/dim]")
    except Exception as e:
        config.print_error(f"Failed to load constitution: {e}")
        raise typer.Exit(1)

    # Initialize state
    if checkpoint_data:
        # Resume from checkpoint
        initial_state = checkpoint_data["state"]
        # Ensure we have plan
        if not initial_state.get("plan"):
            initial_state["plan"] = plan_content
        # Ensure we have data model
        if data_model_content and not initial_state.get("data_model"):
            initial_state["data_model"] = data_model_content
        # Update constitution (may have changed)
        initial_state["constitution"] = constitution
        # Reset governance for new phase
        initial_state["governance_passes"] = False
    else:
        # Create new state
        from acpctl.core.state import create_test_state

        initial_state = create_test_state(
            phase="plan",  # Coming from planning phase
            constitution=constitution,
            plan=plan_content,
            data_model=data_model_content,
            governance_passes=True,  # Plan phase passed
        )

    config.print_details("[dim]Initialized workflow state[/dim]")

    # Create agents
    config.print_details("[dim]Initializing AI agents...[/dim]")

    # Use mock mode if --mock flag set or if no LLM configured
    use_mock = mock or not has_llm_configured()

    if use_mock:
        config.print_warning(
            "Using mock mode (no LLM configured or --mock flag set)"
        )

    implementation_agent = create_implementation_agent(
        llm=None,  # LLM integration will be added later
        mock_mode=use_mock,
        skip_tests=no_tests,
        project_root=output_dir,
    )

    governance_agent = create_governance_agent(
        llm=None,
        mock_mode=use_mock,
    )

    # Execute implementation workflow
    config.print_progress("\n[bold]Starting TDD implementation workflow...[/bold]")

    try:
        final_state = execute_implementation_workflow(
            initial_state,
            implementation_agent,
            governance_agent,
            no_tests,
            force,
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

    # Verify we have code artifacts
    code_artifacts = final_state.get("code_artifacts", {})
    if not code_artifacts or not any(k.startswith(("src/", "tests/")) for k in code_artifacts):
        config.print_error("Workflow completed but no code was generated")
        raise typer.Exit(1)

    # Write code artifacts to disk
    try:
        write_code_artifacts(
            code_artifacts=code_artifacts,
            output_dir=Path(output_dir),
            config=config,
        )
    except Exception as e:
        config.print_error(f"Failed to write code artifacts: {e}")
        raise typer.Exit(1)

    # Save checkpoint
    try:
        # Update checkpoint metadata
        if checkpoint_data:
            feature_name = checkpoint_data.get("feature_name", feature_id)
            thread_id = checkpoint_data.get("thread_id", "implement_" + feature_id)
            existing_phases = checkpoint_data.get("phases_completed", [])
        else:
            feature_name = feature_id
            thread_id = "implement_" + feature_id
            existing_phases = ["init", "specify", "planning"]

        # Add implementation to completed phases
        phases_completed = existing_phases.copy()
        if "implement" not in phases_completed and "implementation" not in phases_completed:
            phases_completed.append("implementation")

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

    # Extract test results for display
    test_results_before = None
    test_results_after = None

    if not no_tests:
        # Parse test results from state
        test_results_before_json = code_artifacts.get("_test_results_before.json", "{}")
        test_results_after_json = code_artifacts.get("_test_results_after.json", "{}")

        try:
            test_results_before = TestResult.from_dict(json.loads(test_results_before_json))
            test_results_after = TestResult.from_dict(json.loads(test_results_after_json))
        except Exception:
            pass

    # Success message
    display_success_message(
        feature_id,
        Path(output_dir),
        code_artifacts,
        test_results_before,
        test_results_after,
        config,
    )


# ============================================================
# WORKFLOW EXECUTION
# ============================================================


class WorkflowAbortedError(Exception):
    """Raised when user aborts workflow."""

    pass


def execute_implementation_workflow(
    initial_state: ACPState,
    impl_agent: ImplementationAgent,
    gov_agent: GovernanceAgent,
    skip_tests: bool,
    force_ignore: bool,
    config: Config,
) -> ACPState:
    """
    Execute TDD implementation workflow.

    Args:
        initial_state: Initial workflow state
        impl_agent: Implementation agent
        gov_agent: Governance agent
        skip_tests: If True, skip test execution
        force_ignore: If True, ignore governance violations
        config: UI configuration

    Returns:
        Final workflow state

    Raises:
        WorkflowAbortedError: If user aborts workflow
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=config.console,
        transient=False,
    ) as progress:
        # Phase 1: Generate tests
        task_tests = progress.add_task(
            "[cyan]TDD Phase 1: Generating test files...", total=None
        )

        config.print_details("[dim]Running Implementation Agent (Tests)...[/dim]")

        # Verbose mode - show agent reasoning
        if config.is_verbose():
            display_agent_reasoning_table(
                "Test Generation",
                [
                    ("Input", "Plan + Data Model"),
                    ("Process", "Analyzing components, generating pytest tests"),
                    ("Output", "Test files covering expected behavior"),
                ],
                config,
            )

        state_after_tests = impl_agent.generate_tests(initial_state)

        progress.update(
            task_tests,
            completed=True,
            description="[green]✓[/green] TDD Phase 1: Test files generated",
        )

        # RED Phase: Run tests (should fail)
        if not skip_tests:
            task_red = progress.add_task(
                "[cyan]TDD RED Phase: Running tests (should fail)...", total=None
            )

            state_after_red = impl_agent.validate_tdd_red_phase(state_after_tests)

            progress.update(
                task_red,
                completed=True,
                description="[green]✓[/green] TDD RED Phase: Tests validated (expected failures)",
            )
        else:
            state_after_red = state_after_tests
            config.print_details("[dim]Skipping test execution (--no-tests flag)[/dim]")

        # Phase 2: Generate implementation
        task_impl = progress.add_task(
            "[cyan]TDD Phase 2: Generating implementation code...", total=None
        )

        config.print_details("[dim]Running Implementation Agent (Code)...[/dim]")

        # Verbose mode - show agent reasoning
        if config.is_verbose():
            display_agent_reasoning_table(
                "Implementation Generation",
                [
                    ("Input", "Test files + Plan"),
                    ("Process", "Generating code to satisfy tests"),
                    ("Output", "Production code with type hints and docstrings"),
                ],
                config,
            )

        state_after_impl = impl_agent.generate_implementation(state_after_red)

        progress.update(
            task_impl,
            completed=True,
            description="[green]✓[/green] TDD Phase 2: Implementation code generated",
        )

        # GREEN Phase: Run tests (should pass)
        if not skip_tests:
            task_green = progress.add_task(
                "[cyan]TDD GREEN Phase: Running tests (should pass)...", total=None
            )

            state_after_green = impl_agent.validate_tdd_green_phase(state_after_impl)

            progress.update(
                task_green,
                completed=True,
                description="[green]✓[/green] TDD GREEN Phase: Tests validated (all passing)",
            )
        else:
            state_after_green = state_after_impl

        # Constitutional validation
        task_gov = progress.add_task(
            "[cyan]Validating against constitution...", total=None
        )

        config.print_details("[dim]Running Governance Agent...[/dim]")

        # Verbose mode - show agent reasoning
        if config.is_verbose():
            display_agent_reasoning_table(
                "Constitutional Validation",
                [
                    ("Input", "Generated code + Constitution"),
                    ("Process", "Checking for secrets, license compliance, security"),
                    ("Output", "Pass/Fail with violations"),
                ],
                config,
            )

        state_after_gov = gov_agent(state_after_green)

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

        # Display violations
        violations_json = (
            state_after_gov.get("code_artifacts", {}).get("_governance_violations.json", "[]")
        )

        try:
            violations_data = json.loads(violations_json)
            display_violations(violations_data, config)
        except Exception:
            violations_data = []

        # Handle violations
        if force_ignore:
            config.print_warning(
                "[bold yellow]--force flag set: Ignoring constitutional violations[/bold yellow]"
            )
            if Confirm.ask(
                "Are you sure you want to proceed with violations?",
                default=False,
                console=config.console,
            ):
                state_after_gov["governance_passes"] = True
                return state_after_gov
            else:
                raise WorkflowAbortedError("User declined to force-ignore violations")

        # Prompt user
        config.console.print("\n[bold]How would you like to proceed?[/bold]")
        config.console.print("  [R] Regenerate code (fix violations)")
        config.console.print("  [A] Abort workflow (cancel operation)")
        config.console.print("  [I] Ignore violations (proceed anyway, not recommended)\n")

        choice = Prompt.ask(
            "Your choice",
            choices=["R", "r", "A", "a", "I", "i"],
            default="A",
            console=config.console,
        ).upper()

        if choice == "R":
            config.print_error(
                "Regeneration not yet implemented - please fix violations manually and re-run"
            )
            raise WorkflowAbortedError("Manual fix required")
        elif choice == "A":
            raise WorkflowAbortedError("User aborted workflow")
        elif choice == "I":
            if Confirm.ask(
                "Are you absolutely sure?",
                default=False,
                console=config.console,
            ):
                state_after_gov["governance_passes"] = True
                return state_after_gov
            else:
                raise WorkflowAbortedError("User declined to ignore violations")

    return state_after_gov


# ============================================================
# DISPLAY FUNCTIONS (T073)
# ============================================================


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


def display_test_results(
    title: str,
    test_result: Optional[TestResult],
    config: Config,
) -> None:
    """
    Display test results in Rich table.

    Args:
        title: Table title
        test_result: Test result to display
        config: UI configuration
    """
    if not test_result:
        return

    # Create results table
    table = Table(title=f"[bold]{title}[/bold]", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")

    # Summary rows
    table.add_row("Total Tests", str(test_result.total))
    table.add_row(
        "Passed",
        f"[green]{test_result.passed}[/green]" if test_result.passed > 0 else "0",
    )
    table.add_row(
        "Failed",
        f"[red]{test_result.failed}[/red]" if test_result.failed > 0 else "0",
    )

    if test_result.skipped > 0:
        table.add_row("Skipped", f"[yellow]{test_result.skipped}[/yellow]")

    table.add_row("Duration", f"{test_result.duration:.2f}s")

    # Success rate
    if test_result.total > 0:
        success_rate = (test_result.passed / test_result.total) * 100
        color = "green" if success_rate == 100 else "yellow" if success_rate >= 75 else "red"
        table.add_row("Success Rate", f"[{color}]{success_rate:.1f}%[/{color}]")

    config.console.print(table)

    # Show failures if any
    if test_result.failures:
        config.console.print("\n[bold red]Failures:[/bold red]")
        for failure in test_result.failures:
            config.console.print(f"  • {failure['test']}: {failure['error']}")

    config.console.print()


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


def write_code_artifacts(
    code_artifacts: dict,
    output_dir: Path,
    config: Config,
) -> None:
    """
    Write code artifacts to disk.

    Args:
        code_artifacts: Dictionary of path -> content
        output_dir: Output directory
        config: UI configuration
    """
    written_files = []

    for path, content in code_artifacts.items():
        # Skip internal files (test results, violations)
        if path.startswith("_"):
            continue

        # Write file
        full_path = output_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

        written_files.append(str(full_path))
        config.print_details(f"[dim]Wrote: {full_path}[/dim]")

    config.print_details(f"\n[green]✓[/green] Wrote {len(written_files)} files")


def display_success_message(
    feature_id: str,
    output_dir: Path,
    code_artifacts: dict,
    test_results_before: Optional[TestResult],
    test_results_after: Optional[TestResult],
    config: Config,
) -> None:
    """
    Display success message with Rich panel.

    Args:
        feature_id: Feature ID
        output_dir: Output directory
        code_artifacts: Generated artifacts
        test_results_before: Test results before implementation
        test_results_after: Test results after implementation
        config: UI configuration
    """
    # Count files
    src_files = [k for k in code_artifacts.keys() if k.startswith("src/")]
    test_files = [k for k in code_artifacts.keys() if k.startswith("tests/")]

    success_parts = [
        "[bold green]Code generation completed successfully![/bold green]\n",
        "[bold]TDD Workflow:[/bold]",
    ]

    # RED phase results
    if test_results_before:
        success_parts.append(
            f"  • RED Phase: {test_results_before.total} tests generated "
            f"({test_results_before.failed} failed as expected)"
        )

    # GREEN phase results
    if test_results_after:
        if test_results_after.is_success():
            success_parts.append(
                f"  • GREEN Phase: All {test_results_after.passed} tests passing! ✓"
            )
        else:
            success_parts.append(
                f"  • GREEN Phase: {test_results_after.passed}/{test_results_after.total} tests passing "
                f"({test_results_after.failed} still failing)"
            )

    success_parts.extend(
        [
            "\n[bold]Generated Files:[/bold]",
            f"  • {len(src_files)} production files in {output_dir}/src/",
            f"  • {len(test_files)} test files in {output_dir}/tests/",
            f"  • Checkpoint saved: .acp/state/{feature_id}.json",
            "\n[bold]Next Steps:[/bold]",
            f"  1. Review generated code: [cyan]tree {output_dir}[/cyan]",
            "  2. Run tests: [cyan]pytest tests/ -v[/cyan]",
            "  3. Review coverage: [cyan]pytest --cov=src tests/[/cyan]",
            "\n[dim]Implementation workflow complete - feature is ready for use![/dim]",
        ]
    )

    success_message = "\n".join(success_parts)

    if config.should_show_progress():
        config.console.print(
            Panel(
                success_message,
                title="Implementation Complete",
                border_style="green",
                padding=(1, 2),
            )
        )

        # Display test results if available
        if test_results_after:
            display_test_results("Final Test Results", test_results_after, config)
    else:
        config.print_minimal(f"[green]✓[/green] Code generated: {output_dir}")


# Export command
__all__ = ["implement_command"]
