"""
acpctl Rich Terminal UI Components

Provides Rich Console configuration and UI utilities for acpctl CLI.
Implements progressive disclosure with three verbosity levels.

Usage:
    >>> from acpctl.cli.ui import get_console, Config, ConsoleLevel
    >>> config = Config.get_instance()
    >>> config.set_level(ConsoleLevel.VERBOSE)
    >>> console = get_console()
    >>> console.print("Processing...")
"""

from rich.console import Console

from acpctl.cli.ui.config import Config, ConsoleLevel

__all__ = ["Config", "ConsoleLevel", "get_console"]


def get_console() -> Console:
    """
    Get the global Rich Console instance.

    Returns:
        Console: Rich Console instance configured by Config singleton

    Example:
        >>> console = get_console()
        >>> console.print("[green]Success![/green]")
    """
    config = Config.get_instance()
    return config.console
