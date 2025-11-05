"""
acpctl Schema Validation Helpers

Provides validation utilities for ACPState, checkpoints, and CLI metadata.
These helpers ensure data integrity at key boundaries in the workflow.

Architecture:
- Validates state against Pydantic models
- Sanitizes state for JSON serialization
- Provides helpful error messages for validation failures

Reference: T076 - Phase 8 implementation
"""

from typing import Any, Dict, Optional, Tuple

from pydantic import ValidationError

from acpctl.core.checkpoint import CheckpointData, CLIMetadata
from acpctl.core.state import ACPState, ACPStateModel


# ============================================================
# SCHEMA VERSION
# ============================================================


def get_schema_version() -> str:
    """
    Get current schema version for checkpoints.

    Returns:
        Schema version string (e.g., "1.0.0")

    Example:
        >>> version = get_schema_version()
        >>> print(version)
        '1.0.0'
    """
    return "1.0.0"


# ============================================================
# STATE VALIDATION
# ============================================================


def validate_state_schema(state: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate ACPState dictionary against Pydantic schema.

    Args:
        state: State dictionary to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Example:
        >>> state = {'phase': 'init', 'constitution': '', ...}
        >>> valid, error = validate_state_schema(state)
        >>> if not valid:
        ...     print(f"State invalid: {error}")
    """
    try:
        ACPStateModel(**state)
        return True, None
    except ValidationError as e:
        error_msg = _format_validation_error(e, "State")
        return False, error_msg
    except Exception as e:
        return False, f"Unexpected validation error: {str(e)}"


def validate_checkpoint_schema(checkpoint: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate checkpoint dictionary structure.

    Args:
        checkpoint: Checkpoint dictionary to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Example:
        >>> checkpoint = {'metadata': {...}, 'state': {...}}
        >>> valid, error = validate_checkpoint_schema(checkpoint)
        >>> if not valid:
        ...     print(f"Checkpoint invalid: {error}")
    """
    try:
        CheckpointData(**checkpoint)
        return True, None
    except ValidationError as e:
        error_msg = _format_validation_error(e, "Checkpoint")
        return False, error_msg
    except Exception as e:
        return False, f"Unexpected validation error: {str(e)}"


def validate_cli_metadata(metadata: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate CLI metadata structure.

    Args:
        metadata: CLI metadata dictionary to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Example:
        >>> metadata = {'feature_id': '001', 'thread_id': 'abc', ...}
        >>> valid, error = validate_cli_metadata(metadata)
        >>> if not valid:
        ...     print(f"Metadata invalid: {error}")
    """
    try:
        CLIMetadata(**metadata)
        return True, None
    except ValidationError as e:
        error_msg = _format_validation_error(e, "CLI Metadata")
        return False, error_msg
    except Exception as e:
        return False, f"Unexpected validation error: {str(e)}"


# ============================================================
# STATE SANITIZATION
# ============================================================


def sanitize_state_for_checkpoint(state: ACPState) -> Dict[str, Any]:
    """
    Sanitize state for checkpoint serialization.

    Removes non-serializable fields and prepares state for JSON export.
    This ensures checkpoints can be safely saved and loaded.

    Args:
        state: ACPState to sanitize

    Returns:
        Sanitized dictionary ready for JSON serialization

    Example:
        >>> state = create_test_state()
        >>> clean_state = sanitize_state_for_checkpoint(state)
        >>> json.dumps(clean_state)  # Should succeed
    """
    # Convert to dict if needed
    if not isinstance(state, dict):
        state = dict(state)

    # Create a copy to avoid mutating original
    sanitized = {}

    for key, value in state.items():
        sanitized[key] = _sanitize_value(value)

    return sanitized


def _sanitize_value(value: Any) -> Any:
    """
    Recursively sanitize a value for JSON serialization.

    Args:
        value: Value to sanitize

    Returns:
        JSON-serializable version of value
    """
    # Handle None, strings, numbers, bools
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    # Handle lists and tuples
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(item) for item in value]

    # Handle dicts
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}

    # Handle other types - convert to string
    # This includes datetime, Path, custom objects
    return str(value)


# ============================================================
# ERROR FORMATTING
# ============================================================


def _format_validation_error(error: ValidationError, context: str) -> str:
    """
    Format Pydantic validation error into user-friendly message.

    Args:
        error: ValidationError from Pydantic
        context: Context string (e.g., "State", "Checkpoint")

    Returns:
        Formatted error message with helpful details

    Example output:
        "State validation failed:
         - phase: Value error, Invalid phase 'invalid'. Must be one of {...}
         - constitution: Field required"
    """
    errors = error.errors()

    if not errors:
        return f"{context} validation failed: Unknown error"

    lines = [f"{context} validation failed:"]

    for err in errors:
        # Get field path (e.g., ['state', 'phase'] -> 'state.phase')
        field_path = ".".join(str(loc) for loc in err.get("loc", []))

        # Get error type and message
        error_type = err.get("type", "error")
        error_msg = err.get("msg", "Unknown error")

        # Format as bullet point
        lines.append(f"  - {field_path}: {error_msg}")

    return "\n".join(lines)


# ============================================================
# VALIDATION HELPERS FOR WORKFLOW PHASES
# ============================================================


def validate_phase_requirements(state: ACPState, phase: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that state meets requirements for a given phase.

    Args:
        state: Current state
        phase: Target phase to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Example:
        >>> valid, error = validate_phase_requirements(state, 'specify')
        >>> if not valid:
        ...     print(f"Cannot enter specify phase: {error}")
    """
    # Phase-specific validation rules
    if phase == "specify":
        if not state.get("constitution"):
            return False, "Specification phase requires constitution from init phase"
        if not state.get("governance_passes"):
            return False, "Specification phase requires governance validation"

    elif phase == "plan":
        if not state.get("spec"):
            return False, "Planning phase requires completed specification"
        if not state.get("feature_description"):
            return False, "Planning phase requires feature description"

    elif phase == "implement":
        if not state.get("plan"):
            return False, "Implementation phase requires completed plan"
        if not state.get("data_model"):
            return False, "Implementation phase requires data model"

    elif phase == "complete":
        tasks = state.get("tasks", [])
        completed = state.get("completed_tasks", [])
        if len(tasks) == 0:
            return False, "Cannot complete workflow: no tasks defined"
        if len(completed) != len(tasks):
            remaining = len(tasks) - len(completed)
            return False, f"Cannot complete workflow: {remaining} tasks remaining"

    return True, None


def validate_state_transition(
    current_phase: str, target_phase: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate that phase transition is allowed.

    Args:
        current_phase: Current workflow phase
        target_phase: Target workflow phase

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Example:
        >>> valid, error = validate_state_transition('init', 'specify')
        >>> if valid:
        ...     # Proceed with transition
    """
    # Define valid phase transitions
    valid_transitions = {
        "init": ["specify"],
        "specify": ["plan"],
        "plan": ["implement"],
        "implement": ["complete"],
        "complete": [],  # Terminal phase
    }

    # Check if transition is allowed
    if current_phase not in valid_transitions:
        return False, f"Invalid current phase: {current_phase}"

    allowed_next = valid_transitions[current_phase]

    if target_phase not in allowed_next:
        return (
            False,
            f"Cannot transition from '{current_phase}' to '{target_phase}'. "
            f"Allowed transitions: {allowed_next}",
        )

    return True, None
