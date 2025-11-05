"""
acpctl Error Messages and Utilities

Provides comprehensive, user-friendly error messages with actionable suggestions.
Centralizes error handling patterns for consistent UX across all commands.

Reference: T079 - Phase 8 implementation
"""

from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel


# ============================================================
# ERROR MESSAGE TEMPLATES
# ============================================================


class ErrorMessages:
    """
    Centralized error messages with actionable suggestions.

    All error messages follow the pattern:
    1. Clear problem statement
    2. Context (what was being attempted)
    3. Suggested fix (actionable next steps)
    """

    @staticmethod
    def constitution_not_found(acp_dir: str = ".acp") -> str:
        """Error when constitution file is missing."""
        return f"""[bold red]Constitution file not found[/bold red]

[bold]Problem:[/bold]
  The constitutional governance file is missing at:
  {Path(acp_dir).resolve()}/templates/constitution.md

[bold]Solution:[/bold]
  Run [cyan]acpctl init[/cyan] to initialize the project with constitutional governance.

[bold]What this does:[/bold]
  Creates .acp/ directory structure and constitutional template
  with example principles for your project."""

    @staticmethod
    def checkpoint_not_found(feature_id: Optional[str] = None) -> str:
        """Error when checkpoint file is missing."""
        if feature_id:
            msg = f"[bold red]Checkpoint not found for feature: {feature_id}[/bold red]"
        else:
            msg = "[bold red]No checkpoint found[/bold red]"

        return f"""{msg}

[bold]Problem:[/bold]
  No workflow checkpoint exists to resume from.

[bold]Solution:[/bold]
  - Run [cyan]acpctl history[/cyan] to see available workflows
  - Run [cyan]acpctl specify "your feature"[/cyan] to start a new workflow

[bold]What checkpoints do:[/bold]
  Checkpoints save workflow progress after each phase,
  allowing you to resume from any interruption point."""

    @staticmethod
    def specification_missing() -> str:
        """Error when specification is required but missing."""
        return """[bold red]Specification not found[/bold red]

[bold]Problem:[/bold]
  The current workflow phase requires a completed specification,
  but no specification has been generated yet.

[bold]Solution:[/bold]
  Run [cyan]acpctl specify "your feature description"[/cyan] to generate specification.

[bold]Workflow phases:[/bold]
  init → [cyan]specify[/cyan] → plan → implement → complete"""

    @staticmethod
    def plan_missing() -> str:
        """Error when plan is required but missing."""
        return """[bold red]Implementation plan not found[/bold red]

[bold]Problem:[/bold]
  The current workflow phase requires a completed implementation plan,
  but no plan has been generated yet.

[bold]Solution:[/bold]
  Run [cyan]acpctl plan[/cyan] to generate implementation plan.

[bold]Workflow phases:[/bold]
  init → specify → [cyan]plan[/cyan] → implement → complete"""

    @staticmethod
    def invalid_phase_transition(current: str, target: str, allowed: List[str]) -> str:
        """Error when phase transition is invalid."""
        allowed_str = ", ".join(allowed) if allowed else "none (terminal phase)"

        return f"""[bold red]Invalid workflow transition[/bold red]

[bold]Problem:[/bold]
  Cannot transition from phase '{current}' to '{target}'

[bold]Current phase:[/bold] {current}
[bold]Requested phase:[/bold] {target}
[bold]Allowed next phases:[/bold] {allowed_str}

[bold]Solution:[/bold]
  Run [cyan]acpctl status[/cyan] to see current workflow state
  and available next steps."""

    @staticmethod
    def governance_failed(violation_count: int) -> str:
        """Error when governance validation fails."""
        return f"""[bold red]Constitutional governance validation failed[/bold red]

[bold]Problem:[/bold]
  {violation_count} constitutional principle violation{'s' if violation_count != 1 else ''} detected

[bold]What this means:[/bold]
  The generated artifact conflicts with your project's
  constitutional principles defined in .acp/templates/constitution.md

[bold]Options:[/bold]
  [R] [cyan]Regenerate[/cyan] - Try generating the artifact again
  [E] [cyan]Edit[/cyan] - Modify the constitution principles
  [A] [cyan]Abort[/cyan] - Stop the workflow
  [I] [cyan]Ignore[/cyan] - Continue anyway (--force)"""

    @staticmethod
    def llm_error(operation: str, error: str) -> str:
        """Error when LLM call fails."""
        return f"""[bold red]LLM operation failed[/bold red]

[bold]Problem:[/bold]
  Failed during: {operation}

[bold]Error details:[/bold]
  {error}

[bold]Common causes:[/bold]
  • API key not configured (check OPENAI_API_KEY environment variable)
  • Rate limit exceeded (wait a moment and try again)
  • Network connectivity issues
  • Model unavailable

[bold]Solution:[/bold]
  1. Check your API credentials are configured
  2. Verify network connectivity
  3. Try again in a few moments
  4. If problem persists, check LLM provider status"""

    @staticmethod
    def file_write_error(filepath: str, error: str) -> str:
        """Error when file write operation fails."""
        return f"""[bold red]File write failed[/bold red]

[bold]Problem:[/bold]
  Cannot write to file: {filepath}

[bold]Error details:[/bold]
  {error}

[bold]Common causes:[/bold]
  • Insufficient permissions
  • Directory doesn't exist
  • Disk full
  • File in use by another process

[bold]Solution:[/bold]
  1. Check file permissions: ls -l {Path(filepath).parent}
  2. Verify directory exists
  3. Check disk space: df -h
  4. Ensure file is not locked by another process"""

    @staticmethod
    def checkpoint_corrupted(filepath: str, error: str) -> str:
        """Error when checkpoint file is corrupted."""
        return f"""[bold red]Checkpoint file corrupted[/bold red]

[bold]Problem:[/bold]
  Cannot load checkpoint from: {filepath}

[bold]Error details:[/bold]
  {error}

[bold]What this means:[/bold]
  The checkpoint file is malformed or incomplete,
  and cannot be safely loaded.

[bold]Solution:[/bold]
  1. Check the checkpoint file is valid JSON
  2. Look for backup checkpoints: ls -la .acp/state/
  3. If no backup exists, start a new workflow:
     [cyan]acpctl specify "your feature"[/cyan]"""

    @staticmethod
    def feature_id_conflict(feature_id: str) -> str:
        """Error when feature ID already exists."""
        return f"""[bold red]Feature ID conflict[/bold red]

[bold]Problem:[/bold]
  Feature ID '{feature_id}' already exists

[bold]What this means:[/bold]
  A workflow with this feature ID is already in progress
  or has been completed.

[bold]Solution:[/bold]
  1. Resume existing workflow: [cyan]acpctl resume {feature_id}[/cyan]
  2. View workflow status: [cyan]acpctl status[/cyan]
  3. Use a different feature ID
  4. If you want to replace it, delete the old checkpoint:
     rm .acp/state/{feature_id}.json"""

    @staticmethod
    def max_retries_exceeded(operation: str, retry_count: int) -> str:
        """Error when max retry attempts exceeded."""
        return f"""[bold red]Maximum retry attempts exceeded[/bold red]

[bold]Problem:[/bold]
  Operation '{operation}' failed after {retry_count} attempts

[bold]What this means:[/bold]
  The operation was retried multiple times but continued
  to fail, indicating a persistent issue.

[bold]Solution:[/bold]
  1. Review error details above
  2. Check if the issue is with:
     • Constitutional principles (too strict?)
     • Input requirements (missing information?)
     • System resources (API limits?)
  3. Try modifying your approach or input
  4. If problem persists, use --force to bypass validation"""


# ============================================================
# ERROR DISPLAY HELPERS
# ============================================================


def display_error(message: str, console: Optional[Console] = None) -> None:
    """
    Display error message in Rich panel.

    Args:
        message: Error message (can include Rich markup)
        console: Optional Rich console (creates new if None)

    Example:
        >>> display_error(ErrorMessages.constitution_not_found())
    """
    if console is None:
        console = Console()

    console.print(
        Panel(
            message,
            title="Error",
            border_style="red",
            padding=(1, 2),
        )
    )


def display_warning(message: str, console: Optional[Console] = None) -> None:
    """
    Display warning message in Rich panel.

    Args:
        message: Warning message (can include Rich markup)
        console: Optional Rich console (creates new if None)

    Example:
        >>> display_warning("Using default configuration...")
    """
    if console is None:
        console = Console()

    console.print(
        Panel(
            message,
            title="Warning",
            border_style="yellow",
            padding=(1, 2),
        )
    )


# ============================================================
# EXCEPTION CLASSES WITH MESSAGES
# ============================================================


class ACPError(Exception):
    """Base exception for acpctl errors."""

    def __init__(self, message: str, suggested_fix: Optional[str] = None):
        """
        Initialize acpctl error.

        Args:
            message: Error message
            suggested_fix: Optional suggested fix
        """
        self.message = message
        self.suggested_fix = suggested_fix
        super().__init__(message)


class ConstitutionNotFoundError(ACPError):
    """Raised when constitution file is not found."""

    def __init__(self, acp_dir: str = ".acp"):
        message = f"Constitution file not found at {acp_dir}/templates/constitution.md"
        suggested_fix = "Run 'acpctl init' to initialize the project"
        super().__init__(message, suggested_fix)


class CheckpointNotFoundError(ACPError):
    """Raised when checkpoint file is not found."""

    def __init__(self, feature_id: Optional[str] = None):
        if feature_id:
            message = f"Checkpoint not found for feature: {feature_id}"
        else:
            message = "No checkpoint found"
        suggested_fix = "Run 'acpctl history' to see available workflows"
        super().__init__(message, suggested_fix)


class InvalidPhaseTransitionError(ACPError):
    """Raised when phase transition is invalid."""

    def __init__(self, current: str, target: str, allowed: List[str]):
        message = f"Cannot transition from '{current}' to '{target}'"
        allowed_str = ", ".join(allowed) if allowed else "none"
        suggested_fix = f"Allowed next phases: {allowed_str}"
        super().__init__(message, suggested_fix)


class GovernanceValidationError(ACPError):
    """Raised when governance validation fails."""

    def __init__(self, violation_count: int):
        message = f"{violation_count} constitutional violations detected"
        suggested_fix = "Choose [R]egenerate, [E]dit, [A]bort, or [I]gnore"
        super().__init__(message, suggested_fix)
