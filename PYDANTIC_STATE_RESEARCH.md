# Pydantic State Model Best Practices for acpctl

**Research Date**: November 5, 2025
**Context**: acpctl workflow state architecture using LangGraph with JSON checkpointing
**Status**: Research-based recommendations with code patterns

---

## Executive Summary

This document provides evidence-based recommendations for defining acpctl's `ACPState` structure. The research identifies a **layered hybrid approach** as optimal for acpctl's requirements:

- **TypedDict for LangGraph internal state** (minimal overhead, type-safe)
- **Pydantic BaseModel for boundary validation** (API inputs, checkpoint I/O)
- **JSON serialization via Pydantic** for checkpoint files

This approach balances LangGraph's performance requirements with enterprise-grade validation for checkpoint persistence.

---

## State Model Architecture

### Decision: Layered Hybrid Approach

**Primary Layer (LangGraph Internal)**: TypedDict
**Boundary Layer (I/O, Checkpointing)**: Pydantic BaseModel
**Serialization Format**: JSON via Pydantic's `model_dump_json()`

### Rationale

**Why This Hybrid Over Pure Approaches**:

1. **Pure TypedDict drawback**: No runtime validation on checkpoint loading—malformed JSON silently corrupts state
2. **Pure Pydantic drawback**: Runtime validation overhead on every LangGraph node execution slows graph traversal
3. **Hybrid advantage**: Fast internal graph execution + validated state persistence

**LangGraph Integration Pattern**:
- LangGraph nodes operate on **TypedDict state** (zero validation overhead)
- At checkpoint boundaries, Pydantic **validates** TypedDict before serialization
- On resume, Pydantic **validates** deserialized JSON before TypedDict conversion
- Result: Type-safe, performance-optimized workflow

### Alternatives Considered

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Pure Pydantic** | Strong validation throughout | Runtime overhead on every node; LangGraph performance impact | ❌ Not recommended |
| **Pure TypedDict** | Zero overhead; native LangGraph | No validation; corrupted checkpoints silent fail | ❌ Not recommended |
| **Hybrid (TypedDict + Pydantic)** | Fast graph + validated persistence | Slight complexity in boundary translation | ✅ **Recommended** |
| **Dataclass + Pydantic** | Similar to hybrid | Fewer type hint tools; Pydantic is more powerful | ⚠️ Secondary option |

---

## JSON Serialization Strategy

### Decision: Pydantic `model_dump_json()` with Field Serializers

### Rationale

**Why `model_dump_json()` for Checkpointing**:

1. **Automatic Type Conversion**: Handles datetime, UUID, complex objects without custom encoders
2. **Deterministic Output**: Consistent JSON format across serialization calls
3. **Mode Parameter**: `mode='json'` ensures only JSON-safe types in output
4. **Built-in Validation**: `model_validate_json()` on deserialization catches corruption early

**Key Pydantic Features for acpctl**:

1. **`mode='json'` Parameter**: Converts Python objects to JSON-compatible primitives
   ```python
   # During checkpoint save
   state_dict = pydantic_model.model_dump(mode='json')
   json_bytes = json.dumps(state_dict).encode()

   # During checkpoint load
   loaded_dict = json.loads(json_bytes.decode())
   validated_model = ACPStateModel.model_validate(loaded_dict)
   ```

2. **Field Serializers**: Custom serialization for complex nested structures
   ```python
   @field_serializer('contracts', when_used='json')
   def serialize_contracts(self, v: dict) -> dict:
       # Ensure all contract values are JSON-serializable
       return {k: str(v_item) if not isinstance(v_item, (str, int, float, bool, type(None))) else v_item
               for k, v_item in v.items()}
   ```

3. **SerializeAsAny**: For polymorphic types (e.g., list of mixed artifact types)
   ```python
   from pydantic import SerializeAsAny
   from typing import Annotated

   code_artifacts: Annotated[dict, SerializeAsAny[dict]] = {}
   ```

### Implementation Pattern for acpctl

**Checkpoint Write**:
```python
def save_checkpoint(state: ACPState, filepath: str) -> None:
    """Serialize TypedDict state through Pydantic validation to JSON checkpoint."""
    # Convert TypedDict to Pydantic model
    validated_state = ACPStateModel(**state)

    # Serialize to JSON with mode='json'
    json_data = validated_state.model_dump_json(mode='json', indent=2)

    # Write checkpoint file
    with open(filepath, 'w') as f:
        f.write(json_data)
```

**Checkpoint Load & Resume**:
```python
def load_checkpoint(filepath: str) -> ACPState:
    """Deserialize JSON checkpoint through Pydantic validation to TypedDict."""
    # Read and validate JSON
    with open(filepath, 'r') as f:
        json_data = f.read()

    validated_state = ACPStateModel.model_validate_json(json_data)

    # Convert Pydantic model back to TypedDict
    return ACPState(**validated_state.model_dump())
```

### Handling Complex Types in Contracts

**Challenge**: `contracts: dict` can contain mixed types (strings, objects, nested dicts)

**Solution: Custom Serializer Pattern**:
```python
from pydantic import BaseModel, field_serializer
from typing import Any, Dict

class ACPStateModel(BaseModel):
    contracts: Dict[str, Any] = {}

    @field_serializer('contracts', when_used='json')
    def serialize_contracts_to_json(self, v: Dict[str, Any], _info) -> Dict[str, Any]:
        """Recursively convert non-JSON-serializable types."""
        def make_serializable(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                # Convert unknown types to string representation
                return str(obj)

        return make_serializable(v)
```

### Benefits for acpctl Checkpoints

| Requirement | How Pydantic Handles |
|-------------|---------------------|
| **Nested lists** (e.g., `clarifications: List[str]`) | Automatic validation; fails on non-string items |
| **Complex dicts** (e.g., `contracts: dict`) | Custom serializer handles polymorphic values |
| **Validation on load** | `model_validate_json()` catches corrupted checkpoints immediately |
| **Deterministic format** | Consistent JSON output for version control / diffing |
| **Type safety** | TypedDict used in LangGraph; Pydantic validates at boundaries |

---

## State Validation & Transitions

### Decision: Pydantic Model Validators for Workflow State Invariants

### Rationale

**Why Not Just Field Validators**:
- Field validators handle individual field constraints (e.g., "clarifications must be non-empty strings")
- State transitions require cross-field invariants (e.g., "can't specify without constitution")
- Model validators enable holistic workflow logic

**Four Validator Types Available**:

1. **After Validators** (Recommended): Run post-Pydantic validation, type-safe
2. **Before Validators**: Process raw input before parsing
3. **Wrap Validators**: Complete control over validation flow
4. **Plain Validators**: Terminate validation chain immediately

### Code Pattern: State Transition Validation

```python
from pydantic import BaseModel, field_validator, model_validator, ValidationInfo
from typing import Optional, List, Dict, Any

class ACPStateModel(BaseModel):
    """Pydantic model for acpctl state with transition validation."""

    # Constitution layer
    constitution: str = ""
    governance_passes: bool = False

    # Specification layer
    feature_description: str = ""
    spec: str = ""
    clarifications: List[str] = []

    # Planning layer
    unknowns: List[str] = []
    research: str = ""
    plan: str = ""
    data_model: str = ""
    contracts: Dict[str, Any] = {}

    # Task/Implementation layers
    tasks: List[Dict[str, Any]] = []
    completed_tasks: List[str] = []
    code_artifacts: Dict[str, str] = {}
    validation_status: str = "pending"

    # Workflow phase tracking (for transition validation)
    phase: str = "init"  # init → specify → plan → implement → complete

    # ============================================================
    # FIELD VALIDATORS - Individual field constraints
    # ============================================================

    @field_validator('phase')
    @classmethod
    def validate_phase(cls, v: str) -> str:
        """Ensure phase is one of allowed values."""
        allowed_phases = {'init', 'specify', 'plan', 'implement', 'complete'}
        if v not in allowed_phases:
            raise ValueError(f"Invalid phase '{v}'. Must be one of {allowed_phases}")
        return v

    @field_validator('clarifications', mode='after')
    @classmethod
    def validate_clarifications(cls, v: List[str]) -> List[str]:
        """Ensure clarifications are non-empty strings."""
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Clarifications must be non-empty strings")
        return v

    @field_validator('completed_tasks', mode='after')
    @classmethod
    def validate_completed_tasks(cls, v: List[str], info: ValidationInfo) -> List[str]:
        """Completed tasks must be subset of all tasks."""
        all_tasks = info.data.get('tasks', [])
        all_task_ids = {t.get('id') for t in all_tasks}

        for task_id in v:
            if task_id not in all_task_ids:
                raise ValueError(f"Completed task '{task_id}' not in task list")
        return v

    # ============================================================
    # MODEL VALIDATORS - Workflow state transition rules
    # ============================================================

    @model_validator(mode='after')
    def validate_state_transitions(self) -> 'ACPStateModel':
        """
        Enforce workflow invariants that span multiple fields.
        Ensures logical consistency of state transitions.
        """

        # Rule 1: Specification requires constitution
        if self.phase in {'specify', 'plan', 'implement', 'complete'}:
            if not self.constitution or not self.governance_passes:
                raise ValueError(
                    "Cannot transition to 'specify' phase without valid constitution "
                    "and governance_passes=True"
                )

        # Rule 2: Planning requires specification
        if self.phase in {'plan', 'implement', 'complete'}:
            if not self.spec or not self.feature_description:
                raise ValueError(
                    "Cannot transition to 'plan' phase without completed specification"
                )

        # Rule 3: Implementation requires plan
        if self.phase in {'implement', 'complete'}:
            if not self.plan or not self.data_model:
                raise ValueError(
                    "Cannot transition to 'implement' phase without completed plan"
                )

        # Rule 4: Completed tasks cannot exceed total tasks
        if len(self.completed_tasks) > len(self.tasks):
            raise ValueError(
                f"Completed tasks ({len(self.completed_tasks)}) exceed total tasks ({len(self.tasks)})"
            )

        # Rule 5: Can only mark complete when all tasks are done
        if self.phase == 'complete' and len(self.completed_tasks) != len(self.tasks):
            raise ValueError(
                "Cannot mark workflow complete until all tasks are completed"
            )

        return self

    @model_validator(mode='after')
    def validate_governance_gates(self) -> 'ACPStateModel':
        """
        Additional validation: governance gates must be passed
        before advancing to next phase.
        """
        phase_order = ['init', 'specify', 'plan', 'implement', 'complete']
        current_phase_idx = phase_order.index(self.phase)

        # After init, governance must always pass
        if current_phase_idx > 0 and not self.governance_passes:
            raise ValueError(
                f"Cannot be in '{self.phase}' phase without passing governance gate"
            )

        return self


# ============================================================
# STATE TRANSITION HANDLER
# ============================================================

def transition_state(
    state: 'ACPStateModel',
    new_phase: str,
    updates: Dict[str, Any]
) -> 'ACPStateModel':
    """
    Safely transition to a new phase with validation.

    Args:
        state: Current state model
        new_phase: Target phase
        updates: Fields to update before transition

    Returns:
        New validated state

    Raises:
        ValueError: If transition violates workflow invariants
    """
    # Create updated state
    new_state_dict = state.model_dump()
    new_state_dict.update(updates)
    new_state_dict['phase'] = new_phase

    # Validation happens here - will raise if invariants violated
    new_state = ACPStateModel(**new_state_dict)

    print(f"✓ Transitioned to phase '{new_phase}'")
    return new_state
```

### Example Usage: Workflow Phase Progression

```python
# Initialize state
state = ACPStateModel()  # phase='init'

# Specify phase: requires constitution
try:
    state = transition_state(
        state,
        new_phase='specify',
        updates={
            'constitution': 'Our principles...',
            'governance_passes': True,
            'feature_description': 'Add OAuth2 support'
        }
    )
except ValueError as e:
    print(f"Invalid transition: {e}")

# Plan phase: requires specification
state = transition_state(
    state,
    new_phase='plan',
    updates={
        'spec': 'OAuth2 support specification...',
        'plan': 'Implementation plan...',
        'data_model': 'DB schema...'
    }
)

# Verify state is valid at each step
assert state.phase == 'plan'
assert state.governance_passes == True
assert len(state.spec) > 0
```

### State Transition Diagram

```
init (empty state)
  ↓
  [Must have: constitution + governance_passes=True]
  ↓
specify (feature_description, spec, clarifications filled)
  ↓
  [Must have: plan + data_model]
  ↓
plan (planning artifacts complete)
  ↓
  [Must have: tasks list]
  ↓
implement (executing tasks, building code)
  ↓
  [Must have: all completed_tasks == all tasks]
  ↓
complete (workflow done)
```

### Validation Rules Summary

| Transition | Preconditions | Triggered Validators |
|------------|---------------|---------------------|
| init → specify | `constitution` and `governance_passes=True` | `validate_state_transitions()` |
| specify → plan | `spec` and `feature_description` populated | `validate_state_transitions()` |
| plan → implement | `plan` and `data_model` populated | `validate_state_transitions()` |
| implement → complete | `completed_tasks == tasks` | `validate_state_transitions()` + `validate_governance_gates()` |

---

## Schema Versioning

### Decision: Version-Aware Checkpoint Format with Migration Strategy

### Rationale

**Why Versioning Matters for acpctl**:
1. **Feature evolution**: New phases/agents added over time
2. **Checkpoint backward compatibility**: Resume old workflows with new code
3. **Safe schema evolution**: Migrate checkpoints without data loss

**Versioning Pattern**: Semantic versioning in checkpoint JSON

### Implementation Pattern

```python
from typing import Union, Literal
from pydantic import BaseModel, field_validator
from datetime import datetime

# ============================================================
# VERSION-AWARE STATE MODELS
# ============================================================

class ACPStateV1(BaseModel):
    """Version 1: Initial checkpoint format (Phase 1)."""
    schema_version: Literal["1.0.0"] = "1.0.0"
    created_at: str  # ISO 8601 timestamp

    # Core fields from Phase 1
    constitution: str = ""
    governance_passes: bool = False
    feature_description: str = ""
    spec: str = ""
    clarifications: list = []
    plan: str = ""
    data_model: str = ""
    contracts: dict = {}
    tasks: list = []
    completed_tasks: list = []
    code_artifacts: dict = {}
    validation_status: str = "pending"
    phase: str = "init"


class ACPStateV2(BaseModel):
    """Version 2: Extended checkpoint format (Phase 2+)."""
    schema_version: Literal["2.0.0"] = "2.0.0"
    created_at: str
    updated_at: str  # NEW: Track last update

    # Phase 1 fields (all present)
    constitution: str = ""
    governance_passes: bool = False
    feature_description: str = ""
    spec: str = ""
    clarifications: list = []
    plan: str = ""
    data_model: str = ""
    contracts: dict = {}
    tasks: list = []
    completed_tasks: list = []
    code_artifacts: dict = {}
    validation_status: str = "pending"
    phase: str = "init"

    # NEW Phase 2 fields
    research: str = ""  # NEW: Research findings
    unknowns: list = []  # NEW: Open questions
    task_dependencies: dict = {}  # NEW: Dependency graph
    parallel_batches: list = []  # NEW: Parallel execution plan
    validation_report: dict = {}  # NEW: Detailed validation

    # Meta fields
    checkpoint_reason: str = "phase_complete"  # Why checkpoint was saved
    checkpoint_number: int = 0  # Sequence number for this feature


# ============================================================
# MIGRATION HANDLERS
# ============================================================

def migrate_checkpoint(old_data: dict, target_version: str) -> dict:
    """
    Migrate checkpoint from old format to new format.

    Args:
        old_data: Raw checkpoint dict with schema_version
        target_version: Target schema version (e.g., "2.0.0")

    Returns:
        Migrated checkpoint dict compatible with target version

    Raises:
        ValueError: If migration path not supported
    """
    current_version = old_data.get('schema_version', '1.0.0')

    # No migration needed
    if current_version == target_version:
        return old_data

    # Migration: 1.0.0 → 2.0.0
    if current_version == '1.0.0' and target_version == '2.0.0':
        return _migrate_v1_to_v2(old_data)

    # Future migrations: 2.0.0 → 3.0.0, etc.
    raise ValueError(
        f"No migration path from schema {current_version} to {target_version}"
    )


def _migrate_v1_to_v2(v1_data: dict) -> dict:
    """Migrate V1 checkpoint to V2 format."""
    v2_data = v1_data.copy()

    # Update schema version
    v2_data['schema_version'] = '2.0.0'

    # Add new V2 fields with defaults
    v2_data['updated_at'] = datetime.now().isoformat()
    v2_data['research'] = ''
    v2_data['unknowns'] = []
    v2_data['task_dependencies'] = {}
    v2_data['parallel_batches'] = []
    v2_data['validation_report'] = {}
    v2_data['checkpoint_reason'] = 'migrated_from_v1'
    v2_data['checkpoint_number'] = 0

    return v2_data


# ============================================================
# CHECKPOINT LOADING WITH AUTO-MIGRATION
# ============================================================

def load_checkpoint_with_migration(
    filepath: str,
    target_version: str = "2.0.0"
) -> ACPStateV2:
    """
    Load checkpoint, auto-migrate if needed, return latest schema.

    Args:
        filepath: Path to checkpoint JSON
        target_version: Target schema (defaults to latest)

    Returns:
        ACPStateV2 (or appropriate model for target_version)
    """
    import json

    # Load raw JSON
    with open(filepath, 'r') as f:
        raw_data = json.load(f)

    # Detect version and migrate if needed
    current_version = raw_data.get('schema_version', '1.0.0')

    if current_version != target_version:
        print(f"Migrating checkpoint from {current_version} to {target_version}...")
        raw_data = migrate_checkpoint(raw_data, target_version)

    # Validate against target schema
    if target_version == "2.0.0":
        return ACPStateV2(**raw_data)
    elif target_version == "1.0.0":
        return ACPStateV1(**raw_data)
    else:
        raise ValueError(f"Unknown target version: {target_version}")


# ============================================================
# CHECKPOINT SAVING WITH VERSION TRACKING
# ============================================================

def save_checkpoint(
    state: Union[ACPStateV1, ACPStateV2],
    filepath: str,
    checkpoint_reason: str = "phase_complete"
) -> None:
    """Save checkpoint with version metadata."""
    import json

    # Add metadata
    state_dict = state.model_dump()
    state_dict['created_at'] = datetime.now().isoformat()
    state_dict['checkpoint_reason'] = checkpoint_reason

    # Write with pretty formatting for version control readability
    with open(filepath, 'w') as f:
        json.dump(state_dict, f, indent=2)

    print(f"✓ Checkpoint saved (v{state.schema_version}): {filepath}")
```

### Backward Compatibility Strategy

**Principle**: New code must always read old checkpoints without data loss.

**Migration Rules**:

| Change Type | Example | Strategy |
|-------------|---------|----------|
| **New field** | Add `research: str` | Default to empty string/list; no data loss |
| **Renamed field** | `clarifications` → `clarification_list` | Create migration handler; preserve data |
| **Removed field** | Drop deprecated field | Migration handler logs warning; field ignored |
| **Type change** | `tasks: list` → `tasks: dict` | Conversion function during migration |
| **New phase** | Phase 2 adds "research" phase | New phase inserted into workflow; old checkpoints skip it |

**Example: Adding Research Phase (Phase 2)**

```python
# Phase 1 checkpoint
{
  "schema_version": "1.0.0",
  "phase": "plan",
  "plan": "...",
  "tasks": [...]
}

# Auto-migrated to Phase 2
{
  "schema_version": "2.0.0",
  "phase": "plan",  # Unchanged
  "plan": "...",    # Unchanged
  "tasks": [...],   # Unchanged
  "research": "",   # New field (empty, no data loss)
  "unknowns": [],   # New field (empty)
  "task_dependencies": {},  # New field (empty)
}
```

### Version Compatibility Matrix

| Current Code | V1 Checkpoint | V2 Checkpoint | V1.5 Checkpoint |
|--------------|---------------|---------------|-----------------|
| **V1 Code** | ✅ Native | ❌ Fails | ❌ Fails |
| **V2 Code** | ✅ Auto-migrates | ✅ Native | ✅ Auto-migrates |
| **V1.5 Code** | ✅ Native | ❌ Fails | ✅ Native |

### Best Practices for Schema Evolution

1. **Always Add, Never Remove**: Deprecated fields → default values
2. **Increment Minor Version** for new optional fields: `1.0.0` → `1.1.0`
3. **Increment Major Version** for breaking changes: `1.x.x` → `2.0.0`
4. **Migration Handler for Each Version Jump**: Ensures forward/backward compatibility
5. **Test Migration Path**: Before deploying new version, test loading old checkpoints
6. **Document Schema Changes**: Update `PYDANTIC_STATE_RESEARCH.md` with each version

### Checkpoint Metadata for Debugging

```python
class CheckpointMetadata(BaseModel):
    """Track checkpoint provenance for audit trails."""
    schema_version: str
    created_at: str  # ISO 8601
    updated_at: str
    checkpoint_reason: str  # e.g., "phase_complete", "manual_save", "error_recovery"
    checkpoint_number: int  # Sequential number for this feature
    acpctl_version: str  # Which acpctl version saved this
    python_version: str  # Python version for compatibility
    git_commit: str  # Optional: git SHA of acpctl codebase

    @field_validator('checkpoint_reason')
    @classmethod
    def validate_reason(cls, v: str) -> str:
        allowed = {
            'phase_complete', 'manual_save', 'error_recovery',
            'human_review', 'migrated_from_v1', 'migrated_from_v2'
        }
        if v not in allowed:
            raise ValueError(f"checkpoint_reason must be one of {allowed}")
        return v
```

---

## Integration with acpctl LangGraph Workflow

### Complete State Model Pattern for acpctl

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import TypedDict, List, Dict, Any, Annotated
from datetime import datetime

# ============================================================
# TypedDict FOR LANGGRAPH INTERNAL STATE
# ============================================================

class ACPState(TypedDict):
    """LangGraph state schema - used in graph.StateGraph()."""
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


# ============================================================
# PYDANTIC MODEL FOR CHECKPOINT I/O
# ============================================================

class ACPStateModel(BaseModel):
    """Pydantic model - used for validation and checkpoint serialization."""
    schema_version: str = "1.0.0"
    created_at: str = ""

    # Constitution layer
    constitution: str = ""
    governance_passes: bool = False

    # Specification layer
    feature_description: str = ""
    spec: str = ""
    clarifications: List[str] = []

    # Planning layer
    unknowns: List[str] = []
    research: str = ""
    plan: str = ""
    data_model: str = ""
    contracts: Dict[str, Any] = {}

    # Task/Implementation layers
    tasks: List[Dict[str, Any]] = []
    completed_tasks: List[str] = []
    code_artifacts: Dict[str, str] = {}
    validation_status: str = "pending"

    # Workflow control
    phase: str = "init"

    # [Include field_validator and model_validator methods from above]


# ============================================================
# CONVERSION FUNCTIONS FOR BOUNDARY CROSSING
# ============================================================

def typed_dict_to_pydantic(state: ACPState) -> ACPStateModel:
    """Convert TypedDict (from LangGraph) to Pydantic (for validation)."""
    return ACPStateModel(**state)


def pydantic_to_typed_dict(model: ACPStateModel) -> ACPState:
    """Convert Pydantic (after validation) to TypedDict (for LangGraph)."""
    return ACPState(**model.model_dump())


# ============================================================
# CHECKPOINT OPERATIONS
# ============================================================

def save_checkpoint(state: ACPState, filepath: str) -> None:
    """
    Workflow:
    1. TypedDict state → Pydantic model (validates)
    2. Pydantic model → JSON (serializes)
    3. JSON → File (persists)
    """
    validated = typed_dict_to_pydantic(state)
    json_data = validated.model_dump_json(mode='json', indent=2)

    with open(filepath, 'w') as f:
        f.write(json_data)


def load_checkpoint(filepath: str) -> ACPState:
    """
    Workflow:
    1. File → JSON (reads)
    2. JSON → Pydantic model (validates)
    3. Pydantic model → TypedDict state (converts)
    """
    with open(filepath, 'r') as f:
        json_data = f.read()

    validated = ACPStateModel.model_validate_json(json_data)
    return pydantic_to_typed_dict(validated)


# ============================================================
# USAGE IN LANGGRAPH NODES
# ============================================================

from langgraph.graph import StateGraph, START, END

# Create graph with TypedDict
workflow = StateGraph(ACPState)

def specification_node(state: ACPState) -> ACPState:
    """LangGraph node operates on TypedDict - zero validation overhead."""
    # Node receives TypedDict
    state['spec'] = "Generated specification..."
    state['phase'] = "plan"
    return state

def checkpoint_node(state: ACPState) -> ACPState:
    """Checkpoint node validates before saving."""
    # Validate before checkpointing
    try:
        save_checkpoint(state, ".acp/state/NNN-feature.json")
    except ValueError as e:
        # State transition violated invariant
        print(f"Checkpoint failed validation: {e}")
        state['validation_status'] = 'error'
    return state

workflow.add_node("specify", specification_node)
workflow.add_node("checkpoint", checkpoint_node)
workflow.add_edge(START, "specify")
workflow.add_edge("specify", "checkpoint")
workflow.add_edge("checkpoint", END)
```

---

## Practical Checklist for acpctl Implementation

### Phase 1 Implementation Checklist

- [ ] Define `ACPState` TypedDict in `src/state.py`
- [ ] Define `ACPStateModel` Pydantic in `src/models.py`
- [ ] Implement field validators for `clarifications`, `completed_tasks`, etc.
- [ ] Implement model validators for state transitions (init → specify → plan → implement)
- [ ] Add custom serializer for `contracts: dict` (handle polymorphic types)
- [ ] Create checkpoint save/load functions with proper error handling
- [ ] Add unit tests for state transitions:
  - [ ] Valid phase progression works
  - [ ] Invalid transitions raise `ValueError`
  - [ ] Checkpoint round-trip (save/load) preserves data
  - [ ] JSON serialization handles all field types
- [ ] Add integration tests:
  - [ ] Full workflow: init → specify → plan → implement → complete
  - [ ] Resume from each checkpoint
  - [ ] Corrupted checkpoint detection

### Phase 2 Implementation (When Adding New Features)

- [ ] Create `ACPStateV2` Pydantic model with new fields
- [ ] Implement `migrate_checkpoint(v1_data)` function
- [ ] Update version to `2.0.0` in checkpoint metadata
- [ ] Test backward compatibility:
  - [ ] V1 checkpoints load and migrate to V2
  - [ ] V2 code reads both V1 (migrated) and V2 checkpoints
  - [ ] No data loss during migration
- [ ] Document schema changes in this file

---

## Key Takeaways

1. **Hybrid TypedDict + Pydantic** is optimal for acpctl (performance + validation)
2. **Pydantic's `model_dump_json()` and `model_validate_json()`** handle checkpointing perfectly
3. **Model validators** enforce workflow invariants (can't skip phases)
4. **Field serializers** handle complex nested types like `contracts: dict`
5. **Version-aware checkpoints** enable safe schema evolution and backward compatibility
6. **Boundary conversion functions** keep LangGraph fast while maintaining safety

---

## References

- **Pydantic Docs**: https://docs.pydantic.dev/latest/concepts/serialization/
- **Pydantic Validators**: https://docs.pydantic.dev/latest/concepts/validators/
- **LangGraph State Management**: https://langchain-ai.github.io/langgraph/concepts/low_level_graph/
- **JSON Schema Versioning**: Confluent schema registry patterns for backward compatibility
- **acpctl Architecture**: `speckit-langgraph-architecture.md`

---

**Document Version**: 1.0.0
**Last Updated**: November 5, 2025
**Maintained By**: acpctl Design Phase
