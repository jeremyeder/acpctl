"""
acpctl Checkpoint Management

Handles saving and loading workflow state checkpoints with schema versioning.
Implements JSON-based persistence for workflow state and CLI metadata.

Architecture:
- Workflow checkpoints: .acp/state/NNN-feature.json (includes ACPState + metadata)
- Schema versioning: Supports migration between versions
- CLI metadata: feature_id, thread_id, status, phases_completed, timestamp

Reference: STATE_IMPLEMENTATION_TEMPLATE.py, PYDANTIC_STATE_RESEARCH.md
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from acpctl.core.state import ACPState, ACPStateModel, typed_dict_to_pydantic


# ============================================================
# CLI METADATA MODELS
# ============================================================


class CLIMetadata(BaseModel):
    """
    CLI-specific metadata for checkpoint management.

    Stored alongside ACPState in checkpoint files to enable
    resume functionality and workflow tracking.
    """

    feature_id: str  # e.g., "001-oauth2-authentication"
    feature_name: str = ""  # Slugified description for display
    thread_id: str  # LangGraph thread ID for workflow continuation
    status: str  # "in_progress", "completed", "failed", "pending"
    phases_completed: List[str] = Field(default_factory=list)  # ["init", "specify"]
    current_phase: str = "init"
    started_at: str = ""  # ISO 8601 timestamp when workflow started
    updated_at: str = ""  # ISO 8601 timestamp of last update
    spec_path: str = ""  # Path to spec directory (e.g., "specs/001-feature")
    checkpoint_version: str = "1.0.0"  # Version of checkpoint format
    acpctl_version: str = "1.0.0"  # Version of acpctl that created checkpoint

    class Config:
        """Pydantic config."""

        extra = "forbid"


class CheckpointData(BaseModel):
    """
    Complete checkpoint file structure.

    Combines workflow state (ACPStateModel) with CLI metadata.
    This is the top-level structure saved to JSON files.
    """

    metadata: CLIMetadata
    state: ACPStateModel

    class Config:
        """Pydantic config."""

        extra = "forbid"


# ============================================================
# CHECKPOINT OPERATIONS
# ============================================================


def save_checkpoint(
    state: ACPState,
    filepath: str,
    feature_id: str,
    thread_id: str,
    status: str = "in_progress",
    phases_completed: Optional[List[str]] = None,
    feature_name: str = "",
    spec_path: str = "",
    started_at: Optional[str] = None,
) -> None:
    """
    Save TypedDict state to JSON checkpoint file with CLI metadata.

    Workflow:
    1. Convert TypedDict → Pydantic (validates)
    2. Create CLI metadata
    3. Combine state + metadata → CheckpointData
    4. Serialize CheckpointData → JSON
    5. Write JSON → File

    Args:
        state: TypedDict state from LangGraph
        filepath: Path to checkpoint file (e.g., ".acp/state/001-oauth2.json")
        feature_id: Feature identifier (e.g., "001-oauth2-authentication")
        thread_id: LangGraph thread ID
        status: Workflow status ("in_progress", "completed", "failed", "pending")
        phases_completed: List of completed phases (e.g., ["init", "specify"])
        feature_name: Human-readable feature name
        spec_path: Path to spec directory
        started_at: ISO timestamp when workflow started (auto-set if None)

    Raises:
        ValueError: If state fails validation
        IOError: If file write fails

    Example:
        >>> state = create_test_state()
        >>> save_checkpoint(
        ...     state,
        ...     ".acp/state/001-oauth2.json",
        ...     feature_id="001-oauth2-authentication",
        ...     thread_id="abc123",
        ... )
    """
    # Validate state via Pydantic
    try:
        validated_state = typed_dict_to_pydantic(state)
    except ValueError as e:
        raise ValueError(f"State validation failed: {e}")

    # Create CLI metadata
    if phases_completed is None:
        phases_completed = []

    now = datetime.now().isoformat()

    # Try to load existing metadata to preserve started_at
    if started_at is None and Path(filepath).exists():
        try:
            _, existing_metadata = load_checkpoint(filepath)
            started_at = existing_metadata.started_at
        except Exception:
            started_at = now
    elif started_at is None:
        started_at = now

    metadata = CLIMetadata(
        feature_id=feature_id,
        feature_name=feature_name,
        thread_id=thread_id,
        status=status,
        phases_completed=phases_completed,
        current_phase=validated_state.phase,
        started_at=started_at,
        updated_at=now,
        spec_path=spec_path,
        checkpoint_version="1.0.0",
        acpctl_version="1.0.0",
    )

    # Combine state and metadata
    checkpoint_data = CheckpointData(metadata=metadata, state=validated_state)

    # Serialize to JSON
    try:
        json_data = checkpoint_data.model_dump_json(indent=2)
    except Exception as e:
        raise ValueError(f"Serialization failed: {e}")

    # Write to file
    try:
        checkpoint_path = Path(filepath)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(json_data, encoding="utf-8")
    except IOError as e:
        raise IOError(f"Failed to write checkpoint: {e}")


def load_checkpoint(filepath: str) -> Tuple[ACPState, CLIMetadata]:
    """
    Load JSON checkpoint file to TypedDict state and CLI metadata.

    Workflow:
    1. Read JSON → File
    2. Parse JSON → Dict
    3. Validate Dict → CheckpointData (catches corruption)
    4. Extract state and metadata
    5. Convert state Pydantic → TypedDict

    Args:
        filepath: Path to checkpoint file

    Returns:
        Tuple of (ACPState TypedDict, CLIMetadata)

    Raises:
        FileNotFoundError: If checkpoint doesn't exist
        ValueError: If checkpoint is corrupted/invalid

    Example:
        >>> state, metadata = load_checkpoint(".acp/state/001-oauth2.json")
        >>> print(metadata.feature_id)
        '001-oauth2-authentication'
        >>> print(state['phase'])
        'plan'
    """
    checkpoint_path = Path(filepath)

    # Read file
    try:
        json_data = checkpoint_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Checkpoint not found: {filepath}")

    # Validate via Pydantic
    try:
        checkpoint_data = CheckpointData.model_validate_json(json_data)
    except Exception as e:
        raise ValueError(f"Checkpoint validation failed: {e}")

    # Convert state back to TypedDict
    state_dict = checkpoint_data.state.model_dump()
    typed_dict_state = ACPState(**state_dict)

    return typed_dict_state, checkpoint_data.metadata


def checkpoint_exists(filepath: str) -> bool:
    """
    Check if checkpoint file exists and is readable.

    Args:
        filepath: Path to checkpoint file

    Returns:
        True if checkpoint exists and is a file, False otherwise
    """
    checkpoint_path = Path(filepath)
    return checkpoint_path.exists() and checkpoint_path.is_file()


def validate_checkpoint_file(filepath: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a checkpoint file without loading it.

    Args:
        filepath: Path to checkpoint file

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Example:
        >>> valid, error = validate_checkpoint_file(".acp/state/001-oauth2.json")
        >>> if not valid:
        ...     print(f"Checkpoint invalid: {error}")
    """
    try:
        checkpoint_path = Path(filepath)
        if not checkpoint_path.exists():
            return False, "File does not exist"

        json_data = checkpoint_path.read_text(encoding="utf-8")
        CheckpointData.model_validate_json(json_data)
        return True, None
    except Exception as e:
        return False, str(e)


def list_checkpoints(state_dir: str = ".acp/state") -> List[Dict[str, Any]]:
    """
    List all checkpoint files in the state directory.

    Args:
        state_dir: Path to state directory (default: ".acp/state")

    Returns:
        List of checkpoint summaries with metadata

    Example:
        >>> checkpoints = list_checkpoints()
        >>> for cp in checkpoints:
        ...     print(f"{cp['feature_id']}: {cp['status']} ({cp['current_phase']})")
    """
    state_path = Path(state_dir)

    if not state_path.exists():
        return []

    checkpoints = []

    for checkpoint_file in state_path.glob("*.json"):
        try:
            _, metadata = load_checkpoint(str(checkpoint_file))
            checkpoints.append(
                {
                    "filepath": str(checkpoint_file),
                    "feature_id": metadata.feature_id,
                    "feature_name": metadata.feature_name,
                    "thread_id": metadata.thread_id,
                    "status": metadata.status,
                    "current_phase": metadata.current_phase,
                    "phases_completed": metadata.phases_completed,
                    "started_at": metadata.started_at,
                    "updated_at": metadata.updated_at,
                    "spec_path": metadata.spec_path,
                }
            )
        except (ValueError, FileNotFoundError):
            # Skip corrupted or invalid checkpoints
            continue

    # Sort by updated_at timestamp (most recent first)
    checkpoints.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

    return checkpoints


def get_latest_checkpoint(state_dir: str = ".acp/state") -> Optional[str]:
    """
    Get the filepath of the most recent checkpoint.

    Args:
        state_dir: Path to state directory (default: ".acp/state")

    Returns:
        Filepath of latest checkpoint, or None if no checkpoints exist

    Example:
        >>> latest = get_latest_checkpoint()
        >>> if latest:
        ...     state, metadata = load_checkpoint(latest)
    """
    checkpoints = list_checkpoints(state_dir)
    if not checkpoints:
        return None

    return checkpoints[0]["filepath"]


def get_checkpoint_by_feature_id(
    feature_id: str, state_dir: str = ".acp/state"
) -> Optional[str]:
    """
    Find checkpoint filepath by feature ID.

    Args:
        feature_id: Feature identifier (e.g., "001-oauth2-authentication")
        state_dir: Path to state directory (default: ".acp/state")

    Returns:
        Filepath of checkpoint, or None if not found

    Example:
        >>> filepath = get_checkpoint_by_feature_id("001-oauth2-authentication")
        >>> if filepath:
        ...     state, metadata = load_checkpoint(filepath)
    """
    checkpoints = list_checkpoints(state_dir)

    for checkpoint in checkpoints:
        if checkpoint["feature_id"] == feature_id:
            return checkpoint["filepath"]

    return None


# ============================================================
# SCHEMA VERSIONING (For Future Expansion)
# ============================================================


def get_checkpoint_version(filepath: str) -> str:
    """
    Get schema version from checkpoint file without full validation.

    Args:
        filepath: Path to checkpoint file

    Returns:
        Schema version string (e.g., "1.0.0")

    Raises:
        FileNotFoundError: If checkpoint doesn't exist
        ValueError: If checkpoint is malformed
    """
    checkpoint_path = Path(filepath)

    try:
        json_data = checkpoint_path.read_text(encoding="utf-8")
        raw_data = json.loads(json_data)

        # Look for version in state.schema_version
        if "state" in raw_data and "schema_version" in raw_data["state"]:
            return raw_data["state"]["schema_version"]

        # Default to 1.0.0 if not specified
        return "1.0.0"

    except FileNotFoundError:
        raise FileNotFoundError(f"Checkpoint not found: {filepath}")
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Malformed checkpoint: {e}")


def migrate_checkpoint_v1_to_v2(v1_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate V1 checkpoint to V2 format (placeholder for future use).

    Args:
        v1_data: Parsed V1 checkpoint dict

    Returns:
        Migrated dict compatible with V2 model

    Note:
        This is a placeholder for Phase 2+ when schema evolution is needed.
        Currently, all checkpoints use v1.0.0 schema.
    """
    v2_data = v1_data.copy()

    # Update schema version
    if "state" in v2_data:
        v2_data["state"]["schema_version"] = "2.0.0"

    # Add new V2 fields with defaults (example for future expansion)
    # v2_data['state']['task_dependencies'] = {}
    # v2_data['state']['parallel_batches'] = []

    return v2_data


def migrate_checkpoint(
    checkpoint: Dict[str, Any], from_version: str, to_version: str
) -> Dict[str, Any]:
    """
    Migrate checkpoint from one schema version to another.

    Supports automatic migration between schema versions to maintain
    backward compatibility when checkpoint format evolves.

    Args:
        checkpoint: Checkpoint dictionary to migrate
        from_version: Source schema version (e.g., "1.0.0")
        to_version: Target schema version (e.g., "2.0.0")

    Returns:
        Migrated checkpoint dictionary

    Raises:
        ValueError: If migration path is not supported

    Example:
        >>> checkpoint = load_old_checkpoint()
        >>> migrated = migrate_checkpoint(checkpoint, "1.0.0", "2.0.0")
        >>> save_checkpoint(migrated)
    """
    # No migration needed if versions match
    if from_version == to_version:
        return checkpoint

    # Handle v1.0.0 → v2.0.0 migration
    if from_version == "1.0.0" and to_version == "2.0.0":
        return migrate_checkpoint_v1_to_v2(checkpoint)

    # Add more migration paths as needed in future versions
    # Example for v2.0.0 → v3.0.0:
    # if from_version == "2.0.0" and to_version == "3.0.0":
    #     checkpoint = migrate_checkpoint_v2_to_v3(checkpoint)
    #     from_version = "3.0.0"

    # Handle multi-step migrations (e.g., v1 → v2 → v3)
    # For now, only direct migrations are supported

    raise ValueError(
        f"Migration from version {from_version} to {to_version} is not supported"
    )


def load_checkpoint_with_migration(
    filepath: str, target_version: Optional[str] = None
) -> Tuple[ACPState, CLIMetadata, bool]:
    """
    Load checkpoint and automatically migrate if needed.

    This function handles backward compatibility by detecting checkpoint
    schema version and migrating to current version if needed.

    Args:
        filepath: Path to checkpoint file
        target_version: Target schema version (defaults to current version)

    Returns:
        Tuple of (ACPState, CLIMetadata, was_migrated: bool)

    Example:
        >>> state, metadata, migrated = load_checkpoint_with_migration("001.json")
        >>> if migrated:
        ...     print("Checkpoint was migrated to current version")
        ...     # Save migrated checkpoint
        ...     save_checkpoint(state, filepath, ...)
    """
    if target_version is None:
        # Use current schema version as target
        from acpctl.utils.validation import get_schema_version

        target_version = get_schema_version()

    # Load checkpoint
    checkpoint_path = Path(filepath)

    try:
        json_data = checkpoint_path.read_text(encoding="utf-8")
        raw_checkpoint = json.loads(json_data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Checkpoint not found: {filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in checkpoint: {e}")

    # Detect checkpoint version
    checkpoint_version = raw_checkpoint.get("state", {}).get("schema_version", "1.0.0")

    # Migrate if needed
    was_migrated = False
    if checkpoint_version != target_version:
        try:
            raw_checkpoint = migrate_checkpoint(
                raw_checkpoint, checkpoint_version, target_version
            )
            was_migrated = True
        except ValueError as e:
            raise ValueError(f"Checkpoint migration failed: {e}")

    # Validate migrated checkpoint
    try:
        checkpoint_data = CheckpointData(**raw_checkpoint)
    except Exception as e:
        raise ValueError(f"Checkpoint validation failed after migration: {e}")

    # Convert to TypedDict
    state_dict = checkpoint_data.state.model_dump()
    typed_dict_state = ACPState(**state_dict)

    return typed_dict_state, checkpoint_data.metadata, was_migrated
