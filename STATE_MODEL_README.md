# acpctl State Model Documentation

**Quick Navigation for State Architecture Research & Implementation**

---

## Research Deliverables

This directory contains comprehensive research on Pydantic best practices for acpctl's JSON-serializable, type-safe workflow state management. All documents are based on current Pydantic v2 and LangGraph patterns (November 2025).

### Core Documents

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[PYDANTIC_STATE_RESEARCH.md](PYDANTIC_STATE_RESEARCH.md)** | Comprehensive research with evidence-based recommendations | 45 min |
| **[STATE_ARCHITECTURE_DECISIONS.md](STATE_ARCHITECTURE_DECISIONS.md)** | Executive summary of decisions with visual diagrams | 15 min |
| **[STATE_IMPLEMENTATION_TEMPLATE.py](STATE_IMPLEMENTATION_TEMPLATE.py)** | Production-ready code templates for Phase 1 implementation | 30 min |

---

## Research Summary

### Research Questions Answered

#### 1. TypedDict vs Pydantic BaseModel for LangGraph

**Decision**: Hybrid layered approach
- **Inside LangGraph**: TypedDict (zero validation overhead per node)
- **Checkpoint boundaries**: Pydantic BaseModel (validation gates)
- **Serialization**: Pydantic's `model_dump_json()` for JSON checkpoints

**Why**: Balances LangGraph's performance requirements with enterprise-grade validation for persistent state.

#### 2. JSON Serialization for Checkpoint Files

**Decision**: Pydantic v2's `model_dump_json()` with field serializers

**Key Methods**:
```python
# Serialize with JSON compatibility
json_str = pydantic_model.model_dump_json(mode='json', indent=2)

# Deserialize with validation
validated = PydanticModel.model_validate_json(json_str)

# Handle complex types
@field_serializer('contracts', when_used='json')
def serialize_contracts(self, v: dict) -> dict:
    # Recursively convert non-JSON-serializable types
    ...
```

**Handles**:
- DateTime objects (auto-converts to ISO 8601)
- UUID fields (auto-converts to strings)
- Nested structures (lists, dicts)
- Polymorphic types (via `SerializeAsAny`)

#### 3. State Validation & Transitions

**Decision**: Pydantic model validators for workflow invariants

**Two Validator Types**:

1. **Field Validators** (individual constraints):
   ```python
   @field_validator('clarifications', mode='after')
   @classmethod
   def validate_clarifications(cls, v: List[str]) -> List[str]:
       # Must be non-empty strings
       ...
   ```

2. **Model Validators** (cross-field invariants):
   ```python
   @model_validator(mode='after')
   def validate_state_transitions(self) -> 'ACPStateModel':
       # Can't specify without constitution
       # Can't plan without specification
       # Can't implement without plan
       ...
   ```

**Enforces**:
- Phase progression rules (init → specify → plan → implement → complete)
- Constitutional governance gates
- Dependency constraints (task completion, etc.)

#### 4. Schema Versioning Strategy

**Decision**: Semantic versioning with auto-migration

**Pattern**:
- V1.0.0: Phase 1 core workflow (11 fields)
- V2.0.0: Phase 2+ enhancements (new fields, backward compatible)

**Migration Approach**:
```python
# Auto-migrate old checkpoints on load
def load_checkpoint_with_migration(filepath: str):
    raw_data = json.load(filepath)
    current_version = raw_data.get('schema_version', '1.0.0')

    if current_version == '1.0.0':
        raw_data = migrate_v1_to_v2(raw_data)

    return ACPStateModel.model_validate(raw_data)
```

**Guarantees**:
- New code reads old checkpoints seamlessly
- No data loss during migration
- Version tracking for audit trails

---

## Implementation Path

### Phase 1 (Ready to Implement)

1. **Create `src/state.py`** - Define TypedDict state schema
   - Reference: `STATE_IMPLEMENTATION_TEMPLATE.py` lines 45-94
   - Test: State structure matches all required fields

2. **Create `src/models.py`** - Define Pydantic model with validators
   - Reference: `STATE_IMPLEMENTATION_TEMPLATE.py` lines 97-350
   - Field validators: clarifications, completed_tasks
   - Model validators: state transitions, governance gates

3. **Create `src/checkpoint.py`** - Checkpoint save/load functions
   - Reference: `STATE_IMPLEMENTATION_TEMPLATE.py` lines 351-470
   - `save_checkpoint()`: TypedDict → JSON
   - `load_checkpoint()`: JSON → TypedDict
   - Error handling for corrupted checkpoints

4. **Create `tests/test_state_transitions.py`** - Workflow validation tests
   - Valid phase progressions work
   - Invalid transitions raise ValueError
   - All validator rules enforced

5. **Create `tests/test_checkpoint_roundtrip.py`** - Serialization tests
   - State → JSON → State preserves all fields
   - Complex types serialize correctly
   - Corrupted JSON detected on load

### Phase 2 (When Expanding Features)

1. Define `ACPStateV2` model
2. Implement `migrate_checkpoint_v1_to_v2()` handler
3. Update checkpoint loader with version detection
4. Test backward compatibility with Phase 1 checkpoints

---

## Code Patterns Quick Reference

### Pattern 1: Create & Validate State

```python
from src.models import ACPStateModel

# Create and validate
state = ACPStateModel(
    constitution="Our principles...",
    governance_passes=True,
    phase='init'
)
# Raises ValueError if invalid
```

### Pattern 2: State Transitions

```python
from src.models import transition_state, ACPStateModel

state = ACPStateModel(...)
state = transition_state(
    state,
    new_phase='specify',
    updates={
        'feature_description': 'Add OAuth2',
        'spec': '...'
    }
)
# Validates all transition invariants automatically
```

### Pattern 3: Save Checkpoint

```python
from src.checkpoint import save_checkpoint
from src.state import ACPState

# Inside LangGraph node, work with TypedDict
state: ACPState = {...}

# At checkpoint boundary
save_checkpoint(state, ".acp/state/001-oauth2.json")
# Automatically validates before saving
```

### Pattern 4: Load & Resume

```python
from src.checkpoint import load_checkpoint

state = load_checkpoint(".acp/state/001-oauth2.json")
# Auto-migrates if needed, validates during load
# Returns TypedDict ready for LangGraph
```

### Pattern 5: Handle Complex Fields

```python
from pydantic import field_serializer

class ACPStateModel(BaseModel):
    contracts: Dict[str, Any]

    @field_serializer('contracts', when_used='json')
    def serialize_contracts(self, v: dict) -> dict:
        # Recursively convert non-JSON-serializable types
        def make_safe(obj):
            if isinstance(obj, dict):
                return {k: make_safe(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [make_safe(item) for item in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                return str(obj)
        return make_safe(v)
```

---

## Architecture Overview

```
LangGraph Workflow (Fast)
    ↓ TypedDict
    ├─ Specification Node
    ├─ Architecture Node
    ├─ Implementation Node
    ↓
Checkpoint Boundary (Validation Gate)
    ├─ TypedDict → Pydantic (validates)
    ├─ Field validators (individual constraints)
    ├─ Model validators (workflow invariants)
    └─ Raises ValueError if invalid
    ↓
Checkpoint Storage (Persistent)
    ├─ Pydantic → JSON (serializes with mode='json')
    ├─ File I/O (.acp/state/NNN-feature.json)
    └─ Auto-migration on load (V1→V2)
```

---

## Validation Checklist for State Changes

- [ ] State implements required fields from ACPState TypedDict
- [ ] Pydantic model has corresponding fields with defaults
- [ ] Field validators defined for constraint validation
- [ ] Model validators enforce workflow invariants
- [ ] Complex fields have custom serializers
- [ ] Checkpoint save/load functions work end-to-end
- [ ] Invalid state transitions raise ValueError
- [ ] JSON round-trip preserves all data
- [ ] Corrupted JSON detected on load
- [ ] Unit tests pass (state transitions, serialization)
- [ ] Integration tests pass (full workflow: init→specify→plan→implement)

---

## Key Design Principles

1. **TypedDict for Speed**: LangGraph nodes work on TypedDict (zero overhead)
2. **Pydantic for Safety**: Boundaries validated via Pydantic (checkpoint I/O)
3. **JSON as Lingua Franca**: All checkpoint files are plain JSON (version-control-friendly)
4. **Validate Transitions**: Model validators enforce workflow invariants
5. **Serialize Everything**: `mode='json'` ensures full JSON compatibility
6. **Version Seamlessly**: Auto-migration handles schema evolution
7. **Audit Trail**: Checkpoint metadata tracks provenance and versions

---

## Common Questions

### Q: Why TypedDict inside LangGraph?
**A**: Zero validation overhead per node execution. Validation happens once at checkpoint boundaries, not per-node.

### Q: Why Pydantic at boundaries?
**A**: Runtime validation catches corrupted checkpoints early. Protects against file corruption, version mismatches, and invalid state transitions.

### Q: What if I add a new field to state?
**A**: Add to both TypedDict (in `src/state.py`) and Pydantic model (in `src/models.py`). For Phase 1→2 transitions, increment version and create migration handler.

### Q: Can old checkpoints be loaded by new code?
**A**: Yes. The `load_checkpoint_with_migration()` function auto-detects version and migrates if needed.

### Q: Can new checkpoints be loaded by old code?
**A**: Only if schema is backward compatible (new fields are optional with defaults). Major schema changes require users to update code.

### Q: How do I validate state transitions?
**A**: Use `transition_state()` function which runs all validators. Or create state with new values—validators raise ValueError if invariants violated.

---

## Performance Notes

| Operation | Complexity | Expected Time |
|-----------|-----------|----------------|
| Node execution (TypedDict) | O(1) | <1ms |
| Checkpoint save | O(n) fields | <10ms |
| Checkpoint load | O(n) fields + validation | <50ms |
| State transition | O(n) validators | <5ms |

**Key insight**: LangGraph nodes are fast because they use TypedDict. Validation only at checkpoint boundaries.

---

## Research Sources

- **Pydantic v2 Docs**: https://docs.pydantic.dev/latest/concepts/serialization/
- **Pydantic Validators**: https://docs.pydantic.dev/latest/concepts/validators/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **JSON Schema Versioning**: Confluent Schema Registry patterns
- **acpctl Architecture**: `speckit-langgraph-architecture.md`

---

## Next Steps

1. **Review** `PYDANTIC_STATE_RESEARCH.md` for detailed patterns (45 min)
2. **Review** `STATE_ARCHITECTURE_DECISIONS.md` for decision rationale (15 min)
3. **Reference** `STATE_IMPLEMENTATION_TEMPLATE.py` during implementation (copy patterns)
4. **Implement** Phase 1 state model using templates (see "Implementation Path")
5. **Test** checkpoint round-trip and state transitions
6. **Document** any custom validators or serializers

---

## Files in This Research Package

```
/workspace/sessions/agentic-session-1762315841/workspace/acpctl/
├── PYDANTIC_STATE_RESEARCH.md              [31 KB] Full research with examples
├── STATE_ARCHITECTURE_DECISIONS.md         [12 KB] Executive summary & diagrams
├── STATE_IMPLEMENTATION_TEMPLATE.py        [20 KB] Ready-to-use code patterns
├── STATE_MODEL_README.md                   [THIS FILE] Navigation & quick ref
└── speckit-langgraph-architecture.md       [Context] Overall system design
```

---

**Research Completed**: November 5, 2025
**Status**: Ready for Phase 1 Implementation
**Quality**: Evidence-based recommendations from Pydantic v2 & LangGraph best practices
