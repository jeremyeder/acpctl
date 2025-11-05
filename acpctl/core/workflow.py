"""
acpctl Workflow Orchestration

Manages LangGraph StateGraph workflow for acpctl agent orchestration.
Handles workflow creation, node registration, and checkpoint management.

Workflow Architecture:
- StateGraph with ACPState schema
- SqliteSaver for persistent checkpointing
- Thread-based workflow tracking
- Conditional routing for governance gates and phase transitions

Reference: speckit-langgraph-architecture.md, PYDANTIC_STATE_RESEARCH.md
"""

import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from acpctl.core.state import ACPState

# Note: LangGraph 1.0.2 uses MemorySaver for checkpointing.
# For persistent storage across process restarts, we use our own
# JSON checkpoint files in acpctl.core.checkpoint module.


# ============================================================
# WORKFLOW BUILDER
# ============================================================


class WorkflowBuilder:
    """
    Builder for creating LangGraph StateGraph workflows.

    Provides fluent interface for workflow construction with built-in
    checkpointing support via MemorySaver.

    Note: LangGraph's MemorySaver provides in-memory checkpointing for
    workflow interruption/resumption within a single process. For persistent
    checkpoints across process restarts, use acpctl.core.checkpoint module.

    Example:
        >>> builder = WorkflowBuilder()
        >>> builder.add_node("specify", specification_agent)
        >>> builder.add_node("governance", governance_agent)
        >>> builder.add_edge(START, "specify")
        >>> builder.add_conditional_edges("specify", route_governance)
        >>> workflow = builder.compile()
    """

    def __init__(self, use_checkpointer: bool = True):
        """
        Initialize workflow builder.

        Args:
            use_checkpointer: If True, enable in-memory checkpointing
        """
        # Create StateGraph with ACPState schema
        self.graph = StateGraph(ACPState)

        # Setup in-memory checkpointer
        self.checkpointer = MemorySaver() if use_checkpointer else None

        # Track nodes for validation
        self._nodes: set[str] = set()

    def add_node(
        self, name: str, node_function: Callable[[ACPState], ACPState]
    ) -> "WorkflowBuilder":
        """
        Add node to workflow graph.

        Args:
            name: Node name (must be unique)
            node_function: Function that processes state (signature: ACPState -> ACPState)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If node name already exists

        Example:
            >>> builder.add_node("specify", specification_agent)
        """
        if name in self._nodes:
            raise ValueError(f"Node '{name}' already exists")

        self.graph.add_node(name, node_function)
        self._nodes.add(name)

        return self

    def add_edge(self, from_node: str, to_node: str) -> "WorkflowBuilder":
        """
        Add directed edge between nodes.

        Args:
            from_node: Source node (or START constant)
            to_node: Target node (or END constant)

        Returns:
            Self for method chaining

        Example:
            >>> builder.add_edge(START, "specify")
            >>> builder.add_edge("specify", "governance")
        """
        self.graph.add_edge(from_node, to_node)
        return self

    def add_conditional_edges(
        self,
        source: str,
        path_function: Callable[[ACPState], str],
        path_map: Optional[Dict[str, str]] = None,
    ) -> "WorkflowBuilder":
        """
        Add conditional edges based on state.

        Args:
            source: Source node
            path_function: Function that returns next node name based on state
            path_map: Optional mapping of path_function returns to node names

        Returns:
            Self for method chaining

        Example:
            >>> def route_governance(state: ACPState) -> str:
            ...     return "passed" if state['governance_passes'] else "failed"
            >>> builder.add_conditional_edges(
            ...     "governance",
            ...     route_governance,
            ...     {"passed": "plan", "failed": "error_handler"}
            ... )
        """
        self.graph.add_conditional_edges(source, path_function, path_map)
        return self

    def set_entry_point(self, node: str) -> "WorkflowBuilder":
        """
        Set workflow entry point.

        Args:
            node: Entry node name

        Returns:
            Self for method chaining

        Example:
            >>> builder.set_entry_point("specify")
        """
        self.graph.set_entry_point(node)
        return self

    def compile(self) -> "CompiledWorkflow":
        """
        Compile workflow graph into executable workflow.

        Returns:
            CompiledWorkflow ready for execution

        Example:
            >>> workflow = builder.compile()
            >>> result = workflow.run(initial_state)
        """
        compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
        return CompiledWorkflow(compiled_graph, self.checkpointer)


# ============================================================
# COMPILED WORKFLOW
# ============================================================


class CompiledWorkflow:
    """
    Compiled LangGraph workflow with checkpoint support.

    Wraps compiled StateGraph and provides high-level execution interface
    with thread management and checkpoint tracking.
    """

    def __init__(self, compiled_graph: Any, checkpointer: Optional[MemorySaver]):
        """
        Initialize compiled workflow.

        Args:
            compiled_graph: Compiled LangGraph StateGraph
            checkpointer: MemorySaver instance for in-memory checkpointing
        """
        self.graph = compiled_graph
        self.checkpointer = checkpointer

    def run(
        self,
        initial_state: ACPState,
        thread_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> ACPState:
        """
        Execute workflow from start to completion.

        Args:
            initial_state: Initial workflow state
            thread_id: Thread ID for checkpoint tracking (generates new if None)
            config: Optional LangGraph config overrides

        Returns:
            Final workflow state

        Example:
            >>> state = workflow.run(initial_state, thread_id="abc123")
        """
        if thread_id is None:
            thread_id = generate_thread_id()

        if config is None:
            config = {}

        config["configurable"] = config.get("configurable", {})
        config["configurable"]["thread_id"] = thread_id

        # Execute workflow
        result = self.graph.invoke(initial_state, config)

        return result

    def stream(
        self,
        initial_state: ACPState,
        thread_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream workflow execution with intermediate states.

        Args:
            initial_state: Initial workflow state
            thread_id: Thread ID for checkpoint tracking
            config: Optional LangGraph config overrides

        Yields:
            Intermediate workflow states

        Example:
            >>> for state in workflow.stream(initial_state):
            ...     print(f"Current phase: {state['phase']}")
        """
        if thread_id is None:
            thread_id = generate_thread_id()

        if config is None:
            config = {}

        config["configurable"] = config.get("configurable", {})
        config["configurable"]["thread_id"] = thread_id

        # Stream workflow execution
        for state in self.graph.stream(initial_state, config):
            yield state

    def resume(
        self,
        thread_id: str,
        updates: Optional[ACPState] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> ACPState:
        """
        Resume workflow from checkpoint.

        Args:
            thread_id: Thread ID of workflow to resume
            updates: Optional state updates to apply before resuming
            config: Optional LangGraph config overrides

        Returns:
            Final workflow state

        Raises:
            ValueError: If thread_id not found in checkpoints

        Example:
            >>> state = workflow.resume(thread_id="abc123")
        """
        if config is None:
            config = {}

        config["configurable"] = config.get("configurable", {})
        config["configurable"]["thread_id"] = thread_id

        # Get current state from checkpoint
        current_state = self.get_state(thread_id)

        if current_state is None:
            raise ValueError(f"No checkpoint found for thread_id: {thread_id}")

        # Apply updates if provided
        if updates:
            current_state.update(updates)

        # Resume execution
        result = self.graph.invoke(current_state, config)

        return result

    def get_state(self, thread_id: str) -> Optional[ACPState]:
        """
        Get current state for thread from checkpoint.

        Args:
            thread_id: Thread ID to query

        Returns:
            Current state or None if thread not found

        Example:
            >>> state = workflow.get_state("abc123")
            >>> if state:
            ...     print(f"Current phase: {state['phase']}")
        """
        config = {"configurable": {"thread_id": thread_id}}

        try:
            checkpoint = self.graph.get_state(config)
            if checkpoint and checkpoint.values:
                return checkpoint.values
        except Exception:
            pass

        return None


# ============================================================
# ROUTING FUNCTIONS
# ============================================================


def route_governance(state: ACPState) -> Literal["passed", "failed", "retry"]:
    """
    Route based on governance gate result with retry logic.

    Args:
        state: Current workflow state

    Returns:
        "passed" if governance_passes is True
        "retry" if failed but retries remain
        "failed" if max retries exceeded

    Example:
        >>> builder.add_conditional_edges(
        ...     "governance",
        ...     route_governance,
        ...     {"passed": "next_phase", "retry": "error_handler", "failed": END}
        ... )
    """
    if state.get("governance_passes", False):
        # Reset error count on success
        state["error_count"] = 0
        return "passed"

    # Check retry count
    error_count = state.get("error_count", 0)
    max_retries = 3

    if error_count < max_retries:
        # Increment error count for next iteration
        state["error_count"] = error_count + 1
        return "retry"
    else:
        # Max retries exceeded
        return "failed"


def route_after_error_handler(state: ACPState) -> Literal["regenerate", "complete"]:
    """
    Route after error handler processes violation.

    Args:
        state: Current workflow state

    Returns:
        "regenerate" if user chose to regenerate, "complete" if resolved/ignored

    Example:
        >>> builder.add_conditional_edges(
        ...     "error_handler",
        ...     route_after_error_handler,
        ...     {"regenerate": "specification", "complete": END}
        ... )
    """
    # Check if governance now passes (user chose ignore or edited constitution)
    if state.get("governance_passes", False):
        return "complete"
    else:
        # Regenerate artifact
        return "regenerate"


def route_by_phase(state: ACPState) -> str:
    """
    Route based on current workflow phase.

    Args:
        state: Current workflow state

    Returns:
        Current phase name

    Example:
        >>> builder.add_conditional_edges("router", route_by_phase)
    """
    return state.get("phase", "init")


def route_completion(state: ACPState) -> Literal["continue", "complete"]:
    """
    Route based on workflow completion status.

    Args:
        state: Current workflow state

    Returns:
        "complete" if phase is "complete", "continue" otherwise

    Example:
        >>> builder.add_conditional_edges(
        ...     "check_completion",
        ...     route_completion,
        ...     {"complete": END, "continue": "next_node"}
        ... )
    """
    phase = state.get("phase", "init")
    return "complete" if phase == "complete" else "continue"


def route_planning_governance(state: ACPState) -> Literal["passed", "failed", "retry"]:
    """
    Route based on planning phase governance validation with retry logic.

    Args:
        state: Current workflow state

    Returns:
        "passed" if governance_passes is True
        "retry" if failed but retries remain
        "failed" if max retries exceeded

    Example:
        >>> builder.add_conditional_edges(
        ...     "planning_governance",
        ...     route_planning_governance,
        ...     {"passed": "planning_complete", "retry": "error_handler", "failed": END}
        ... )
    """
    if state.get("governance_passes", False):
        # Reset error count on success
        state["error_count"] = 0
        return "passed"

    # Check retry count
    error_count = state.get("error_count", 0)
    max_retries = 3

    if error_count < max_retries:
        # Increment error count for next iteration
        state["error_count"] = error_count + 1
        return "retry"
    else:
        # Max retries exceeded
        return "failed"


# ============================================================
# THREAD MANAGEMENT
# ============================================================


def generate_thread_id() -> str:
    """
    Generate unique thread ID for workflow tracking.

    Returns:
        UUID-based thread ID

    Example:
        >>> thread_id = generate_thread_id()
        >>> print(thread_id)
        'thread_abc123def456...'
    """
    return f"thread_{uuid.uuid4().hex[:16]}"


def create_thread_config(thread_id: str) -> Dict[str, Any]:
    """
    Create LangGraph config for thread-based execution.

    Args:
        thread_id: Thread ID for workflow

    Returns:
        Config dictionary for LangGraph

    Example:
        >>> config = create_thread_config("abc123")
        >>> result = workflow.run(state, config=config)
    """
    return {"configurable": {"thread_id": thread_id}}


# ============================================================
# ERROR HANDLER NODE
# ============================================================


def create_governance_error_handler(
    on_violation: Optional[Callable[[ACPState, list], ACPState]] = None,
) -> Callable[[ACPState], ACPState]:
    """
    Create error handler node for constitutional violations.

    The error handler is called when governance validation fails. It can
    be customized with a callback function to handle user interaction
    (e.g., prompt for [R]egenerate, [E]dit, [A]bort, [I]gnore).

    Args:
        on_violation: Optional callback function that receives state and violations
                     and returns updated state. If None, violations are logged only.

    Returns:
        Error handler node function

    Example:
        >>> def my_handler(state, violations):
        ...     # Show violations to user, get choice
        ...     # Update state based on choice
        ...     return state
        >>> error_handler = create_governance_error_handler(on_violation=my_handler)
        >>> builder.add_node("error_handler", error_handler)
    """

    def error_handler_node(state: ACPState) -> ACPState:
        """
        Handle constitutional violations.

        Args:
            state: State with governance_passes=False

        Returns:
            Updated state after handling violations
        """
        # Extract violations from state (stored as JSON string)
        import json

        violations_json = (
            state.get("code_artifacts", {}).get("_governance_violations.json", "[]")
        )

        try:
            violations_data = json.loads(violations_json)
        except (json.JSONDecodeError, TypeError):
            violations_data = []

        if not violations_data:
            # No violations stored, something went wrong
            # Default to passing governance to avoid infinite loop
            state["governance_passes"] = True
            return state

        # If custom handler provided, use it
        if on_violation:
            return on_violation(state, violations_data)

        # Default behavior: log violations and fail
        # (CLI will override this with interactive handler)
        print(
            f"[Governance Error] {len(violations_data)} constitutional violations detected"
        )
        for v in violations_data:
            print(
                f"  - {v.get('principle', 'Unknown')}: {v.get('explanation', 'No explanation')}"
            )

        # Mark as failed (will exit workflow)
        state["governance_passes"] = False
        return state

    return error_handler_node


# ============================================================
# WORKFLOW FACTORY
# ============================================================


def create_workflow_builder(use_checkpointer: bool = True) -> WorkflowBuilder:
    """
    Factory function to create workflow builder.

    Args:
        use_checkpointer: If True, enable in-memory checkpointing

    Returns:
        WorkflowBuilder instance

    Example:
        >>> builder = create_workflow_builder()
        >>> builder.add_node("specify", specification_agent)
        >>> workflow = builder.compile()
    """
    return WorkflowBuilder(use_checkpointer=use_checkpointer)


# ============================================================
# EXAMPLE WORKFLOW CONSTRUCTION
# ============================================================


def create_example_workflow() -> CompiledWorkflow:
    """
    Create example workflow for testing and documentation.

    This demonstrates the workflow construction pattern.
    Actual workflow will be constructed in CLI commands.

    Returns:
        Example compiled workflow

    Example:
        >>> workflow = create_example_workflow()
    """

    def dummy_node(state: ACPState) -> ACPState:
        """Dummy node for example."""
        return state

    builder = create_workflow_builder()

    # Add nodes
    builder.add_node("init", dummy_node)
    builder.add_node("specify", dummy_node)
    builder.add_node("governance", dummy_node)
    builder.add_node("plan", dummy_node)
    builder.add_node("implement", dummy_node)

    # Add edges
    builder.add_edge(START, "init")
    builder.add_edge("init", "specify")
    builder.add_edge("specify", "governance")

    # Add conditional routing
    builder.add_conditional_edges(
        "governance",
        route_governance,
        {"passed": "plan", "failed": END},
    )

    builder.add_edge("plan", "implement")
    builder.add_edge("implement", END)

    return builder.compile()
