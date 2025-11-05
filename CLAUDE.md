# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**acpctl** is a strategic design repository for the **acpctl** (Ambient Code Platform CLI), a LangGraph-based agent system that ports GitHub's spec-kit workflow into an intelligent, governed, multi-agent architecture.

**Current Status**: Design phase with UX demo. No implementation yet.

**Purpose**: Create a spec-driven development workflow with constitutional governance, automatic checkpointing, and intelligent agent orchestration for Red Hat's AI Engineering workflows.

## Repository Structure

```
acpctl/
├── speckit-langgraph-architecture.md       # Core architecture design doc
├── acpctl-phase1-implementation-plan.md    # Detailed Phase 1 implementation plan
└── demo/                                   # UX demonstration (mock only)
    ├── mock-acpctl.py                      # Mock CLI showing target UX
    ├── record-demo.sh                      # Demo recording script
    ├── acpctl-demo.cast                    # asciinema recording
    └── README.md                           # Demo documentation
```

## Key Concepts

### Workflow Philosophy

This project translates GitHub's **spec-kit** linear workflow into a **LangGraph agent graph** with these enhancements:

1. **Constitutional Governance**: Every phase validated against project principles (`.acp/templates/constitution.md`)
2. **Checkpoint/Resume**: Workflow state persists after each phase, enabling interruption and resumption
3. **Pre-flight Questionnaire**: All clarifications collected upfront before workflow starts (no interruptions)
4. **Multi-agent Orchestration**: Specialized agents (Governance, Specification, Architect, Implementation) with conditional routing

### Core Workflow Stages

Inspired by spec-kit's stages:

1. **Init** → Creates constitution template
2. **Specify** → Generates `spec.md` (what/why, not how)
3. **Plan** → Generates `plan.md`, `data-model.md`, `contracts/`
4. **Implement** → Generates code using TDD approach

Each stage has **governance gates** that validate output against constitutional principles.

### Agent Architecture

**Phase 1 Agents** (sequential):
- **Governance Agent**: Constitutional validator, reports violations with actionable fixes
- **Specification Agent**: Requirements analyzer with pre-flight Q&A
- **Architect Agent**: Technical planner (plan, data models, API contracts)
- **Implementation Agent**: Code generator with TDD approach

**Phase 2+ Agents** (deferred):
- Research Agent (parallel fanout)
- Task Decomposition Agent
- Validation Agent with rework loops

### State Management

**ACPState** TypedDict structure (from architecture doc):
```python
class ACPState(TypedDict):
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
    contracts: dict

    # Task/Implementation layers
    tasks: List[dict]
    completed_tasks: List[str]
    code_artifacts: dict
    validation_status: str
```

Checkpoints saved as JSON in `.acp/state/` after each phase completion.

## Demo Usage

### View UX Demo

```bash
# Play asciinema recording
asciinema play demo/acpctl-demo.cast

# Test mock CLI manually
./demo/mock-acpctl.py init
./demo/mock-acpctl.py specify "Add OAuth2 authentication"
./demo/mock-acpctl.py plan --verbose
./demo/mock-acpctl.py status
./demo/mock-acpctl.py resume
```

### Re-record Demo

```bash
# Edit mock CLI or demo script
vim demo/mock-acpctl.py
vim demo/record-demo.sh

# Re-record
asciinema rec demo/acpctl-demo.cast -c "./demo/record-demo.sh" --overwrite
```

## Target acpctl Commands (Not Yet Implemented)

When implementing Phase 1, these are the CLI commands to build:

```bash
acpctl init                              # Create .acp/ structure with constitution
acpctl specify "<description>"           # Generate spec with pre-flight Q&A
acpctl plan                              # Generate architecture plan
acpctl implement                         # Generate code via TDD
acpctl status                            # Show workflow progress
acpctl resume [spec-id]                  # Resume from checkpoint
acpctl history                           # List all workflows

# Verbosity flags (apply to all commands)
--quiet / -q                             # Minimal output
--verbose / -v                           # Full agent reasoning
# (default is moderate verbosity)
```

## Generated Artifact Structure (Target)

When implemented, acpctl will create:

```
.acp/
├── templates/
│   └── constitution.md                  # Project governing principles
├── state/
│   └── NNN-feature.json                 # Checkpoint files
└── memory/                              # (Phase 2)

specs/NNN-feature/
├── spec.md                              # Functional specification
├── plan.md                              # Implementation plan
├── data-model.md                        # Database schema
└── contracts/
    └── api.yaml                         # API contracts
```

## Implementation Technology Stack (Phase 1 Plan)

When building Phase 1:

**Core Dependencies**:
- **LangGraph** - Agent orchestration and StateGraph
- **LangChain** - Agent framework
- **Click** or **Typer** - CLI framework
- **Rich** - Terminal formatting (progress indicators, box drawing)
- **Pydantic** - State schema validation

**Dev Dependencies**:
- pytest, black, isort, mypy

## Architecture Principles

When implementing agents or workflow:

1. **Specifications as First-Class Artifacts** - Code serves specs, not vice versa
2. **Constitutional Governance** - Every artifact validated against principles
3. **Checkpoint Everything** - Save state after EVERY phase completion
4. **Pre-flight Over Interruption** - Collect all questions upfront (Specification Agent)
5. **Actionable Errors** - Constitutional violations must include fix suggestions
6. **Progressive Disclosure** - Support `--quiet`, moderate (default), `--verbose` output modes

## UX Design Decisions

From the demo and implementation plan:

1. **spec-kit Familiarity**: Command structure mirrors original spec-kit for easy migration
2. **Pre-flight Questionnaire**: Specification Agent asks ALL clarifying questions before workflow starts (no mid-workflow interruptions)
3. **Automatic Checkpointing**: State saves after `SPECIFICATION_COMPLETE`, `PLANNING_COMPLETE`, `IMPLEMENTATION_COMPLETE`
4. **Resume Anywhere**: `acpctl resume` loads checkpoint, skips completed phases, continues from breakpoint
5. **Constitutional Violation Handling**: Interactive prompts with `[R]egenerate`, `[E]dit constitution`, `[A]bort`, `[I]gnore --force` options

## Phase 1 Scope

**What's in Phase 1**:
- Sequential workflow (Governance → Specify → Plan → Implement)
- Constitutional gates at phase boundaries
- Pre-flight questionnaire
- Checkpoint/resume
- All acpctl commands
- Professional UX with 3 verbosity modes

**What's deferred to Phase 2+**:
- Parallel execution (research fanout, parallel implementation)
- Task decomposition with dependency graphs
- Validation agent with rework loops
- Red Hat enterprise integrations
- Performance optimization

## Validation Criteria for Phase 1 Completion

Phase 1 is done when:

- ✅ Full workflow runs: `acpctl init → specify → plan → implement`
- ✅ Pre-flight questionnaire works (no workflow interruptions)
- ✅ Constitutional violations caught and reported with fixes
- ✅ Checkpoints save automatically, resume works correctly
- ✅ `--quiet` and `--verbose` flags work across all commands
- ✅ Generated artifacts match spec-kit structure (`specs/NNN-feature/`)
- ✅ Complete audit trail via state inspection

## Red Hat Context

This project aligns with Red Hat AI Engineering's mission:

- **Governed Development**: Constitutional principles enforce security, licensing, architectural standards
- **Audit Trails**: Complete state history for compliance
- **Resume-from-Failure**: Critical for long-running enterprise workflows
- **Future Integration Points**: Internal docs (Confluence/Jira), approval workflows, CI/CD pipelines

## References

- **Architecture Document**: `speckit-langgraph-architecture.md` - Complete agent design, LangGraph structure, strategic rationale
- **Implementation Plan**: `acpctl-phase1-implementation-plan.md` - Week-by-week implementation sequence, validation criteria
- **Demo Documentation**: `demo/README.md` - UX demonstration details, recording instructions
- **Original spec-kit**: https://github.com/github/spec-kit
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- ACP stands for Ambient Code Platform
