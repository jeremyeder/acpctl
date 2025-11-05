# Implementation Plan: Governed Spec-Driven Development CLI

**Branch**: `001-langgraph-spec-kit-port` | **Date**: 2025-11-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-langgraph-spec-kit-port/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature ports GitHub's spec-kit workflow into a LangGraph-based intelligent agent system (acpctl) that provides constitutional governance, automatic checkpointing, and multi-agent orchestration for spec-driven development. The CLI enables developers to generate specifications, implementation plans, and code through an AI-powered workflow that validates all artifacts against project-specific constitutional principles.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: LangGraph (agent orchestration), LangChain (agent framework), Click or Typer (CLI), Rich (terminal UI), Pydantic (state validation)
**Storage**: JSON checkpoint files in `.acp/state/` directory, file-based artifact storage in `specs/` directories
**Testing**: pytest with fixtures for agent mocks, integration tests for workflow phases
**Target Platform**: Linux/macOS/Windows CLI environments, container-ready for CI/CD integration
**Project Type**: Single CLI application with library-first architecture
**Performance Goals**: <10s for initialization, <10min for specification with pre-flight Q&A, <30min for complete workflow end-to-end
**Constraints**: Must support workflow interruption and resume without data loss, all state must be serializable to JSON, agent prompts must fit within LLM context windows
**Scale/Scope**: Enterprise development teams (10-100 developers), features ranging from simple (authentication) to complex (distributed systems), specifications up to 50 pages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Evaluation (Initial)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specifications as First-Class Artifacts** | ✅ PASS | Feature spec.md correctly focuses on user scenarios, acceptance criteria, and requirements without implementation details. No frameworks or languages mentioned in spec. |
| **II. Constitutional Governance** | ✅ PASS | This plan implements the governance workflow itself. All phases include validation gates. |
| **III. Checkpoint Everything** | ✅ PASS | Design includes JSON checkpoint files at phase boundaries (.acp/state/). State persistence is core requirement. |
| **IV. Pre-flight Over Interruption** | ✅ PASS | Specification Agent design includes pre-flight questionnaire (FR-003). All questions collected before workflow execution. |
| **V. Progressive Disclosure** | ✅ PASS | Three verbosity modes specified in FR-016. Rich terminal UI planned. |
| **VI. Library-First Architecture** | ⚠️ PENDING | Project structure not yet determined. Will validate in Phase 1 after source structure defined. |
| **VII. Test-First** | ⚠️ PENDING | TDD approach required by FR-013. Implementation details in Phase 2. Will validate test infrastructure in Phase 1. |
| **Enterprise: Security & Compliance** | ✅ PASS | No secrets in current design. Audit trail via checkpoint history. Python/LangChain are Apache 2.0 compatible. |
| **Enterprise: Performance Standards** | ✅ PASS | Performance goals explicitly defined in Technical Context and Success Criteria. All thresholds measurable. |
| **Quality Standards** | ⚠️ PENDING | Pydantic models planned for state. Type safety and error handling will be validated in Phase 1 design. |

**Overall Status**: ✅ **PASS** - No blocking violations. Pending items will be resolved during design phases.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
acpctl/                          # Root package
├── __init__.py
├── cli/                         # CLI entry points and command handlers
│   ├── __init__.py
│   ├── main.py                  # CLI application entry
│   ├── commands/                # Command implementations (init, specify, plan, etc.)
│   └── ui/                      # Rich terminal UI components
├── core/                        # Core business logic (library-first)
│   ├── __init__.py
│   ├── workflow.py              # LangGraph workflow orchestration
│   ├── state.py                 # Pydantic state models
│   └── checkpoint.py            # Checkpoint save/load logic
├── agents/                      # LangGraph agent implementations
│   ├── __init__.py
│   ├── base.py                  # Base agent interface
│   ├── governance.py            # Constitutional validation agent
│   ├── specification.py         # Spec generation + pre-flight Q&A agent
│   ├── architect.py             # Planning and design agent
│   └── implementation.py        # Code generation agent
├── storage/                     # File system operations
│   ├── __init__.py
│   ├── artifacts.py             # Artifact file management (specs, plans)
│   └── constitution.py          # Constitution file operations
└── utils/                       # Shared utilities
    ├── __init__.py
    ├── logging.py               # Structured logging
    └── validation.py            # Schema validation helpers

tests/
├── contract/                    # Agent contract tests
│   ├── test_governance_agent.py
│   ├── test_specification_agent.py
│   └── test_checkpoint_schema.py
├── integration/                 # Multi-phase workflow tests
│   ├── test_init_workflow.py
│   ├── test_specify_workflow.py
│   ├── test_resume_workflow.py
│   └── fixtures/                # Test data and mocks
└── unit/                        # Component unit tests
    ├── test_state_models.py
    ├── test_checkpoint.py
    └── test_artifacts.py

.acp/                            # Runtime directory (created by acpctl init)
├── templates/
│   └── constitution.md          # Constitutional template
├── state/                       # Checkpoint files
│   └── 001-feature.json
└── memory/                      # (Phase 2 - not in Phase 1)
```

**Structure Decision**: Selected **single project** pattern. This is a CLI tool with library-first architecture following Constitutional Principle VI. Core logic in `acpctl/core/` and `acpctl/agents/` can be imported and tested independently of CLI layer. Clear separation: CLI (commands/UI) → Core (workflow/state) → Agents (LangGraph) → Storage (filesystem).

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations requiring justification.

---

## Post-Design Constitution Check

*Re-evaluated after Phase 1 design artifacts generated*

### Evaluation (After research.md, data-model.md, contracts/, quickstart.md)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specifications as First-Class Artifacts** | ✅ PASS | Spec.md remains implementation-free. Data-model.md describes entities without database details. |
| **II. Constitutional Governance** | ✅ PASS | Governance gates designed into workflow with conditional edges. Error handler provides [R]egenerate, [E]dit, [A]bort, [I]gnore options. |
| **III. Checkpoint Everything** | ✅ PASS | Research confirms LangGraph SqliteSaver with thread_id checkpointing. CLI metadata files in .acp/state/ for workflow lifecycle. |
| **IV. Pre-flight Over Interruption** | ✅ PASS | Design includes Pre-flight Question entity with max 10 questions. All questions collected before workflow execution (FR-003 validated). |
| **V. Progressive Disclosure** | ✅ PASS | Research confirms Typer + Rich integration with Config class. Three verbosity modes implemented via console_level. |
| **VI. Library-First Architecture** | ✅ PASS | Project structure shows clear separation: acpctl/core/ (library), acpctl/cli/ (wrapper). Tests can import core without CLI. |
| **VII. Test-First** | ✅ PASS | Data model includes Implementation Artifact with TEST/IMPLEMENTATION types. TDD cycle enforced: TEST artifacts created before IMPLEMENTATION artifacts. |
| **Enterprise: Security & Compliance** | ✅ PASS | Constitution validates no secrets in code. Implementation Artifact validation rules check for hardcoded credentials. Audit trail via checkpoint history. |
| **Enterprise: Performance Standards** | ✅ PASS | Technical Context confirms all performance goals measurable. Research addresses LangGraph performance patterns. |
| **Quality Standards** | ✅ PASS | Research confirms Pydantic BaseModel for checkpoint validation, mypy strict mode. ACPState schema includes error handling with error_count and retry logic. |

**Overall Status**: ✅ **PASS** - All constitutional principles satisfied by design artifacts.

**Validation Notes**:
- All pending items from pre-research evaluation are now resolved
- Project structure follows library-first pattern (Constitutional Principle VI)
- TDD approach validated with Implementation Artifact state transitions (Constitutional Principle VII)
- Type safety confirmed via Pydantic models and mypy (Quality Standards)
- No blocking violations or unjustified complexity

**Phase 1 Design Complete**: Ready for Phase 2 (task generation via `/speckit.tasks` command).

