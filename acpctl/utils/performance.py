"""
acpctl Performance Utilities

Provides timing, profiling, and performance monitoring utilities.
Helps ensure performance targets are met across all commands.

Performance Targets (from spec):
- acpctl init: < 10 seconds (SC-001)
- acpctl specify: < 10 minutes (SC-002)
- Full workflow: < 30 minutes (SC-006)

Reference: T084 - Phase 8 implementation
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

from acpctl.utils.logging import get_logger

logger = get_logger(__name__)


# ============================================================
# TIMING CONTEXT MANAGER
# ============================================================


@contextmanager
def timed_operation(operation_name: str, log_result: bool = True):
    """
    Context manager for timing operations.

    Args:
        operation_name: Name of operation being timed
        log_result: If True, log timing result

    Yields:
        Timer object with elapsed() method

    Example:
        >>> with timed_operation("LLM call") as timer:
        ...     result = llm.invoke(prompt)
        ...     print(f"Took {timer.elapsed():.2f}s")
    """

    class Timer:
        def __init__(self):
            self.start_time = time.time()

        def elapsed(self) -> float:
            """Get elapsed time in seconds."""
            return time.time() - self.start_time

    timer = Timer()

    try:
        yield timer
    finally:
        duration = timer.elapsed()
        if log_result:
            logger.info(f"{operation_name} completed in {duration:.2f}s")


# ============================================================
# TIMING DECORATOR
# ============================================================


def timed(operation_name: Optional[str] = None):
    """
    Decorator for timing function execution.

    Args:
        operation_name: Optional name (defaults to function name)

    Returns:
        Decorated function

    Example:
        >>> @timed("Checkpoint save")
        ... def save_checkpoint(state):
        ...     # ... save logic ...
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            name = operation_name or func.__name__
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{name} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{name} failed after {duration:.2f}s: {e}")
                raise

        return wrapper

    return decorator


# ============================================================
# PERFORMANCE TRACKING
# ============================================================


class PerformanceTracker:
    """
    Tracks performance metrics for workflow operations.

    Collects timing data and helps identify bottlenecks.
    """

    def __init__(self):
        """Initialize performance tracker."""
        self.operations: dict[str, list[float]] = {}
        self.start_times: dict[str, float] = {}

    def start(self, operation_name: str) -> None:
        """
        Start timing an operation.

        Args:
            operation_name: Name of operation

        Example:
            >>> tracker = PerformanceTracker()
            >>> tracker.start("LLM call")
            >>> # ... do work ...
            >>> tracker.end("LLM call")
        """
        self.start_times[operation_name] = time.time()

    def end(self, operation_name: str) -> float:
        """
        End timing an operation and record duration.

        Args:
            operation_name: Name of operation

        Returns:
            Duration in seconds

        Raises:
            KeyError: If operation was not started
        """
        if operation_name not in self.start_times:
            raise KeyError(f"Operation '{operation_name}' was not started")

        duration = time.time() - self.start_times[operation_name]
        del self.start_times[operation_name]

        if operation_name not in self.operations:
            self.operations[operation_name] = []

        self.operations[operation_name].append(duration)

        return duration

    @contextmanager
    def track(self, operation_name: str):
        """
        Context manager for tracking operation.

        Args:
            operation_name: Name of operation

        Yields:
            None

        Example:
            >>> tracker = PerformanceTracker()
            >>> with tracker.track("LLM call"):
            ...     result = llm.invoke(prompt)
        """
        self.start(operation_name)
        try:
            yield
        finally:
            self.end(operation_name)

    def get_stats(self, operation_name: str) -> dict[str, float]:
        """
        Get statistics for an operation.

        Args:
            operation_name: Name of operation

        Returns:
            Dictionary with min, max, avg, total, count

        Example:
            >>> stats = tracker.get_stats("LLM call")
            >>> print(f"Average: {stats['avg']:.2f}s")
        """
        if operation_name not in self.operations:
            return {}

        durations = self.operations[operation_name]

        return {
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / len(durations),
            "total": sum(durations),
            "count": len(durations),
        }

    def get_all_stats(self) -> dict[str, dict[str, float]]:
        """
        Get statistics for all tracked operations.

        Returns:
            Dictionary mapping operation names to stats

        Example:
            >>> all_stats = tracker.get_all_stats()
            >>> for op, stats in all_stats.items():
            ...     print(f"{op}: {stats['avg']:.2f}s avg")
        """
        return {op: self.get_stats(op) for op in self.operations.keys()}

    def reset(self) -> None:
        """Reset all tracked operations."""
        self.operations.clear()
        self.start_times.clear()

    def log_summary(self) -> None:
        """Log summary of all tracked operations."""
        if not self.operations:
            logger.info("No performance data tracked")
            return

        logger.info("Performance Summary:")
        for operation_name, stats in self.get_all_stats().items():
            logger.info(
                f"  {operation_name}: "
                f"avg={stats['avg']:.2f}s, "
                f"min={stats['min']:.2f}s, "
                f"max={stats['max']:.2f}s, "
                f"count={stats['count']}"
            )


# ============================================================
# PERFORMANCE VALIDATION
# ============================================================


def check_performance_target(
    operation_name: str, duration: float, target: float, warn_percentage: float = 0.8
) -> bool:
    """
    Check if operation met performance target.

    Args:
        operation_name: Name of operation
        duration: Actual duration in seconds
        target: Target duration in seconds
        warn_percentage: Warn if duration exceeds this percentage of target

    Returns:
        True if target met, False otherwise

    Example:
        >>> duration = 8.5
        >>> target_met = check_performance_target("init", duration, 10.0)
        >>> # Logs warning if duration > 8.0s, returns False if > 10.0s
    """
    if duration > target:
        logger.warning(
            f"{operation_name} exceeded performance target: "
            f"{duration:.2f}s > {target:.2f}s target"
        )
        return False

    if duration > target * warn_percentage:
        logger.warning(
            f"{operation_name} approaching performance target: "
            f"{duration:.2f}s (target: {target:.2f}s)"
        )

    return True


# ============================================================
# LAZY LOADING HELPER
# ============================================================


class LazyLoader:
    """
    Lazy loader for expensive imports/initializations.

    Defers loading until first use to improve startup time.
    """

    def __init__(self, loader_func: Callable[[], Any]):
        """
        Initialize lazy loader.

        Args:
            loader_func: Function that performs the expensive loading
        """
        self._loader_func = loader_func
        self._loaded_value: Optional[Any] = None
        self._is_loaded = False

    def get(self) -> Any:
        """
        Get the loaded value, loading if necessary.

        Returns:
            Loaded value

        Example:
            >>> expensive_import = LazyLoader(lambda: import_large_module())
            >>> # Module not loaded yet
            >>> module = expensive_import.get()  # Loaded on first access
            >>> module2 = expensive_import.get()  # Returns cached value
        """
        if not self._is_loaded:
            with timed_operation(f"Lazy load: {self._loader_func.__name__}"):
                self._loaded_value = self._loader_func()
                self._is_loaded = True

        return self._loaded_value

    def is_loaded(self) -> bool:
        """Check if value has been loaded."""
        return self._is_loaded


# ============================================================
# GLOBAL PERFORMANCE TRACKER
# ============================================================

# Global tracker instance for workflow-level performance monitoring
_global_tracker: Optional[PerformanceTracker] = None


def get_global_tracker() -> PerformanceTracker:
    """
    Get global performance tracker instance.

    Returns:
        Global PerformanceTracker

    Example:
        >>> tracker = get_global_tracker()
        >>> with tracker.track("overall_workflow"):
        ...     # ... workflow execution ...
        ...     pass
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = PerformanceTracker()
    return _global_tracker


def reset_global_tracker() -> None:
    """Reset global performance tracker."""
    global _global_tracker
    if _global_tracker:
        _global_tracker.reset()
