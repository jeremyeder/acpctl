# acpctl State Architecture: Decision Summary

**Quick Reference for State Model Design**

---

## Executive Decisions

### 1. State Model Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ LangGraph Workflow (Fast Path)                              │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ TypedDict ACPState                                   │  │
│  │ ├─ constitution: str                                │  │
│  │ ├─ spec: str                                        │  │
│  │ ├─ plan: str                                        │  │
│  │ └─ ... (zero validation overhead)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│           │                                                 │
│           ├─ Specification Node                            │
│           ├─ Architecture Node                             │
│           └─ Implementation Node                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
           ↓ (at checkpoint boundaries)
┌─────────────────────────────────────────────────────────────┐
│ Checkpoint Boundary (Validation Gate)                       │
│                                                             │
│  ACPStateModel.model_validate(**typed_dict_state)          │
│  - Field validators check individual constraints          │
│  - Model validators check state transitions               │
│  - Raises ValueError if invariants violated               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
           ↓ (if validated)
┌─────────────────────────────────────────────────────────────┐
│ Checkpoint Storage (Persistent)                            │
│                                                             │
│  state.model_dump_json(mode='json')                        │
│  → `.acp/state/NNN-feature.json`                           │
│                                                             │
│  On Resume:                                                │
│  model_validate_json(json_data)                            │
│  → TypedDict for LangGraph                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Why**: Performance inside graph (TypedDict) + Validation at boundaries (Pydantic)

---

### 2. JSON Serialization

| Requirement | Solution | Code |
|-------------|----------|------|
| **DateTime handling** | Pydantic auto-converts | `model_dump_json()` |
| **Nested structures** | Custom serializers | `@field_serializer` |
| **Complex dicts** | Recursive conversion | Contracts serializer |
| **Type validation** | `mode='json'` parameter | `model_dump(mode='json')` |

**Key Method**: `model_dump_json(mode='json', indent=2)`

---

### 3. State Transitions & Validation

```
Workflow Phase Progression:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

init
  │
  ├─ [Model Validator: Need constitution + governance_passes]
  │
  ↓
specify (feature_description, spec, clarifications)
  │
  ├─ [Model Validator: Need spec + feature_description]
  │
  ↓
plan (plan, data_model, contracts)
  │
  ├─ [Model Validator: Need plan + data_model]
  │
  ↓
implement (executing tasks)
  │
  ├─ [Model Validator: All tasks must be completed]
  │
  ↓
complete (workflow done)
```

**Validator Types Used**:
- **Field Validators** (After mode): Check individual field constraints
  - `clarifications`: Must be non-empty strings
  - `completed_tasks`: Must exist in tasks list

- **Model Validators** (After mode): Check workflow invariants
  - Can't specify without constitution
  - Can't implement without plan
  - Can't complete without all tasks done

---

### 4. Schema Versioning

```
Phase 1: Schema Version 1.0.0
  ├─ Core workflow state
  ├─ Constitution, Specification, Planning, Implementation layers
  └─ 11 core fields

Phase 2: Schema Version 2.0.0 (backward compatible)
  ├─ All Phase 1 fields (unchanged)
  ├─ New fields: research, unknowns, task_dependencies, parallel_batches
  ├─ Auto-migration: v1→v2
  └─ Old checkpoints load seamlessly
```

**Strategy**: Add new optional fields with defaults (no breaking changes)

---

## Implementation Patterns

### Pattern 1: Save Checkpoint

```python
def save_checkpoint(state: ACPState, filepath: str) -> None:
    # TypedDict → Pydantic (validates)
    validated = ACPStateModel(**state)

    # Pydantic → JSON (serializes)
    json_data = validated.model_dump_json(mode='json', indent=2)

    # JSON → File (persists)
    with open(filepath, 'w') as f:
        f.write(json_data)
```

### Pattern 2: Load Checkpoint

```python
def load_checkpoint(filepath: str) -> ACPState:
    # File → JSON (reads)
    with open(filepath, 'r') as f:
        json_data = f.read()

    # JSON → Pydantic (validates + auto-migrates if needed)
    validated = ACPStateModel.model_validate_json(json_data)

    # Pydantic → TypedDict (for LangGraph)
    return ACPState(**validated.model_dump())
```

### Pattern 3: Validate State Transition

```python
def transition_state(
    state: ACPStateModel,
    new_phase: str,
    updates: Dict[str, Any]
) -> ACPStateModel:
    # Update fields
    new_dict = state.model_dump()
    new_dict.update(updates)
    new_dict['phase'] = new_phase

    # Validation happens here (raises ValueError if invariants violated)
    new_state = ACPStateModel(**new_dict)
    return new_state
```

---

## Decision Matrix

| Decision | Choice | Rationale | Alternative |
|----------|--------|-----------|-------------|
| **LangGraph State** | TypedDict | Zero overhead, native support | Pydantic (slower) |
| **Checkpoint I/O** | Pydantic BaseModel | Validation at boundaries | JSONSchema (less type-safe) |
| **Serialization** | `model_dump_json()` | Built-in JSON support | Custom encoder (more code) |
| **Validators** | Pydantic (after mode) | Type-safe, composable | Before mode (edge cases) |
| **Versioning** | Semantic with migration | Backward compatible | Ad-hoc (fragile) |

---

## Common Implementation Tasks

### Task 1: Add New Field to State

1. Add to TypedDict:
   ```python
   class ACPState(TypedDict):
       new_field: str = ""  # Default value
   ```

2. Add to Pydantic:
   ```python
   class ACPStateModel(BaseModel):
       new_field: str = ""
   ```

3. If Phase 1→2 schema change:
   - Increment version: `1.0.0` → `2.0.0`
   - Add migration handler
   - Test backward compatibility

### Task 2: Add Validation Rule

1. Field-level (single field):
   ```python
   @field_validator('new_field')
   @classmethod
   def validate_new_field(cls, v: str) -> str:
       if not v or v.strip() == '':
           raise ValueError("new_field cannot be empty")
       return v
   ```

2. Model-level (cross-field invariants):
   ```python
   @model_validator(mode='after')
   def validate_new_constraint(self) -> 'ACPStateModel':
       if self.new_field and not self.existing_field:
           raise ValueError("new_field requires existing_field")
       return self
   ```

### Task 3: Handle Complex Type (e.g., contracts dict)

```python
@field_serializer('contracts', when_used='json')
def serialize_contracts(self, v: dict) -> dict:
    def make_serializable(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)  # Fallback: stringify unknown types

    return make_serializable(v)
```

---

## Validation Checklist for Checkpoint Round-Trip

```python
# Test: State → JSON → State preserves all data

def test_checkpoint_roundtrip():
    # 1. Create valid state
    state = ACPState(
        constitution="...",
        governance_passes=True,
        phase="specify"
    )

    # 2. Save to checkpoint
    save_checkpoint(state, "test.json")

    # 3. Load from checkpoint
    loaded = load_checkpoint("test.json")

    # 4. Verify all fields match
    assert loaded['constitution'] == state['constitution']
    assert loaded['phase'] == state['phase']
    assert loaded == state

    # 5. Verify invalid transitions still caught
    with pytest.raises(ValueError):
        # Try to transition to 'plan' without spec
        bad_state = loaded.copy()
        bad_state['phase'] = 'plan'
        ACPStateModel(**bad_state)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `src/state.py` | TypedDict definition (for LangGraph) |
| `src/models.py` | Pydantic models + validators |
| `src/checkpoint.py` | save/load checkpoint functions |
| `src/migrations.py` | Version migration handlers |
| `tests/test_state_transitions.py` | Workflow validation tests |
| `tests/test_checkpoint_roundtrip.py` | Serialization tests |

---

## Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| **Node execution** (TypedDict) | O(1) | No validation per node |
| **Checkpoint save** | O(n) | Where n = state fields |
| **Checkpoint load** | O(n) | Includes validation |
| **State transition** | O(n) | All validators run |
| **JSON serialization** | O(n) | Recursive for nested types |

**Expected**: <1ms per node execution, <10ms per checkpoint operation

---

## Status: Ready for Implementation

- [x] Research complete
- [x] Decision matrix finalized
- [x] Code patterns documented
- [x] Migration strategy designed
- [ ] Implementation Phase 1
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance benchmarking

See `PYDANTIC_STATE_RESEARCH.md` for detailed patterns and examples.

