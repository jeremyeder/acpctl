"""
acpctl Core State Models

Defines the state schema for LangGraph workflow orchestration with Pydantic validation.
Implements a hybrid TypedDict + Pydantic pattern for optimal performance and validation.

Architecture:
- TypedDict: Used in LangGraph StateGraph for zero-overhead node execution
- Pydantic: Used at checkpoint boundaries for validation and serialization

Reference: STATE_IMPLEMENTATION_TEMPLATE.py, PYDANTIC_STATE_RESEARCH.md
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator


# ============================================================
# PHASE 1: CORE STATE DEFINITIONS
# ============================================================


class ACPState(TypedDict):
    """
    LangGraph state schema - used in StateGraph(ACPState).

    TypedDict is used for performance (zero validation overhead per node).
    Validation happens only at checkpoint boundaries via Pydantic.

    This represents the complete workflow state passed between agents.
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
    error_count: int


class ACPStateModel(BaseModel):
    """
    Pydantic model for checkpoint validation and serialization.

    Used at checkpoint boundaries:
    - Checkpoint Save: TypedDict → ACPStateModel → JSON
    - Checkpoint Load: JSON → ACPStateModel → TypedDict

    Provides field validation, workflow invariant enforcement, and JSON serialization.
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
    error_count: int = 0

    # ========================================================
    # FIELD VALIDATORS - Individual field constraints
    # ========================================================

    @field_validator("phase")
    @classmethod
    def validate_phase(cls, v: str) -> str:
        """Ensure phase is one of allowed workflow values."""
        allowed_phases = {"init", "specify", "plan", "implement", "complete"}
        if v not in allowed_phases:
            raise ValueError(f"Invalid phase '{v}'. Must be one of {allowed_phases}")
        return v

    @field_validator("clarifications", mode="after")
    @classmethod
    def validate_clarifications(cls, v: List[str]) -> List[str]:
        """Ensure clarifications are non-empty strings."""
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("All clarifications must be non-empty strings")
        return v

    @field_validator("completed_tasks", mode="after")
    @classmethod
    def validate_completed_tasks(cls, v: List[str], info: ValidationInfo) -> List[str]:
        """Completed tasks must be a subset of all tasks."""
        all_tasks = info.data.get("tasks", [])
        all_task_ids = {t.get("id") for t in all_tasks if isinstance(t, dict)}

        for task_id in v:
            if task_id not in all_task_ids:
                raise ValueError(f"Completed task '{task_id}' not found in task list")
        return v

    @field_validator("contracts", mode="before")
    @classmethod
    def validate_contracts(cls, v: Any) -> Dict[str, Any]:
        """Ensure contracts is always a dict."""
        if not isinstance(v, dict):
            raise ValueError("contracts must be a dictionary")
        return v

    # ========================================================
    # MODEL VALIDATORS - Workflow state transitions
    # ========================================================

    @model_validator(mode="after")
    def validate_state_transitions(self) -> "ACPStateModel":
        """
        Enforce workflow invariants across multiple fields.

        Ensures logical consistency and prevents invalid state transitions.
        """

        # Rule 1: Specification requires constitution
        if self.phase in {"specify", "plan", "implement", "complete"}:
            if not self.constitution or not self.governance_passes:
                raise ValueError(
                    "Cannot transition to 'specify' phase: "
                    "requires constitution and governance_passes=True"
                )

        # Rule 2: Planning requires specification
        if self.phase in {"plan", "implement", "complete"}:
            if not self.spec or not self.feature_description:
                raise ValueError(
                    "Cannot transition to 'plan' phase: "
                    "requires completed specification (spec + feature_description)"
                )

        # Rule 3: Implementation requires plan
        if self.phase in {"implement", "complete"}:
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
        if self.phase == "complete":
            if len(self.tasks) == 0:
                raise ValueError("Cannot mark complete: no tasks defined")
            if len(self.completed_tasks) != len(self.tasks):
                raise ValueError(
                    f"Cannot mark complete: {len(self.tasks) - len(self.completed_tasks)} "
                    f"tasks remaining"
                )

        return self

    @model_validator(mode="after")
    def validate_governance_gates(self) -> "ACPStateModel":
        """
        Governance must pass to be in any phase beyond init.
        """
        if self.phase != "init" and not self.governance_passes:
            raise ValueError(
                f"Cannot be in '{self.phase}' phase without passing governance gate"
            )
        return self

    class Config:
        """Pydantic config for extra type validation."""

        extra = "forbid"  # Reject unknown fields
        str_strip_whitespace = True  # Auto-strip string fields

    # ========================================================
    # CUSTOM SERIALIZATION
    # ========================================================

    def serialize_contracts_for_json(
        self, contracts: Dict[str, Any]
    ) -> Dict[str, Any]:
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


# ============================================================
# STATE TRANSITION HANDLER
# ============================================================


def transition_state(
    state: ACPStateModel, new_phase: str, updates: Dict[str, Any]
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
    """
    # Create updated state dict
    new_state_dict = state.model_dump()
    new_state_dict.update(updates)
    new_state_dict["phase"] = new_phase

    # Validation happens here - will raise ValueError if invariants violated
    new_state = ACPStateModel(**new_state_dict)

    return new_state


# ============================================================
# CONVERSION UTILITIES
# ============================================================


def typed_dict_to_pydantic(state: ACPState) -> ACPStateModel:
    """
    Convert TypedDict (from LangGraph) to Pydantic (for validation).

    Args:
        state: ACPState TypedDict from LangGraph workflow

    Returns:
        ACPStateModel with validation applied

    Raises:
        ValueError: If state fails validation
    """
    return ACPStateModel(**state)


def pydantic_to_typed_dict(model: ACPStateModel) -> ACPState:
    """
    Convert Pydantic (after validation) to TypedDict (for LangGraph).

    Args:
        model: Validated ACPStateModel

    Returns:
        ACPState TypedDict ready for LangGraph
    """
    return ACPState(**model.model_dump())


# ============================================================
# TESTING UTILITIES
# ============================================================


def create_test_state(phase: str = "init", **overrides: Any) -> ACPState:
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
