# Data Model: acpctl Workflow State

**Feature**: Governed Spec-Driven Development CLI
**Date**: 2025-11-05
**Version**: 1.0.0

This document defines all data entities for the acpctl workflow system without specifying implementation details.

---

## Core Entities

### 1. Constitutional Principle

**Purpose**: Represents a governance rule that all artifacts must satisfy.

**Attributes**:
- **Name**: Unique identifier for the principle (e.g., "I. Specifications as First-Class Artifacts")
- **Description**: Detailed explanation of the rule and its requirements
- **Category**: Classification (Core Principles, Enterprise Requirements, Development Workflow)
- **Enforcement Level**: NON-NEGOTIABLE or STANDARD
- **Validation Rules**: Specific checks that must pass for compliance

**Relationships**:
- Referenced by Constitutional Violations (many-to-one)
- Validated against all Workflow Artifacts (one-to-many)

**State Transitions**: None (principles are immutable within a workflow run)

**Validation Rules**:
- Name must be unique within a constitution
- Description must be non-empty
- At least one validation rule must be defined

---

### 2. Feature Workflow

**Purpose**: Represents the complete journey from natural language description through specification, planning, and implementation.

**Attributes**:
- **Feature ID**: Sequential numeric identifier (e.g., "001")
- **Feature Name**: URL-safe slug (e.g., "langgraph-spec-kit-port")
- **Thread ID**: LangGraph execution identifier (e.g., "acpctl-001-20250105-120000")
- **Feature Description**: Natural language input from user
- **Created At**: Timestamp when workflow started
- **Last Checkpoint**: Most recent phase boundary (INIT, SPECIFICATION_COMPLETE, PLANNING_COMPLETE, IMPLEMENTATION_COMPLETE)
- **Status**: Current state (CREATED, IN_PROGRESS, PAUSED, COMPLETED, FAILED)
- **Phases Completed**: List of finished phases
- **Next Phase**: Which phase to execute next
- **Branch Name**: Git branch for this feature (e.g., "001-langgraph-spec-kit-port")

**Relationships**:
- Has one Constitution (one-to-one)
- Has one Checkpoint per phase (one-to-many)
- Produces multiple Workflow Artifacts (one-to-many)
- May have multiple Constitutional Violations (one-to-many)

**State Transitions**:
```
CREATED → IN_PROGRESS (when first phase starts)
IN_PROGRESS → PAUSED (when interrupted or waiting for user input)
PAUSED → IN_PROGRESS (when resumed)
IN_PROGRESS → COMPLETED (when all phases finish successfully)
IN_PROGRESS → FAILED (when unrecoverable error or user aborts)
```

**Validation Rules**:
- Feature ID must be unique within repository
- Thread ID must be unique globally
- Status transitions must follow allowed paths
- Cannot have COMPLETED status without all phases completed
- Next Phase must be valid for current Status

---

### 3. Checkpoint

**Purpose**: Represents a saved workflow state at a phase boundary, enabling resume capability.

**Attributes**:
- **Checkpoint ID**: Unique identifier (thread_id + phase)
- **Feature ID**: Which workflow this belongs to
- **Thread ID**: LangGraph execution identifier
- **Phase**: Which boundary this checkpoint represents (INIT, SPECIFICATION_COMPLETE, PLANNING_COMPLETE, IMPLEMENTATION_COMPLETE)
- **State Snapshot**: Complete workflow state at this point
- **Created At**: When this checkpoint was saved
- **Schema Version**: State schema version for migration (e.g., "1.0.0")

**Relationships**:
- Belongs to one Feature Workflow (many-to-one)
- Contains references to all Workflow Artifacts created up to this phase (one-to-many)

**State Transitions**: None (checkpoints are immutable once saved)

**Validation Rules**:
- Checkpoint ID must be unique
- State Snapshot must be complete and valid for the phase
- Schema Version must match supported versions
- Feature ID and Thread ID must reference existing workflow

---

### 4. Workflow Artifact

**Purpose**: Abstract base entity for all generated documents (specs, plans, code).

**Attributes**:
- **Artifact ID**: Unique identifier
- **Feature ID**: Which workflow produced this
- **Type**: SPECIFICATION, PLAN, DATA_MODEL, CONTRACT, CODE_TEST, CODE_IMPLEMENTATION
- **File Path**: Location in repository (e.g., "specs/001-feature/spec.md")
- **Content**: The actual artifact text
- **Created At**: When generated
- **Last Modified**: When last updated
- **Constitutional Validation Status**: PENDING, PASS, FAIL
- **Violations**: List of Constitutional Violations (if any)

**Relationships**:
- Belongs to one Feature Workflow (many-to-one)
- May have multiple Constitutional Violations (one-to-many)
- Referenced by Checkpoints (many-to-many)

**State Transitions**:
```
PENDING → PASS (after constitutional validation succeeds)
PENDING → FAIL (when violations detected)
FAIL → PENDING (when regenerated after fixes)
```

**Validation Rules**:
- File Path must be unique within repository
- Content must be non-empty
- Type must match file path convention
- Cannot have PASS status with non-empty violations list

---

### 5. Specification Artifact

**Purpose**: Document describing what users need and why, without implementation details.

**Inherits from**: Workflow Artifact

**Additional Attributes**:
- **User Scenarios**: List of user stories with acceptance criteria
- **Functional Requirements**: Numbered list of system capabilities
- **Success Criteria**: Measurable outcomes
- **Clarifications**: List of answers from pre-flight questionnaire

**Validation Rules** (beyond base):
- Must not contain programming languages, frameworks, databases, or APIs
- Must have at least one user scenario
- Must have at least one functional requirement
- All functional requirements must have corresponding acceptance scenarios

---

### 6. Planning Artifact

**Purpose**: Technical design documents describing how to build the feature.

**Inherits from**: Workflow Artifact

**Additional Attributes**:
- **Technical Context**: Language, dependencies, platform, performance goals
- **Implementation Phases**: Ordered list of development phases
- **Data Model Reference**: Link to data-model.md artifact
- **Contracts Reference**: Links to contract files
- **Unknowns**: List of research questions (should be empty after Phase 0)

**Validation Rules** (beyond base):
- Must reference completed Specification Artifact
- All Unknowns must be resolved before planning completes
- Technical Context must specify all required fields

---

### 7. Constitutional Violation

**Purpose**: Represents a detected conflict between an artifact and a constitutional principle.

**Attributes**:
- **Violation ID**: Unique identifier
- **Artifact ID**: Which artifact has the violation
- **Principle Name**: Which constitutional principle was violated
- **Location**: File path and line number
- **Description**: What the violation is
- **Suggested Fix**: Actionable correction
- **Status**: DETECTED, ACKNOWLEDGED, FIXED, IGNORED_FORCED
- **Detected At**: When found
- **Resolved At**: When fixed (if applicable)

**Relationships**:
- Belongs to one Workflow Artifact (many-to-one)
- References one Constitutional Principle (many-to-one)

**State Transitions**:
```
DETECTED → ACKNOWLEDGED (user views violation report)
ACKNOWLEDGED → FIXED (artifact regenerated and passes validation)
ACKNOWLEDGED → IGNORED_FORCED (user chooses [I]gnore with --force flag)
DETECTED → FIXED (auto-fixed without user intervention)
```

**Validation Rules**:
- Suggested Fix must be non-empty
- Location must reference valid file path and line number
- Cannot transition to FIXED without corresponding artifact update
- IGNORED_FORCED requires explicit user confirmation

---

### 8. Pre-flight Question

**Purpose**: Represents an ambiguity identified in feature description requiring clarification before workflow execution.

**Attributes**:
- **Question ID**: Sequential number (1, 2, 3...)
- **Feature ID**: Which workflow this belongs to
- **Question Text**: What needs clarification
- **Context**: Why this question is being asked
- **Answer**: User's response (null until answered)
- **Asked At**: Timestamp
- **Answered At**: Timestamp (null if not yet answered)

**Relationships**:
- Belongs to one Feature Workflow (many-to-one)
- Answer recorded in Specification Artifact's Clarifications list (one-to-many)

**State Transitions**:
```
UNANSWERED → ANSWERED (when user provides response)
```

**Validation Rules**:
- Question Text must be non-empty
- Answer must be non-empty before workflow can proceed to specification phase
- Maximum 10 questions per workflow (Constitutional Principle IV requirement)
- Cannot ask same question twice (deduplicate by Question Text)

---

### 9. Implementation Artifact

**Purpose**: Generated code files that realize the planned feature.

**Inherits from**: Workflow Artifact

**Additional Attributes**:
- **Code Type**: TEST or IMPLEMENTATION
- **Language**: Programming language (inferred from file extension)
- **Related Test**: Link to corresponding test file (for IMPLEMENTATION type)
- **Related Implementation**: Link to corresponding implementation file (for TEST type)
- **Test Status**: PENDING, FAILING, PASSING (only for TEST type)
- **Coverage**: Percentage of implementation covered (only for TEST type)

**Validation Rules** (beyond base):
- TEST artifacts must be created before corresponding IMPLEMENTATION artifacts (TDD requirement)
- IMPLEMENTATION artifacts cannot be marked complete unless related TEST has PASSING status
- Code must not include hardcoded secrets or credentials
- Must reference completed Planning Artifact

**State Transitions** (TEST type):
```
PENDING → FAILING (after initial generation, before implementation exists)
FAILING → PASSING (after implementation written and tests pass)
```

---

## Workflow State Schema

**Purpose**: Complete state structure passed between LangGraph agents.

**Structure** (TypedDict format):

```
WorkflowState:
  # Constitution layer
  - constitution: String (entire constitution.md content)
  - governance_passes: Boolean (true if no violations)

  # Specification layer
  - feature_description: String (user's natural language input)
  - spec: String (generated spec.md content)
  - clarifications: List[String] (answers from pre-flight Q&A)

  # Planning layer
  - unknowns: List[String] (research questions - empty after Phase 0)
  - research: String (research.md content)
  - plan: String (plan.md content)
  - data_model: String (data-model.md content)
  - contracts: Dictionary (contract file paths → content)

  # Implementation layer
  - tasks: List[Dictionary] (task definitions with dependencies)
  - completed_tasks: List[String] (task IDs that finished)
  - code_artifacts: Dictionary (file paths → code content)
  - validation_status: String (PENDING, PASS, FAIL)

  # Error handling
  - error: Optional[Dictionary] (node, message, count if error occurred)
  - error_count: Integer (number of retry attempts)
```

**Invariants** (validated at checkpoint boundaries):
1. Cannot specify without constitution + governance_passes=True
2. Cannot plan without spec + feature_description
3. Cannot implement without plan + data_model
4. Cannot complete without all tasks in completed_tasks
5. Cannot save checkpoint with error_count >= 3 (must escalate)

---

## Relationships Diagram

```
┌─────────────────────┐
│ Feature Workflow    │
│ - feature_id        │
│ - thread_id         │
│ - status            │
└──────┬──────────────┘
       │
       ├──── has one ───┐
       │                │
       │         ┌──────▼──────────┐
       │         │ Constitution    │
       │         │ - principles[]  │
       │         └─────────────────┘
       │
       ├──── produces ───┐
       │                 │
       │         ┌───────▼─────────────┐
       │         │ Workflow Artifact   │◄──── references
       │         │ - type              │
       │         │ - content           │      ┌────────────────────────┐
       │         │ - validation_status │      │ Constitutional         │
       │         └──────┬──────────────┘      │ Violation              │
       │                │                     │ - location             │
       │                └──── has ────────────┤ - suggested_fix        │
       │                                      └────────────────────────┘
       │
       ├──── has ───┐
       │            │
       │     ┌──────▼──────────┐
       │     │ Checkpoint      │
       │     │ - phase         │
       │     │ - state_snapshot│
       │     └─────────────────┘
       │
       └──── has ───┐
                    │
             ┌──────▼──────────────┐
             │ Pre-flight Question │
             │ - question_text     │
             │ - answer            │
             └─────────────────────┘
```

---

## Persistence Strategy

**Checkpoint Files** (`.acp/state/`):
- One JSON file per workflow: `{feature-id}.json`
- Contains: Feature Workflow metadata + Thread ID for LangGraph lookup
- Human-readable for CLI status display

**LangGraph Checkpointer** (SQLite/Postgres):
- Stores complete WorkflowState snapshots keyed by thread_id
- Handles automatic state persistence after each node
- Enables resumption and rollback

**Artifact Files** (`specs/{feature-id}/`):
- Specification Artifacts: `spec.md`
- Planning Artifacts: `plan.md`, `data-model.md`, `contracts/*.yaml`
- Implementation Artifacts: source code files in repository root

**Separation of Concerns**:
- LangGraph manages execution state (for agent resume)
- CLI metadata files manage workflow lifecycle (for user-facing commands)
- Artifact files are the deliverable outputs (for version control)

---

## Schema Versioning

**Version**: 1.0.0 (Phase 1)

**Planned Additions** (Phase 2+):
- Parallel research agents (research_results: List[Dict])
- Task dependencies (task_graph: Dict[str, List[str]])
- Validation agent rework loops (rework_count: int)
- Memory layer (conversation_history: List[Dict])

**Migration Strategy**:
- Checkpoints include `schema_version` field
- Load checkpoint detects version mismatch
- Auto-migration functions convert old → new format
- No data loss: new fields get safe defaults
- Backward compatible: V2.0.0 code reads V1.0.0 checkpoints

---

## Summary

This data model provides:
- ✅ All entities from feature spec's Key Entities section
- ✅ Complete attribute definitions without implementation details
- ✅ Clear relationships between entities
- ✅ State transition diagrams for stateful entities
- ✅ Validation rules for each entity
- ✅ Complete WorkflowState schema for LangGraph
- ✅ Persistence strategy separating concerns
- ✅ Schema versioning for future compatibility

All entities align with Constitutional Principles (specs as first-class artifacts, checkpoint everything, governance gates, pre-flight Q&A, TDD).
