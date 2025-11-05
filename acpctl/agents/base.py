"""
acpctl Base Agent Interface

Defines the base interface for all LangGraph agents in the acpctl workflow.
Provides common patterns and utilities for agent node functions.

Agent Architecture:
- All agents implement node function signature: fn(state: ACPState) -> ACPState
- Agents are pure functions that transform state
- Side effects (I/O, LLM calls) are isolated within agent implementations
- State validation happens at checkpoint boundaries, not during execution

Reference: speckit-langgraph-architecture.md (Agent Orchestration section)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol

from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.console import Console

from acpctl.core.state import ACPState


# ============================================================
# AGENT PROTOCOL
# ============================================================


class AgentNode(Protocol):
    """
    Protocol for LangGraph agent node functions.

    All agent nodes must accept ACPState and return ACPState.
    This enables type-safe agent composition in LangGraph StateGraph.

    Example:
        >>> def my_agent(state: ACPState) -> ACPState:
        ...     state['spec'] = "Generated specification..."
        ...     return state
        >>> # my_agent conforms to AgentNode protocol
    """

    def __call__(self, state: ACPState) -> ACPState:
        """
        Execute agent logic and return updated state.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        ...


# ============================================================
# BASE AGENT CLASS
# ============================================================


class BaseAgent(ABC):
    """
    Base class for acpctl agents.

    Provides common functionality and enforces consistent agent interface.
    All concrete agents should inherit from this class.

    Attributes:
        agent_name: Human-readable agent name for logging
        agent_type: Agent type identifier (e.g., "governance", "specification")

    Example:
        >>> class MyAgent(BaseAgent):
        ...     def __init__(self):
        ...         super().__init__(agent_name="My Agent", agent_type="custom")
        ...
        ...     def execute(self, state: ACPState) -> ACPState:
        ...         # Agent logic here
        ...         return state
    """

    def __init__(self, agent_name: str, agent_type: str):
        """
        Initialize base agent.

        Args:
            agent_name: Human-readable agent name
            agent_type: Agent type identifier
        """
        self.agent_name = agent_name
        self.agent_type = agent_type
        self._live_display: Optional[Live] = None
        self._console = Console()

    @abstractmethod
    def execute(self, state: ACPState) -> ACPState:
        """
        Execute agent logic.

        This is the main method that must be implemented by all agents.
        It receives the current workflow state and returns updated state.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state with agent modifications

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(f"{self.agent_name} must implement execute()")

    def __call__(self, state: ACPState) -> ACPState:
        """
        Make agent callable as a function.

        This allows agents to be used directly as LangGraph node functions.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state

        Example:
            >>> agent = MyAgent()
            >>> updated_state = agent(current_state)
        """
        return self.execute(state)

    def log(self, message: str, level: str = "info") -> None:
        """
        Log agent activity.

        Args:
            message: Log message
            level: Log level ("info", "warning", "error", "debug")

        Note:
            In production, this will integrate with acpctl.utils.logging.
            For now, it's a simple print for development.
        """
        prefix = f"[{self.agent_name}]"
        print(f"{prefix} {message}")

    def validate_state_requirements(
        self, state: ACPState, required_fields: list[str]
    ) -> None:
        """
        Validate that required fields are present in state.

        Args:
            state: Current workflow state
            required_fields: List of required field names

        Raises:
            ValueError: If any required field is missing or empty

        Example:
            >>> agent.validate_state_requirements(
            ...     state,
            ...     ['constitution', 'feature_description']
            ... )
        """
        missing_fields = []

        for field in required_fields:
            if field not in state or not state[field]:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"{self.agent_name} requires fields: {', '.join(missing_fields)}"
            )

    def update_state(
        self, state: ACPState, updates: Dict[str, Any]
    ) -> ACPState:
        """
        Update state with new values.

        Helper method for clean state updates with logging.

        Args:
            state: Current workflow state
            updates: Dictionary of field updates

        Returns:
            Updated state

        Example:
            >>> state = agent.update_state(
            ...     state,
            ...     {'spec': 'Generated spec...', 'phase': 'plan'}
            ... )
        """
        for key, value in updates.items():
            state[key] = value
            self.log(f"Updated state field: {key}", level="debug")

        return state

    def update_streaming_display(self, message: str, spinner: bool = True) -> None:
        """
        Update streaming display with new message.

        Args:
            message: Message to display
            spinner: Whether to show spinner (default: True)

        Example:
            >>> agent.update_streaming_display("Analyzing requirements...")
        """
        if self._live_display:
            if spinner:
                content = f"[bold]{self.agent_name}[/bold]\n\n{message}"
                self._live_display.update(
                    Panel(
                        content,
                        border_style="blue",
                        padding=(1, 2),
                    )
                )
            else:
                self._live_display.update(Panel(message, border_style="green"))

    def execute_with_streaming(
        self, state: ACPState, verbose: bool = False
    ) -> ACPState:
        """
        Execute agent with streaming display of progress.

        This wrapper provides real-time feedback during agent execution,
        showing progress indicators and status updates.

        Args:
            state: Current workflow state
            verbose: If True, show detailed streaming display

        Returns:
            Updated workflow state

        Example:
            >>> state = agent.execute_with_streaming(state, verbose=True)
        """
        if not verbose:
            # Non-verbose mode: just execute without streaming
            return self.execute(state)

        # Verbose mode: show streaming display
        with Live(
            Panel(
                f"[bold]{self.agent_name}[/bold]\n\nStarting...",
                border_style="blue",
                padding=(1, 2),
            ),
            console=self._console,
            refresh_per_second=4,
        ) as live:
            self._live_display = live
            try:
                result = self.execute(state)
                # Show completion
                self._live_display.update(
                    Panel(
                        f"[bold green]{self.agent_name}[/bold green]\n\nCompleted successfully",
                        border_style="green",
                        padding=(1, 2),
                    )
                )
                return result
            except Exception as e:
                # Show error
                self._live_display.update(
                    Panel(
                        f"[bold red]{self.agent_name}[/bold red]\n\nError: {str(e)}",
                        border_style="red",
                        padding=(1, 2),
                    )
                )
                raise
            finally:
                self._live_display = None


# ============================================================
# AGENT NODE FACTORY
# ============================================================


def create_agent_node(agent: BaseAgent) -> AgentNode:
    """
    Create LangGraph node function from agent instance.

    Wraps agent.execute() in a function that conforms to AgentNode protocol.

    Args:
        agent: BaseAgent instance

    Returns:
        AgentNode function suitable for LangGraph StateGraph

    Example:
        >>> agent = MyAgent()
        >>> node_fn = create_agent_node(agent)
        >>> workflow.add_node("my_agent", node_fn)
    """

    def node_function(state: ACPState) -> ACPState:
        """Agent node function for LangGraph."""
        return agent.execute(state)

    node_function.__name__ = f"{agent.agent_type}_node"
    node_function.__doc__ = f"LangGraph node for {agent.agent_name}"

    return node_function


# ============================================================
# COMMON AGENT UTILITIES
# ============================================================


def extract_phase_from_state(state: ACPState) -> str:
    """
    Extract current phase from state.

    Args:
        state: Current workflow state

    Returns:
        Current phase name

    Example:
        >>> phase = extract_phase_from_state(state)
        >>> print(phase)
        'specify'
    """
    return state.get("phase", "init")


def is_governance_passed(state: ACPState) -> bool:
    """
    Check if governance gate has been passed.

    Args:
        state: Current workflow state

    Returns:
        True if governance_passes is True

    Example:
        >>> if is_governance_passed(state):
        ...     # Proceed to next phase
    """
    return state.get("governance_passes", False)


def get_feature_description(state: ACPState) -> str:
    """
    Extract feature description from state.

    Args:
        state: Current workflow state

    Returns:
        Feature description string

    Example:
        >>> description = get_feature_description(state)
        >>> print(description)
        'Add OAuth2 authentication'
    """
    return state.get("feature_description", "")


def get_constitution(state: ACPState) -> str:
    """
    Extract constitution from state.

    Args:
        state: Current workflow state

    Returns:
        Constitution content string

    Example:
        >>> constitution = get_constitution(state)
    """
    return state.get("constitution", "")


# ============================================================
# AGENT ERROR HANDLING
# ============================================================


class AgentError(Exception):
    """
    Base exception for agent errors.

    Attributes:
        agent_name: Name of agent that raised error
        message: Error message
        state_snapshot: Optional state snapshot at time of error
    """

    def __init__(
        self,
        agent_name: str,
        message: str,
        state_snapshot: ACPState | None = None,
    ):
        """
        Initialize agent error.

        Args:
            agent_name: Name of agent that raised error
            message: Error message
            state_snapshot: Optional state snapshot
        """
        self.agent_name = agent_name
        self.message = message
        self.state_snapshot = state_snapshot
        super().__init__(f"[{agent_name}] {message}")


class AgentValidationError(AgentError):
    """Raised when agent input validation fails."""

    pass


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    pass


class AgentLLMError(AgentError):
    """Raised when LLM call fails."""

    pass
