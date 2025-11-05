"""
acpctl State Model Implementation Template

This module provides production-ready patterns for implementing
ACPState with Pydantic validation and JSON checkpointing.

Reference: PYDANTIC_STATE_RESEARCH.md
"""

from pydantic import BaseModel, field_validator, model_validator, ValidationInfo, Field
from typing import TypedDict, List, Dict, Any, Optional, Literal, Union
from datetime import datetime
from dataclasses import dataclass
import json
from pathlib import Path


# ============================================================
# PHASE 1: CORE STATE DEFINITIONS
# ============================================================

class ACPState(TypedDict):
    """
    LangGraph state schema - used in StateGraph(ACPState).

    TypedDict is used for performance (zero validation overhead per node).
    Validation happens only at checkpoint boundaries via Pydantic.
    """
    # Constitution layer
    constitution: str
    governance_passes: bool

    # Specification layer
    feature_description: str
    spec: str
    clarifications: List[str]

    # Planning layer
    unknowns: List[str]
    research: str
    plan: str
    data_model: str
    contracts: Dict[str, Any]

    # Task/Implementation layers
    tasks: List[Dict[str, Any]]
    completed_tasks: List[str]
    code_artifacts: Dict[str, str]
    validation_status: str

    # Workflow control
    phase: str


class ACPStateModel(BaseModel):
    """
    Pydantic model for checkpoint validation and serialization.

    Used at checkpoint boundaries:
    - Checkpoint Save: TypedDict → ACPStateModel → JSON
    - Checkpoint Load: JSON → ACPStateModel → TypedDict
    """
    schema_version: str = "1.0.0"
    created_at: str = ""

    # Constitution layer
    constitution: str = ""
    governance_passes: bool = False

    # Specification layer
    feature_description: str = ""
    spec: str = ""
    clarifications: List[str] = Field(default_factory=list)

    # Planning layer
    unknowns: List[str] = Field(default_factory=list)
    research: str = ""
    plan: str = ""
    data_model: str = ""
    contracts: Dict[str, Any] = Field(default_factory=dict)

    # Task/Implementation layers
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    code_artifacts: Dict[str, str] = Field(default_factory=dict)
    validation_status: str = "pending"

    # Workflow control
    phase: str = "init"

    # ========================================================
    # FIELD VALIDATORS - Individual field constraints
    # ========================================================

    @field_validator('phase')
    @classmethod
    def validate_phase(cls, v: str) -> str:
        """Ensure phase is one of allowed workflow values."""
        allowed_phases = {'init', 'specify', 'plan', 'implement', 'complete'}
        if v not in allowed_phases:
            raise ValueError(
                f"Invalid phase '{v}'. Must be one of {allowed_phases}"
            )
        return v

    @field_validator('clarifications', mode='after')
    @classmethod
    def validate_clarifications(cls, v: List[str]) -> List[str]:
        """Ensure clarifications are non-empty strings."""
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    "All clarifications must be non-empty strings"
                )
        return v

    @field_validator('completed_tasks', mode='after')
    @classmethod
    def validate_completed_tasks(cls, v: List[str], info: ValidationInfo) -> List[str]:
        """Completed tasks must be a subset of all tasks."""
        all_tasks = info.data.get('tasks', [])
        all_task_ids = {t.get('id') for t in all_tasks if isinstance(t, dict)}

        for task_id in v:
            if task_id not in all_task_ids:
                raise ValueError(
                    f"Completed task '{task_id}' not found in task list"
                )
        return v

    # ========================================================
    # FIELD SERIALIZERS - Handle complex types
    # ========================================================

    @field_validator('contracts', mode='before')
    @classmethod
    def validate_contracts(cls, v: Any) -> Dict[str, Any]:
        """Ensure contracts is always a dict."""
        if not isinstance(v, dict):
            raise ValueError("contracts must be a dictionary")
        return v

    # Custom serializer for JSON compatibility
    def serialize_contracts_for_json(self, contracts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively convert non-JSON-serializable types in contracts dict.
        Called during model_dump_json() if contracts contains complex objects.
        """
        def make_json_safe(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_json_safe(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                # Fallback: stringify unknown types
                return str(obj)

        return make_json_safe(contracts)

    # ========================================================
    # MODEL VALIDATORS - Workflow state transitions
    # ========================================================

    @model_validator(mode='after')
    def validate_state_transitions(self) -> 'ACPStateModel':
        """
        Enforce workflow invariants across multiple fields.

        Ensures logical consistency and prevents invalid state transitions.
        """
        phase_order = ['init', 'specify', 'plan', 'implement', 'complete']

        # Rule 1: Specification requires constitution
        if self.phase in {'specify', 'plan', 'implement', 'complete'}:
            if not self.constitution or not self.governance_passes:
                raise ValueError(
                    "Cannot transition to 'specify' phase: "
                    "requires constitution and governance_passes=True"
                )

        # Rule 2: Planning requires specification
        if self.phase in {'plan', 'implement', 'complete'}:
            if not self.spec or not self.feature_description:
                raise ValueError(
                    "Cannot transition to 'plan' phase: "
                    "requires completed specification (spec + feature_description)"
                )

        # Rule 3: Implementation requires plan
        if self.phase in {'implement', 'complete'}:
            if not self.plan or not self.data_model:
                raise ValueError(
                    "Cannot transition to 'implement' phase: "
                    "requires completed plan (plan + data_model)"
                )

        # Rule 4: Completed tasks cannot exceed total tasks
        if len(self.completed_tasks) > len(self.tasks):
            raise ValueError(
                f"Completed tasks ({len(self.completed_tasks)}) "
                f"exceed total tasks ({len(self.tasks)})"
            )

        # Rule 5: Can only mark complete when all tasks are done
        if self.phase == 'complete':
            if len(self.tasks) == 0:
                raise ValueError(
                    "Cannot mark complete: no tasks defined"
                )
            if len(self.completed_tasks) != len(self.tasks):
                raise ValueError(
                    f"Cannot mark complete: {len(self.tasks) - len(self.completed_tasks)} "
                    f"tasks remaining"
                )

        return self

    @model_validator(mode='after')
    def validate_governance_gates(self) -> 'ACPStateModel':
        """
        Governance must pass to be in any phase beyond init.
        """
        if self.phase != 'init' and not self.governance_passes:
            raise ValueError(
                f"Cannot be in '{self.phase}' phase without passing governance gate"
            )
        return self

    class Config:
        """Pydantic config for extra type validation."""
        extra = 'forbid'  # Reject unknown fields
        str_strip_whitespace = True  # Auto-strip string fields


# ============================================================
# STATE TRANSITION HANDLER
# ============================================================

def transition_state(
    state: ACPStateModel,
    new_phase: str,
    updates: Dict[str, Any]
) -> ACPStateModel:
    """
    Safely transition to a new phase with validation.

    Args:
        state: Current ACPStateModel instance
        new_phase: Target phase name (must be in allowed phases)
        updates: Fields to update before transition

    Returns:
        New ACPStateModel with updated phase and fields

    Raises:
        ValueError: If transition violates workflow invariants

    Example:
        >>> state = ACPStateModel()
        >>> state = transition_state(
        ...     state,
        ...     "specify",
        ...     {
        ...         'constitution': 'Our principles...',
        ...         'governance_passes': True,
        ...         'feature_description': 'Add OAuth2'
        ...     }
        ... )
        ✓ Transitioned to phase 'specify'
    """
    # Create updated state dict
    new_state_dict = state.model_dump()
    new_state_dict.update(updates)
    new_state_dict['phase'] = new_phase

    # Validation happens here - will raise ValueError if invariants violated
    new_state = ACPStateModel(**new_state_dict)

    print(f"✓ Transitioned to phase '{new_phase}'")
    return new_state


# ============================================================
# CHECKPOINT OPERATIONS
# ============================================================

def save_checkpoint(state: ACPState, filepath: str) -> None:
    """
    Save TypedDict state to JSON checkpoint file.

    Workflow:
    1. Convert TypedDict → Pydantic (validates)
    2. Serialize Pydantic → JSON (handles complex types)
    3. Write JSON → File

    Args:
        state: TypedDict state from LangGraph
        filepath: Path to checkpoint file

    Raises:
        ValueError: If state fails validation
        IOError: If file write fails

    Example:
        >>> state = load_initial_state()
        >>> save_checkpoint(state, ".acp/state/001-oauth2.json")
        ✓ Checkpoint saved: .acp/state/001-oauth2.json
    """
    # Validate state via Pydantic
    try:
        validated = ACPStateModel(**state)
    except ValueError as e:
        raise ValueError(f"State validation failed: {e}")

    # Serialize with mode='json' to ensure JSON compatibility
    try:
        json_data = validated.model_dump_json(mode='json', indent=2)
    except Exception as e:
        raise ValueError(f"Serialization failed: {e}")

    # Write to file
    try:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(json_data)
        print(f"✓ Checkpoint saved: {filepath}")
    except IOError as e:
        raise IOError(f"Failed to write checkpoint: {e}")


def load_checkpoint(filepath: str) -> ACPState:
    """
    Load JSON checkpoint file to TypedDict state.

    Workflow:
    1. Read JSON → File
    2. Parse JSON → Dict
    3. Validate Dict → Pydantic (catches corruption)
    4. Convert Pydantic → TypedDict

    Args:
        filepath: Path to checkpoint file

    Returns:
        ACPState TypedDict ready for LangGraph

    Raises:
        FileNotFoundError: If checkpoint doesn't exist
        ValueError: If checkpoint is corrupted/invalid

    Example:
        >>> state = load_checkpoint(".acp/state/001-oauth2.json")
        >>> state['phase']
        'plan'
    """
    filepath = Path(filepath)

    # Read file
    try:
        json_data = filepath.read_text()
    except FileNotFoundError:
        raise FileNotFoundError(f"Checkpoint not found: {filepath}")

    # Validate via Pydantic
    try:
        validated = ACPStateModel.model_validate_json(json_data)
    except Exception as e:
        raise ValueError(f"Checkpoint validation failed: {e}")

    # Convert back to TypedDict
    return ACPState(**validated.model_dump())


def checkpoint_exists(filepath: str) -> bool:
    """Check if checkpoint file exists and is readable."""
    return Path(filepath).exists() and Path(filepath).is_file()


# ============================================================
# PHASE 2: VERSIONED STATE (For Future Expansion)
# ============================================================

class ACPStateV2(BaseModel):
    """
    Version 2 state model - adds Phase 2 features.

    Backward compatible: includes all V1 fields plus new fields.
    """
    schema_version: Literal["2.0.0"] = "2.0.0"
    created_at: str = ""
    updated_at: str = ""

    # All V1 fields (unchanged)
    constitution: str = ""
    governance_passes: bool = False
    feature_description: str = ""
    spec: str = ""
    clarifications: List[str] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    research: str = ""
    plan: str = ""
    data_model: str = ""
    contracts: Dict[str, Any] = Field(default_factory=dict)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    code_artifacts: Dict[str, str] = Field(default_factory=dict)
    validation_status: str = "pending"
    phase: str = "init"

    # NEW Phase 2 fields (all optional with defaults)
    task_dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    parallel_batches: List[List[str]] = Field(default_factory=list)
    validation_report: Dict[str, Any] = Field(default_factory=dict)
    checkpoint_reason: str = "phase_complete"


def migrate_checkpoint_v1_to_v2(v1_data: dict) -> dict:
    """
    Migrate V1 checkpoint to V2 format.

    Adds new V2 fields with sensible defaults.
    No data loss - V1 fields preserved exactly.

    Args:
        v1_data: Parsed V1 checkpoint dict

    Returns:
        Migrated dict compatible with V2 model
    """
    v2_data = v1_data.copy()

    # Update schema version
    v2_data['schema_version'] = '2.0.0'

    # Add new V2 fields with defaults
    v2_data['updated_at'] = datetime.now().isoformat()
    v2_data['task_dependencies'] = {}
    v2_data['parallel_batches'] = []
    v2_data['validation_report'] = {}
    v2_data['checkpoint_reason'] = 'migrated_from_v1'

    return v2_data


def load_checkpoint_with_migration(
    filepath: str,
    target_version: str = "1.0.0"
) -> Union[ACPStateModel, ACPStateV2]:
    """
    Load checkpoint with automatic version migration.

    Detects current version and migrates if needed.

    Args:
        filepath: Path to checkpoint file
        target_version: Target schema version ("1.0.0" or "2.0.0")

    Returns:
        Appropriate Pydantic model for target version

    Example:
        >>> # Load V1 checkpoint with auto-migration to V2
        >>> state = load_checkpoint_with_migration(
        ...     ".acp/state/old.json",
        ...     target_version="2.0.0"
        ... )
    """
    filepath = Path(filepath)
    json_data = filepath.read_text()
    raw_data = json.loads(json_data)

    current_version = raw_data.get('schema_version', '1.0.0')

    # Migrate if needed
    if current_version == '1.0.0' and target_version == '2.0.0':
        print(f"Migrating checkpoint from {current_version} to {target_version}...")
        raw_data = migrate_checkpoint_v1_to_v2(raw_data)

    # Validate against target schema
    if target_version == '2.0.0':
        return ACPStateV2(**raw_data)
    else:
        return ACPStateModel(**raw_data)


# ============================================================
# TESTING UTILITIES
# ============================================================

def create_test_state(phase: str = "init", **overrides) -> ACPState:
    """
    Create a test state for development/testing.

    Args:
        phase: Starting phase
        **overrides: Field overrides

    Returns:
        Valid ACPState ready for testing
    """
    model = ACPStateModel(phase=phase, **overrides)
    return ACPState(**model.model_dump())


def validate_checkpoint_file(filepath: str) -> tuple[bool, Optional[str]]:
    """
    Validate a checkpoint file without loading it.

    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    try:
        filepath = Path(filepath)
        if not filepath.exists():
            return False, "File does not exist"

        json_data = filepath.read_text()
        ACPStateModel.model_validate_json(json_data)
        return True, None
    except Exception as e:
        return False, str(e)


# ============================================================
# CLI INTEGRATION EXAMPLE
# ============================================================

def cli_init_workflow(constitution: str) -> ACPState:
    """Example: CLI command 'acpctl init'"""
    state = ACPStateModel(
        constitution=constitution,
        governance_passes=True,
        phase='init'
    )
    return ACPState(**state.model_dump())


def cli_specify(state: ACPState, description: str, clarifications: List[str]) -> ACPState:
    """Example: CLI command 'acpctl specify'"""
    model = ACPStateModel(**state)
    model = transition_state(
        model,
        'specify',
        {
            'feature_description': description,
            'clarifications': clarifications,
            'spec': f"Specification for: {description}"
        }
    )
    return ACPState(**model.model_dump())


def cli_checkpoint(state: ACPState, spec_id: str) -> None:
    """Example: CLI command 'acpctl checkpoint'"""
    filepath = f".acp/state/{spec_id}.json"
    save_checkpoint(state, filepath)


def cli_resume(spec_id: str) -> ACPState:
    """Example: CLI command 'acpctl resume'"""
    filepath = f".acp/state/{spec_id}.json"
    return load_checkpoint(filepath)


# ============================================================
# USAGE EXAMPLES
# ============================================================

if __name__ == "__main__":
    # Example 1: Valid state transition
    print("=== Example 1: Valid State Transition ===")
    state = ACPStateModel()
    state = transition_state(
        state,
        'specify',
        {
            'constitution': 'Security first, open standards',
            'governance_passes': True,
            'feature_description': 'Add OAuth2 support'
        }
    )
    print(f"Phase: {state.phase}")
    print()

    # Example 2: Invalid transition (missing constitution)
    print("=== Example 2: Invalid Transition ===")
    try:
        invalid_state = ACPStateModel(
            phase='specify',
            governance_passes=False  # Missing constitution
        )
    except ValueError as e:
        print(f"✗ Validation error: {e}")
    print()

    # Example 3: Checkpoint round-trip
    print("=== Example 3: Checkpoint Round-Trip ===")
    typed_dict_state = ACPState(
        constitution='Principles...',
        governance_passes=True,
        feature_description='OAuth2',
        spec='',
        clarifications=[],
        unknowns=[],
        research='',
        plan='',
        data_model='',
        contracts={},
        tasks=[],
        completed_tasks=[],
        code_artifacts={},
        validation_status='pending',
        phase='specify'
    )

    # Save
    filepath = "/tmp/test_checkpoint.json"
    save_checkpoint(typed_dict_state, filepath)

    # Load
    loaded = load_checkpoint(filepath)
    print(f"Loaded phase: {loaded['phase']}")
    print(f"Round-trip successful: {loaded['constitution'] == typed_dict_state['constitution']}")

