# Phase 0 Research: acpctl Technical Decisions

**Feature**: Governed Spec-Driven Development CLI
**Date**: 2025-11-05
**Status**: Complete

This document consolidates all technical research decisions for implementing acpctl's Phase 1 architecture.

---

## 1. LangGraph State Management & Checkpointing

### Decision
Use **SqliteSaver with AsyncSqliteSaver** for local development and testing; **PostgresSaver** for production with connection pooling.

### Rationale
- LangGraph automatically saves state snapshots at every super-step, eliminating manual checkpoint logic
- Thread IDs uniquely identify workflow runs and organize all checkpoints under that logical execution context
- SqliteSaver is ideal for local development; Postgres scales to production with proper connection pooling
- Checkpointing provides automatic fault tolerance: if a node fails, restart from last successful step without re-running completed nodes

### Implementation Pattern
```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

# Development
checkpointer = SqliteSaver(conn=db_connection)

# Compile with checkpointer
graph = builder.compile(checkpointer=checkpointer)

# Execute with thread_id for persistence
graph.invoke(
    initial_state,
    config={"configurable": {"thread_id": thread_id}}
)
```

### Alternatives Considered
- **InMemorySaver**: Too ephemeral; loses state on process restart (rejected for CLI persistence requirement)
- **Manual JSON serialization**: Reinvents the wheel; LangGraph's built-in serialization handles edge cases (pickle fallback for unsupported types)
- **Custom database**: Higher maintenance; LangGraph's JsonPlusSerializer handles cross-session serialization via ormsgpack and JSON

---

## 2. Agent Orchestration & Governance Gates

### Decision
Use **conditional edges with routing functions** as governance gates. Structure as:
1. **Agent nodes** (Governance, Specification, Architect, Implementation) - do the work
2. **Routing nodes** (validation gates) - evaluate state and conditionally route to next phase or error handler

### Rationale
- Conditional edges (with routing functions returning string paths) are LangGraph's native pattern for dynamic control flow
- Separates validation logic from agent logic (single responsibility)
- Gates enable interactive prompts: `[R]egenerate`, `[E]dit constitution`, `[A]bort`, `[I]gnore --force`
- Scales naturally: add new gates without graph restructuring
- Constitutional violations route to error_handler, not silent failures

### Implementation Pattern
```python
from typing import Literal
from langgraph.graph import StateGraph, END

def route_governance(state: ACPState) -> Literal["governance_pass", "governance_fail"]:
    """Gate: evaluate constitution violations"""
    if state.get("governance_passes"):
        return "governance_pass"
    return "governance_fail"

# Build graph
builder = StateGraph(ACPState)
builder.add_node("governance_agent", governance_node)
builder.add_node("governance_gate", route_governance)
builder.add_node("error_handler", handle_governance_error)

# Routing edges
builder.add_edge("governance_agent", "governance_gate")
builder.add_conditional_edges(
    "governance_gate",
    lambda state: route_governance(state),
    {
        "governance_pass": "specification_agent",
        "governance_fail": "error_handler"
    }
)
```

### Alternatives Considered
- **Try/catch in nodes**: Mixes concerns; error handling logic scattered; harder to test (rejected)
- **Separate graph for validation**: Over-engineered; LangGraph's conditional edges are designed for this (rejected)
- **Supervised agent pattern**: Over-verbose for sequential workflow; saves supervisor overhead for parallel agents (rejected)

---

## 3. Error Handling & Resume Strategy

### Decision
Implement **multi-level error handling** with:
1. **Node-level**: Try/catch within nodes, record error state, return special state value
2. **Graph-level**: Conditional edges route errors to retry/escalation logic
3. **Cross-session**: LangGraph's checkpoint recovery + explicit error state for user-facing reporting

### Rationale
- LangGraph's checkpoint system automatically handles node failures: pending writes from successful nodes are preserved; restart from last successful step
- Error state in TypedDict enables conditional routing and user-facing error reporting
- Retry logic at graph level (conditional edge re-routes to same node) rather than within node (cleaner separation)
- Explicit error_count prevents infinite retries
- Escalation path (retry → error handler) after max attempts

### Implementation Pattern
```python
class ACPState(TypedDict):
    error: Optional[Dict[str, Any]]  # { "node": str, "message": str, "count": int }
    error_count: int

def governance_node(state: ACPState) -> Dict:
    try:
        violations = check_constitution(state["constitution"])
        return {
            "governance_passes": len(violations) == 0,
            "violations": violations,
            "error": None
        }
    except Exception as e:
        return {
            "error": {
                "node": "governance_agent",
                "message": str(e),
                "count": state.get("error_count", 0) + 1
            },
            "error_count": state.get("error_count", 0) + 1
        }

def route_with_retry(state: ACPState) -> Literal["pass", "retry", "error"]:
    if state.get("error_count", 0) >= 3:
        return "error"  # Escalate after 3 retries
    if state.get("error"):
        return "retry"  # Attempt retry
    return "pass"  # Success
```

### Alternatives Considered
- **Unbounded retries**: Infinite loops possible; obscures user feedback (rejected)
- **Ignore errors silently**: Violates governance principles; corrupts downstream artifacts (rejected)

---

## 4. CLI Framework Choice

### Decision
**Typer** (with Click as the underlying foundation)

### Rationale
- **Native Async Support**: Critical for LangGraph agent execution and checkpoint operations
- **Modern Type Hints Integration**: Reduces boilerplate, improves maintainability
- **Deep Rich Integration**: Pre-configured with Rich for output formatting
- **Future-Proof**: Standard for modern Python developer tools with AI/LLM workflows
- **Smaller Learning Curve**: Built on Click but cleaner API

### Implementation Notes
```python
import typer
from rich.console import Console

app = typer.Typer()

@app.command()
def specify(
    description: str = typer.Argument(..., help="Feature description"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
):
    """Generate spec with pre-flight Q&A."""
    console = Console(quiet=quiet)
    console.print("Starting specification phase...")
```

### Alternatives Considered
- **Click**: Mature but lacks async support (rejected)
- **argparse**: Too verbose, outdated patterns (rejected)
- **Plac**: Too simple for acpctl's complexity (rejected)

---

## 5. Rich Terminal UI Architecture

### Decision
Use Rich's `Progress`, `Console`, and `Live` APIs with conditional rendering based on verbosity level.

### Rationale
- **Streaming Integration**: LangGraph's `.astream_events()` + Rich's `Live` enables real-time display
- **Multi-Phase Progress Tracking**: Maps directly to acpctl's workflow phases
- **Conditional Output**: Rich's `Console` supports quiet/verbose modes without code duplication

### Key Components
- **`Progress`**: Multi-task progress tracking for workflow phases
- **`Spinner` + `TextColumn`**: Show "Governance phase... [✓]" status
- **`Console`**: Central output manager with verbosity support
- **`Live`**: Real-time display of streaming agent events
- **`Table`**: Structured display of verbose agent reasoning
- **`Panel`**: Highlight constitutional violations with fix suggestions

### Implementation Pattern
```python
from rich.console import Console
from rich.progress import Progress

console = Console(quiet=args.quiet)
progress = Progress(console=console, transient=True)

with progress:
    task = progress.add_task("[cyan]Governance...", total=None)
    for event in graph.astream_events(...):
        progress.update(task, description=f"[cyan]{event['node']}...")
        if args.verbose:
            console.print(event)  # Detailed output
    progress.update(task, completed=100, description="[green]✓ Complete")
```

---

## 6. Verbosity Mode Implementation

### Decision
Centralized `Config` class with `console_level: Literal["quiet", "default", "verbose"]`, propagated through Typer's dependency injection.

### Rationale
- **Single Source of Truth**: Consistent behavior across agents
- **Non-Invasive**: Code doesn't know about CLI flags
- **Typer Dependency Injection**: Automatic config object injection
- **Rich Integration**: Console directly respects verbosity

### Implementation Pattern
```python
from enum import Enum
import typer

class ConsoleLevel(str, Enum):
    QUIET = "quiet"
    DEFAULT = "default"
    VERBOSE = "verbose"

class Config:
    def __init__(self, level: ConsoleLevel):
        self.console_level = level
        self.console = Console(quiet=(level == ConsoleLevel.QUIET))

    def log_agent_step(self, node: str, data: dict):
        if self.console_level == ConsoleLevel.VERBOSE:
            self.console.print(f"[dim]{node}[/dim]: {data}")

def get_config(
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
) -> Config:
    if quiet:
        level = ConsoleLevel.QUIET
    elif verbose:
        level = ConsoleLevel.VERBOSE
    else:
        level = ConsoleLevel.DEFAULT
    return Config(level)

@app.command()
def specify(
    description: str,
    config: Config = typer.Depends(get_config),
):
    config.console.print("Starting specification...")
    config.log_agent_step("Specification Agent", {"phase": "analysis"})
```

---

## 7. Pydantic State Model Architecture

### Decision
**Hybrid TypedDict + Pydantic BaseModel** approach:
- TypedDict for LangGraph internal state (zero validation overhead per node)
- Pydantic BaseModel at checkpoint boundaries (validation gates for persistence)

### Rationale
- Fast graph execution (no validation on every node transition)
- Safe checkpoint persistence (validation catches corruption on load)
- Best of both worlds: performance + reliability

### Implementation Pattern
```python
from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator

# LangGraph internal state (TypedDict)
class ACPState(TypedDict):
    constitution: str
    governance_passes: bool
    feature_description: str
    spec: str
    clarifications: List[str]
    plan: str
    data_model: str
    contracts: Dict[str, Any]
    tasks: List[Dict[str, Any]]
    completed_tasks: List[str]
    code_artifacts: Dict[str, str]
    validation_status: str
    error: Optional[Dict[str, Any]]
    error_count: int

# Checkpoint validation (Pydantic)
class ACPStateModel(BaseModel):
    constitution: str = Field(..., min_length=1)
    governance_passes: bool = False
    feature_description: str = ""
    spec: str = ""
    clarifications: List[str] = Field(default_factory=list)
    plan: str = ""
    data_model: str = ""
    contracts: Dict[str, Any] = Field(default_factory=dict)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    code_artifacts: Dict[str, str] = Field(default_factory=dict)
    validation_status: str = "PENDING"
    error: Optional[Dict[str, Any]] = None
    error_count: int = 0

    @model_validator(mode='after')
    def validate_state_transitions(self) -> 'ACPStateModel':
        # Can't specify without governance passing
        if self.spec and not self.governance_passes:
            raise ValueError("Cannot specify without passing governance")
        # Can't plan without spec
        if self.plan and not self.spec:
            raise ValueError("Cannot plan without specification")
        return self

# Save checkpoint: TypedDict → Pydantic → JSON
def save_checkpoint(state: ACPState, path: Path):
    validated = ACPStateModel(**state)
    json_data = validated.model_dump_json(mode='json', indent=2)
    path.write_text(json_data)

# Load checkpoint: JSON → Pydantic → TypedDict
def load_checkpoint(path: Path) -> ACPState:
    validated = ACPStateModel.model_validate_json(path.read_text())
    return ACPState(**validated.model_dump())
```

### Alternatives Considered
- **Pure Pydantic**: Too much validation overhead on every node (rejected)
- **Pure TypedDict**: No validation on checkpoint load → silent failures (rejected)

---

## 8. Schema Versioning Strategy

### Decision
Semantic versioning with auto-migration on checkpoint load.

### Rationale
- V1.0.0 covers Phase 1 core workflow
- V2.0.0+ adds new fields (backward compatible)
- Old checkpoints work with new code (no data loss)

### Implementation Pattern
```python
class ACPStateModel(BaseModel):
    schema_version: str = Field(default="1.0.0")
    # ... other fields

def load_checkpoint_with_migration(path: Path) -> ACPState:
    data = json.loads(path.read_text())
    version = data.get("schema_version", "1.0.0")

    if version == "1.0.0" and CURRENT_VERSION == "2.0.0":
        data = migrate_v1_to_v2(data)

    validated = ACPStateModel.model_validate(data)
    return ACPState(**validated.model_dump())

def migrate_v1_to_v2(v1_data: dict) -> dict:
    v2_data = v1_data.copy()
    v2_data['schema_version'] = '2.0.0'
    v2_data['research'] = ''  # New field (empty default)
    return v2_data
```

---

## 9. CLI Command Structure

### Decision
Subcommands for main phases with global flags.

### Rationale
- Mirrors spec-kit familiarity (reduces migration friction)
- Atomic state transitions per command (clean checkpointing)
- Clear separation of concerns per phase

### Command Structure
```bash
acpctl [GLOBAL_FLAGS] COMMAND [ARGS]

Global flags:
  --verbose, -v              Verbose output
  --quiet, -q                Quiet output (errors only)

Subcommands:
  init                       Initialize .acp/ with constitution
  specify <description>      Generate spec.md with pre-flight Q&A
  plan                       Generate plan.md and contracts/
  implement                  Generate code via TDD
  status [SPEC_ID]           Show workflow progress
  resume [SPEC_ID]           Resume from checkpoint
  history                    List all workflows
```

---

## 10. CLI State Management for Resume

### Decision
Combine **LangGraph thread_id for execution checkpointing** with **explicit state snapshots in `.acp/state/` for CLI metadata**.

### Rationale
- LangGraph manages execution recovery via thread_id
- CLI metadata provides human-readable workflow history
- Users run `acpctl resume feature-001` without specifying thread_id

### Implementation Pattern
```python
# .acp/state/001-feature.json
{
  "feature_id": "001-feature",
  "thread_id": "acpctl-001-20250105-120000",
  "created_at": "2025-01-05T12:00:00Z",
  "last_checkpoint": "specification_complete",
  "status": "PAUSED",
  "phases_completed": ["INIT", "SPECIFICATION"],
  "next_phase": "PLANNING"
}

# Resume workflow
def resume_workflow(feature_id: str):
    metadata = json.loads(Path(f".acp/state/{feature_id}.json").read_text())
    thread_id = metadata["thread_id"]

    checkpointer = SqliteSaver(...)
    graph = build_acpctl_graph(checkpointer=checkpointer)

    # LangGraph handles resumption
    final_state = graph.invoke(
        {},
        config={"configurable": {"thread_id": thread_id}}
    )

    # Update CLI metadata
    metadata["status"] = "COMPLETED"
    Path(f".acp/state/{feature_id}.json").write_text(json.dumps(metadata, indent=2))
```

---

## Implementation Priorities for Phase 1

### Month 1: Core Infrastructure
**Weeks 1-2**: Setup
- Typer app structure with `get_config()` dependency injection
- Implement verbosity flags with Rich Console
- LangGraph StateGraph with SqliteSaver checkpointing

**Weeks 3-4**: First Command
- Implement `acpctl init` (constitution template creation)
- Verify checkpoint save/restore
- Unit tests for state models

### Month 2: Agent Workflow
**Weeks 1-2**: Governance & Specification Agents
- Governance agent with constitutional validation
- Specification agent with pre-flight Q&A
- Constitutional gates with conditional edges

**Weeks 3-4**: Planning & Implementation Agents
- Architect agent (plan.md generation)
- Implementation agent (TDD code generation)
- Error handling and retry logic

### Month 3: UX & Polish
**Weeks 1-2**: Rich Terminal UI
- Streaming display for phases (Progress, Spinner, Live)
- Verbose mode agent reasoning tables
- Constitutional violation panels

**Weeks 3-4**: Resume & Status
- `acpctl status` command
- `acpctl resume` command
- `acpctl history` command
- Integration tests for full workflow

---

## Validation Criteria

Phase 1 research is complete when:
- ✅ All technical decisions documented with rationale
- ✅ Implementation patterns provided with code examples
- ✅ Alternatives considered and rejected with reasoning
- ✅ Constitutional principles validated against decisions
- ✅ No blocking unknowns or "NEEDS CLARIFICATION" items remaining

**Status**: ✅ **COMPLETE** - All research questions resolved. Ready for Phase 1 design artifacts.
