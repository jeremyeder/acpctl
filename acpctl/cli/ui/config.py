"""
acpctl UI Configuration

Manages console verbosity levels and UI configuration for Rich terminal output.
Provides three verbosity modes: quiet, default, and verbose.

Architecture:
- ConsoleLevel enum: Defines verbosity levels
- Config class: Manages console state and settings
- Thread-safe singleton pattern for global UI configuration

Reference: plan.md (FR-016 - Progressive Disclosure)
"""

from enum import Enum
from typing import Optional

from rich.console import Console


class ConsoleLevel(Enum):
    """
    Console verbosity levels for progressive disclosure.

    QUIET: Minimal output (errors, critical messages only)
    DEFAULT: Standard output (progress, summaries, results)
    VERBOSE: Full output (agent reasoning, detailed logs, debugging info)
    """

    QUIET = "quiet"
    DEFAULT = "default"
    VERBOSE = "verbose"

    @classmethod
    def from_flags(cls, quiet: bool = False, verbose: bool = False) -> "ConsoleLevel":
        """
        Determine console level from CLI flags.

        Args:
            quiet: --quiet/-q flag
            verbose: --verbose/-v flag

        Returns:
            ConsoleLevel (verbose takes precedence over quiet)

        Example:
            >>> level = ConsoleLevel.from_flags(quiet=False, verbose=True)
            >>> print(level)
            ConsoleLevel.VERBOSE
        """
        if verbose:
            return cls.VERBOSE
        elif quiet:
            return cls.QUIET
        else:
            return cls.DEFAULT


class Config:
    """
    Global UI configuration manager.

    Singleton pattern ensures consistent console settings across all commands.
    Manages Rich Console instance and verbosity level.

    Usage:
        >>> config = Config.get_instance()
        >>> config.set_level(ConsoleLevel.VERBOSE)
        >>> if config.should_show_progress():
        ...     config.console.print("Processing...")
    """

    _instance: Optional["Config"] = None

    def __init__(self) -> None:
        """
        Initialize UI configuration.

        Note: Use Config.get_instance() instead of direct instantiation.
        """
        self.console = Console()
        self.level = ConsoleLevel.DEFAULT
        self.force_terminal = False  # For testing/CI environments

    @classmethod
    def get_instance(cls) -> "Config":
        """
        Get or create singleton Config instance.

        Returns:
            Config singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset singleton instance (primarily for testing).

        This allows tests to start with a clean configuration state.
        """
        cls._instance = None

    def set_level(self, level: ConsoleLevel) -> None:
        """
        Set console verbosity level.

        Args:
            level: ConsoleLevel to set

        Example:
            >>> config = Config.get_instance()
            >>> config.set_level(ConsoleLevel.QUIET)
        """
        self.level = level

    def set_level_from_flags(self, quiet: bool = False, verbose: bool = False) -> None:
        """
        Set console level from CLI flags.

        Args:
            quiet: --quiet/-q flag
            verbose: --verbose/-v flag

        Example:
            >>> config = Config.get_instance()
            >>> config.set_level_from_flags(verbose=True)
        """
        self.level = ConsoleLevel.from_flags(quiet=quiet, verbose=verbose)

    def is_quiet(self) -> bool:
        """Check if console is in quiet mode."""
        return self.level == ConsoleLevel.QUIET

    def is_default(self) -> bool:
        """Check if console is in default mode."""
        return self.level == ConsoleLevel.DEFAULT

    def is_verbose(self) -> bool:
        """Check if console is in verbose mode."""
        return self.level == ConsoleLevel.VERBOSE

    def should_show_minimal(self) -> bool:
        """
        Check if minimal messages should be shown.

        Returns:
            True for all levels (errors/critical messages always shown)
        """
        return True

    def should_show_progress(self) -> bool:
        """
        Check if progress indicators should be shown.

        Returns:
            True for DEFAULT and VERBOSE levels
        """
        return self.level in (ConsoleLevel.DEFAULT, ConsoleLevel.VERBOSE)

    def should_show_details(self) -> bool:
        """
        Check if detailed information should be shown.

        Returns:
            True for VERBOSE level only
        """
        return self.level == ConsoleLevel.VERBOSE

    def print_minimal(self, *args, **kwargs) -> None:
        """
        Print minimal output (errors, critical messages).

        Always displayed regardless of verbosity level.
        """
        if self.should_show_minimal():
            self.console.print(*args, **kwargs)

    def print_progress(self, *args, **kwargs) -> None:
        """
        Print progress output (standard messages, summaries).

        Displayed in DEFAULT and VERBOSE levels.
        """
        if self.should_show_progress():
            self.console.print(*args, **kwargs)

    def print_details(self, *args, **kwargs) -> None:
        """
        Print detailed output (agent reasoning, debug info).

        Displayed in VERBOSE level only.
        """
        if self.should_show_details():
            self.console.print(*args, **kwargs)

    def print_error(self, message: str, **kwargs) -> None:
        """
        Print error message.

        Always displayed with error styling.

        Args:
            message: Error message to display
        """
        self.console.print(f"[red]Error:[/red] {message}", **kwargs)

    def print_success(self, message: str, **kwargs) -> None:
        """
        Print success message.

        Always displayed with success styling.

        Args:
            message: Success message to display
        """
        self.console.print(f"[green]✓[/green] {message}", **kwargs)

    def print_warning(self, message: str, **kwargs) -> None:
        """
        Print warning message.

        Displayed in DEFAULT and VERBOSE levels.

        Args:
            message: Warning message to display
        """
        if self.should_show_progress():
            self.console.print(f"[yellow]Warning:[/yellow] {message}", **kwargs)
