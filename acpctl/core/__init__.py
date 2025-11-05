"""
acpctl Core Business Logic

Core workflow orchestration and state management for acpctl.
This module provides the foundation for LangGraph-based agent workflows.

Modules:
- state: Pydantic state models and TypedDict definitions
- checkpoint: Checkpoint save/load with schema versioning
- workflow: LangGraph StateGraph builder and execution
"""

from acpctl.core.checkpoint import (
    CLIMetadata,
    CheckpointData,
    checkpoint_exists,
    get_checkpoint_by_feature_id,
    get_checkpoint_version,
    get_latest_checkpoint,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
    validate_checkpoint_file,
)
from acpctl.core.state import (
    ACPState,
    ACPStateModel,
    create_test_state,
    pydantic_to_typed_dict,
    transition_state,
    typed_dict_to_pydantic,
)
from acpctl.core.workflow import (
    CompiledWorkflow,
    WorkflowBuilder,
    create_thread_config,
    create_workflow_builder,
    generate_thread_id,
    route_by_phase,
    route_completion,
    route_governance,
)

__all__ = [
    # State
    "ACPState",
    "ACPStateModel",
    "create_test_state",
    "transition_state",
    "typed_dict_to_pydantic",
    "pydantic_to_typed_dict",
    # Checkpoint
    "save_checkpoint",
    "load_checkpoint",
    "checkpoint_exists",
    "validate_checkpoint_file",
    "list_checkpoints",
    "get_latest_checkpoint",
    "get_checkpoint_by_feature_id",
    "get_checkpoint_version",
    "CLIMetadata",
    "CheckpointData",
    # Workflow
    "WorkflowBuilder",
    "CompiledWorkflow",
    "create_workflow_builder",
    "generate_thread_id",
    "create_thread_config",
    "route_governance",
    "route_by_phase",
    "route_completion",
]
