"""
acpctl Logging Configuration

Provides structured logging with JSON output support for acpctl.
Manages log levels, handlers, and formatting for both development and production.

Logging Architecture:
- Structured logging with contextual information
- JSON format option for machine parsing
- File and console handlers
- Integration with Rich console for formatted output

Reference: plan.md (Utilities section)
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.logging import RichHandler

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

# Default log directory
DEFAULT_LOG_DIR = ".acp/logs"

# Log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


# ============================================================
# STRUCTURED LOG FORMATTER
# ============================================================


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs log records as JSON for machine parsing and analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable formatter for console output.

    Formats log records with timestamps and color coding (via Rich).
    """

    def __init__(self):
        """Initialize formatter with timestamp format."""
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


# ============================================================
# LOGGER SETUP
# ============================================================


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    console_output: bool = True,
    rich_console: Optional[Console] = None,
) -> logging.Logger:
    """
    Setup logging configuration for acpctl.

    Args:
        level: Log level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        log_file: Optional log file path (relative to log directory)
        json_format: If True, use JSON formatting for file output
        console_output: If True, output to console
        rich_console: Optional Rich Console for formatted output

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(level="DEBUG", log_file="acpctl.log")
        >>> logger.info("Starting workflow")
    """
    # Get root logger
    logger = logging.getLogger("acpctl")
    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with Rich
    if console_output:
        if rich_console is None:
            rich_console = Console(stderr=True)

        console_handler = RichHandler(
            console=rich_console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        console_handler.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_dir = Path(DEFAULT_LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

        log_path = log_dir / log_file

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file

        if json_format:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(HumanReadableFormatter())

        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = "acpctl") -> logging.Logger:
    """
    Get logger instance for module.

    Args:
        name: Logger name (typically module name)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing specification")
    """
    return logging.getLogger(name)


# ============================================================
# CONTEXTUAL LOGGING
# ============================================================


class LogContext:
    """
    Context manager for adding contextual information to logs.

    Adds extra fields to all log records within the context.

    Example:
        >>> with LogContext(logger, feature_id="001-oauth2", phase="specify"):
        ...     logger.info("Generating specification")
        ...     # Log includes feature_id and phase fields
    """

    def __init__(self, logger: logging.Logger, **context: Any):
        """
        Initialize log context.

        Args:
            logger: Logger to add context to
            **context: Context fields to add to all log records
        """
        self.logger = logger
        self.context = context
        self.original_handlers = []

    def __enter__(self) -> logging.Logger:
        """Enter context and add contextual logging."""
        # Store original handlers
        self.original_handlers = self.logger.handlers.copy()

        # Wrap handlers to add context
        for handler in self.logger.handlers:
            original_emit = handler.emit

            def emit_with_context(record: logging.LogRecord) -> None:
                # Add context to record
                record.extra = getattr(record, "extra", {})
                record.extra.update(self.context)
                original_emit(record)

            handler.emit = emit_with_context

        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore original handlers."""
        # Restore original handlers
        self.logger.handlers = self.original_handlers


# ============================================================
# WORKFLOW LOGGING
# ============================================================


def log_workflow_event(
    logger: logging.Logger,
    event_type: str,
    phase: str,
    feature_id: Optional[str] = None,
    **extra: Any,
) -> None:
    """
    Log workflow event with structured data.

    Args:
        logger: Logger instance
        event_type: Event type ("phase_start", "phase_complete", "error", etc.)
        phase: Current workflow phase
        feature_id: Optional feature identifier
        **extra: Additional event data

    Example:
        >>> log_workflow_event(
        ...     logger,
        ...     "phase_start",
        ...     "specify",
        ...     feature_id="001-oauth2"
        ... )
    """
    event_data = {
        "event_type": event_type,
        "phase": phase,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if feature_id:
        event_data["feature_id"] = feature_id

    event_data.update(extra)

    logger.info(f"Workflow event: {event_type}", extra={"event": event_data})


def log_agent_execution(
    logger: logging.Logger,
    agent_name: str,
    agent_type: str,
    action: str,
    **extra: Any,
) -> None:
    """
    Log agent execution event.

    Args:
        logger: Logger instance
        agent_name: Human-readable agent name
        agent_type: Agent type identifier
        action: Action performed ("start", "complete", "error")
        **extra: Additional event data

    Example:
        >>> log_agent_execution(
        ...     logger,
        ...     "Specification Agent",
        ...     "specification",
        ...     "start"
        ... )
    """
    event_data = {
        "agent_name": agent_name,
        "agent_type": agent_type,
        "action": action,
        "timestamp": datetime.utcnow().isoformat(),
    }

    event_data.update(extra)

    logger.info(f"Agent {action}: {agent_name}", extra={"agent": event_data})


def log_checkpoint_event(
    logger: logging.Logger,
    action: str,
    feature_id: str,
    thread_id: str,
    phase: str,
    **extra: Any,
) -> None:
    """
    Log checkpoint save/load event.

    Args:
        logger: Logger instance
        action: Action performed ("save", "load")
        feature_id: Feature identifier
        thread_id: Thread ID
        phase: Current phase
        **extra: Additional event data

    Example:
        >>> log_checkpoint_event(
        ...     logger,
        ...     "save",
        ...     "001-oauth2",
        ...     "thread_abc123",
        ...     "specify"
        ... )
    """
    event_data = {
        "action": action,
        "feature_id": feature_id,
        "thread_id": thread_id,
        "phase": phase,
        "timestamp": datetime.utcnow().isoformat(),
    }

    event_data.update(extra)

    logger.info(
        f"Checkpoint {action}: {feature_id} (phase: {phase})",
        extra={"checkpoint": event_data},
    )


# ============================================================
# LOG ROTATION
# ============================================================


def setup_rotating_file_handler(
    logger: logging.Logger,
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    json_format: bool = False,
) -> None:
    """
    Add rotating file handler to logger.

    Args:
        logger: Logger instance
        log_file: Log file name
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        json_format: If True, use JSON formatting

    Example:
        >>> logger = get_logger()
        >>> setup_rotating_file_handler(logger, "acpctl.log")
    """
    from logging.handlers import RotatingFileHandler

    log_dir = Path(DEFAULT_LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / log_file

    handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    handler.setLevel(logging.DEBUG)

    if json_format:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(HumanReadableFormatter())

    logger.addHandler(handler)


# ============================================================
# INITIALIZATION
# ============================================================


def init_logging(
    level: str = "INFO",
    log_file: Optional[str] = "acpctl.log",
    json_format: bool = False,
) -> logging.Logger:
    """
    Initialize logging for acpctl application.

    Convenience function that sets up logging with sensible defaults.

    Args:
        level: Log level
        log_file: Log file name (None to disable file logging)
        json_format: If True, use JSON formatting for file output

    Returns:
        Configured logger instance

    Example:
        >>> logger = init_logging(level="DEBUG")
        >>> logger.info("acpctl initialized")
    """
    return setup_logging(
        level=level,
        log_file=log_file,
        json_format=json_format,
        console_output=True,
    )
