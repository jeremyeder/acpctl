---
description: "Task list for implementing acpctl - Governed Spec-Driven Development CLI"
---

# Tasks: acpctl - Governed Spec-Driven Development CLI

**Input**: Design documents from `/specs/001-langgraph-spec-kit-port/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL per the feature specification - no explicit TDD requirement found. Test tasks are NOT included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: Repository root with `acpctl/` package
- All paths relative to repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create Python package structure (acpctl/, tests/, setup.py, pyproject.toml)
- [ ] T002 Initialize pyproject.toml with dependencies: LangGraph, LangChain, Typer, Rich, Pydantic
- [ ] T003 [P] Configure pytest with fixtures directory at tests/fixtures/
- [ ] T004 [P] Configure linting tools (black, isort, mypy) in pyproject.toml
- [ ] T005 Create __init__.py files for all package directories per plan.md structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create Pydantic state models in acpctl/core/state.py (ACPState TypedDict and ACPStateModel)
- [ ] T007 Implement checkpoint save/load functions in acpctl/core/checkpoint.py with schema versioning
- [ ] T008 [P] Create Rich Console config in acpctl/cli/ui/__init__.py with verbosity level support
- [ ] T009 [P] Implement Config class in acpctl/cli/ui/config.py with ConsoleLevel enum (quiet, default, verbose)
- [ ] T010 Create base Typer app in acpctl/cli/main.py with global verbosity flags
- [ ] T011 [P] Implement artifact file management in acpctl/storage/artifacts.py (read/write specs, plans, code)
- [ ] T012 [P] Implement constitution file operations in acpctl/storage/constitution.py (template creation, validation loading)
- [ ] T013 Create base agent interface in acpctl/agents/base.py defining node function signature
- [ ] T014 [P] Setup LangGraph StateGraph builder pattern in acpctl/core/workflow.py with SqliteSaver checkpointer
- [ ] T015 [P] Implement logging configuration in acpctl/utils/logging.py with structured output

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Initialize Project with Constitutional Governance (Priority: P1) 🎯 MVP

**Goal**: Enable developers to initialize a project with constitutional governance template

**Independent Test**: Run `acpctl init`, verify `.acp/templates/constitution.md` is created with example principles

### Implementation for User Story 1

- [ ] T016 [US1] Create constitution template content with sections for Core Principles, Enterprise Requirements, and Quality Standards
- [ ] T017 [US1] Implement init command in acpctl/cli/commands/init.py with constitutional template creation
- [ ] T018 [US1] Add directory structure creation (.acp/templates/, .acp/state/) in init command
- [ ] T019 [US1] Add idempotency check (detect existing setup, prompt for confirmation) in init command
- [ ] T020 [US1] Integrate init command with Rich UI for progress indicators and success messages
- [ ] T021 [US1] Register init command in acpctl/cli/main.py Typer app

**Checkpoint**: At this point, User Story 1 should be fully functional - `acpctl init` works independently

---

## Phase 4: User Story 2 - Generate Feature Specification with Pre-flight Questions (Priority: P1)

**Goal**: Enable developers to generate complete specifications from natural language descriptions with upfront clarifications

**Independent Test**: Run `acpctl specify "feature description"`, answer pre-flight questions, verify specs/NNN-feature/spec.md is created and passes constitutional validation

### Implementation for User Story 2

- [ ] T022 [P] [US2] Create Specification Agent in acpctl/agents/specification.py with LangChain integration
- [ ] T023 [P] [US2] Create Governance Agent in acpctl/agents/governance.py with constitutional validation logic
- [ ] T024 [US2] Implement pre-flight questionnaire logic in Specification Agent (max 10 questions)
- [ ] T025 [US2] Implement spec.md generation in Specification Agent using spec-template.md format
- [ ] T026 [US2] Add LangGraph nodes for specification_agent and governance_agent in acpctl/core/workflow.py
- [ ] T027 [US2] Add conditional edge routing function route_governance() in acpctl/core/workflow.py
- [ ] T028 [US2] Create error handler node for constitutional violations in acpctl/core/workflow.py
- [ ] T029 [US2] Implement interactive violation remediation ([R]egenerate, [E]dit, [A]bort, [I]gnore) in error handler
- [ ] T030 [US2] Create specify command in acpctl/cli/commands/specify.py with feature description argument
- [ ] T031 [US2] Add Rich UI components for pre-flight Q&A display (numbered questions, progress indicators)
- [ ] T032 [US2] Add Rich Panel for constitutional violation display with fix suggestions
- [ ] T033 [US2] Implement feature ID generation (find next sequential number) in specify command
- [ ] T034 [US2] Implement feature directory creation (specs/NNN-feature/) in specify command
- [ ] T035 [US2] Add git branch creation (NNN-feature-name) when git repository detected
- [ ] T036 [US2] Integrate specify command with LangGraph workflow execution and checkpoint saving
- [ ] T037 [US2] Register specify command in acpctl/cli/main.py Typer app

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - `acpctl specify` generates validated specifications

---

## Phase 5: User Story 3 - Resume Interrupted Workflow from Checkpoint (Priority: P2)

**Goal**: Enable developers to resume interrupted workflows from last successful checkpoint without losing progress

**Independent Test**: Start `acpctl specify`, let it complete, interrupt, run `acpctl resume`, verify it continues from correct phase

### Implementation for User Story 3

- [ ] T038 [P] [US3] Create CLI metadata structure (feature_id, thread_id, status, phases_completed) in checkpoint.py
- [ ] T039 [P] [US3] Implement CLI metadata save to .acp/state/NNN-feature.json after each phase in checkpoint.py
- [ ] T040 [US3] Implement CLI metadata load from .acp/state/ in checkpoint.py
- [ ] T041 [US3] Implement status command in acpctl/cli/commands/status.py to display workflow state
- [ ] T042 [US3] Add Rich Table formatting for status output (feature ID, status, current phase, checkpoints)
- [ ] T043 [US3] Implement resume command in acpctl/cli/commands/resume.py with feature ID parameter
- [ ] T044 [US3] Add auto-detection of last workflow if no feature ID specified in resume command
- [ ] T045 [US3] Integrate resume with LangGraph thread_id restoration and workflow continuation
- [ ] T046 [US3] Add phase skip logic (display "Skipping phases: X, Y") in resume command
- [ ] T047 [US3] Implement history command in acpctl/cli/commands/history.py to list all workflows
- [ ] T048 [US3] Add Rich Table formatting for history output (ID, name, status, last checkpoint, timestamp)
- [ ] T049 [US3] Register status, resume, and history commands in acpctl/cli/main.py Typer app

**Checkpoint**: All checkpoint/resume functionality should now work - workflows can be interrupted and resumed at any phase boundary

---

## Phase 6: User Story 4 - Generate Implementation Plan with Architecture Validation (Priority: P2)

**Goal**: Enable developers to generate detailed technical plans including implementation approach, data models, and API contracts

**Independent Test**: With approved spec.md, run `acpctl plan`, verify plan.md, data-model.md, research.md, and contracts/ are generated and validated

### Implementation for User Story 4

- [ ] T050 [P] [US4] Create Architect Agent in acpctl/agents/architect.py with LangChain integration
- [ ] T051 [US4] Implement Phase 0 (Research) logic in Architect Agent (research.md generation)
- [ ] T052 [US4] Implement Phase 1 (Design) logic in Architect Agent (plan.md generation using plan-template.md)
- [ ] T053 [US4] Implement data-model.md generation in Architect Agent
- [ ] T054 [US4] Implement contracts/ generation (API contract YAML files) in Architect Agent
- [ ] T055 [US4] Implement quickstart.md generation in Architect Agent
- [ ] T056 [US4] Add LangGraph nodes for architect_agent (research and design phases) in acpctl/core/workflow.py
- [ ] T057 [US4] Add conditional edge routing for planning phase in acpctl/core/workflow.py
- [ ] T058 [US4] Integrate planning artifacts with constitutional validation (governance gate after planning)
- [ ] T059 [US4] Create plan command in acpctl/cli/commands/plan.py with optional spec_id parameter
- [ ] T060 [US4] Add Rich Progress indicators for Phase 0 (Research) and Phase 1 (Design) in plan command
- [ ] T061 [US4] Add verbose mode output (agent reasoning tables) for planning phases
- [ ] T062 [US4] Register plan command in acpctl/cli/main.py Typer app

**Checkpoint**: Planning workflow should be complete - `acpctl plan` generates all design artifacts validated against constitution

---

## Phase 7: User Story 5 - Generate Code Following Test-Driven Development (Priority: P3)

**Goal**: Enable developers to generate working code with tests following TDD approach

**Independent Test**: With approved plan.md, run `acpctl implement`, verify test files generated first, then implementation files, and all tests pass

### Implementation for User Story 5

- [ ] T063 [P] [US5] Create Implementation Agent in acpctl/agents/implementation.py with LangChain integration
- [ ] T064 [US5] Implement test file generation logic in Implementation Agent (TEST artifacts first)
- [ ] T065 [US5] Implement production code generation logic in Implementation Agent (IMPLEMENTATION artifacts second)
- [ ] T066 [US5] Add test execution integration (pytest runner) in Implementation Agent
- [ ] T067 [US5] Add validation for TDD cycle (tests FAIL before implementation, PASS after)
- [ ] T068 [US5] Integrate code artifacts with constitutional validation (no secrets, license compliance)
- [ ] T069 [US5] Add LangGraph nodes for implementation_agent in acpctl/core/workflow.py
- [ ] T070 [US5] Add conditional edge routing for implementation phase completion in acpctl/core/workflow.py
- [ ] T071 [US5] Create implement command in acpctl/cli/commands/implement.py with optional spec_id parameter
- [ ] T072 [US5] Add Rich Progress indicators for test generation, implementation generation, and test execution
- [ ] T073 [US5] Add test results display (passed/failed counts, failure details) with Rich formatting
- [ ] T074 [US5] Add verbose mode output for implementation agent reasoning
- [ ] T075 [US5] Register implement command in acpctl/cli/main.py Typer app

**Checkpoint**: All user stories should now be independently functional - complete workflow from init through implementation works

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T076 [P] Add schema validation helpers in acpctl/utils/validation.py for Pydantic model validation
- [ ] T077 [P] Implement schema versioning migration logic in acpctl/core/checkpoint.py (v1.0.0 to v2.0.0)
- [ ] T078 [P] Add error retry logic with error_count tracking in workflow.py conditional edges
- [ ] T079 Add comprehensive error messages and user-friendly output across all commands
- [ ] T080 [P] Add --version flag to main CLI app
- [ ] T081 [P] Implement streaming display for agent events using Rich Live display
- [ ] T082 [P] Add .acp/ to .gitignore template generated by init command
- [ ] T083 Code cleanup and refactoring across all modules (consistent naming, documentation)
- [ ] T084 Performance optimization - ensure init <10s, specify <10min, full workflow <30min
- [ ] T085 Run quickstart.md validation scenarios to ensure all examples work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (US1-P1): Initialize - Can start after Foundational, no dependencies on other stories
  - User Story 2 (US2-P1): Specify - Depends on US1 (needs init to exist)
  - User Story 3 (US3-P2): Resume - Depends on US2 (needs checkpoints from specify to test)
  - User Story 4 (US4-P2): Plan - Depends on US2 (needs spec.md to exist)
  - User Story 5 (US5-P3): Implement - Depends on US4 (needs plan.md to exist)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 completion (init must work first)
- **User Story 3 (P2)**: Depends on US2 completion (needs specify workflow to generate checkpoints)
- **User Story 4 (P2)**: Depends on US2 completion (needs spec.md from specify)
- **User Story 5 (P3)**: Depends on US4 completion (needs plan.md from planning)

### Within Each User Story

- Foundation tasks must complete before story-specific implementation
- Agents before commands that use them
- Core workflow nodes before CLI integration
- Rich UI components alongside commands that use them
- Constitutional validation integrated at each phase boundary

### Parallel Opportunities

- **Setup Phase**: T003, T004 can run in parallel (different config files)
- **Foundational Phase**: T008+T009 (UI), T011+T012 (storage), T013+T014+T015 (core setup) can run in parallel
- **User Story 2**: T022+T023 (agents) can run in parallel before T024-T029 (workflow integration)
- **User Story 3**: T038+T039+T040 (checkpoint metadata) can run in parallel
- **User Story 4**: T050 (agent creation) can start in parallel with Rich UI work from previous stories
- **User Story 5**: T063+T064+T065 (implementation agent core) can be developed in parallel
- **Polish Phase**: T076, T077, T078, T080, T081, T082 all target different files and can run in parallel

---

## Parallel Example: User Story 2 (Specify)

```bash
# Launch agent creation tasks in parallel:
Task: "Create Specification Agent in acpctl/agents/specification.py"
Task: "Create Governance Agent in acpctl/agents/governance.py"

# After agents ready, build workflow integration sequentially
Task: "Add LangGraph nodes for specification_agent and governance_agent"
Task: "Add conditional edge routing function route_governance()"
Task: "Create error handler node for constitutional violations"

# Launch Rich UI components in parallel with command:
Task: "Add Rich UI components for pre-flight Q&A display"
Task: "Add Rich Panel for constitutional violation display"
Task: "Create specify command in acpctl/cli/commands/specify.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only - Both P1)

1. Complete Phase 1: Setup → Project structure ready
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) → Core infrastructure ready
3. Complete Phase 3: User Story 1 (Initialize) → Can create constitutional templates
4. Complete Phase 4: User Story 2 (Specify) → Can generate validated specifications
5. **STOP and VALIDATE**: Test `acpctl init` and `acpctl specify` independently
6. Deploy/demo MVP - Already provides value for spec-driven development

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Initialize) → Test independently → Deploy/Demo
3. Add User Story 2 (Specify) → Test independently → Deploy/Demo (MVP with governance!)
4. Add User Story 3 (Resume) → Test independently → Deploy/Demo (resilience added)
5. Add User Story 4 (Plan) → Test independently → Deploy/Demo (architecture automation)
6. Add User Story 5 (Implement) → Test independently → Deploy/Demo (full automation)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Initialize)
   - After US1 complete, Developer A moves to US3 (Resume - needs US2 checkpoints to test)
3. Developer B: User Story 2 (Specify - blocks US3, US4, US5)
4. After US2 complete:
   - Developer C: User Story 4 (Plan - depends on US2)
5. After US4 complete:
   - Developer D: User Story 5 (Implement - depends on US4)
6. Stories complete and integrate in dependency order

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests NOT included per feature specification (no explicit TDD requirement)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow library-first architecture: core/ and agents/ should be testable without CLI
- Avoid: vague tasks, same file conflicts, violation of Constitutional Principles

## Validation Checklist

- ✅ All tasks follow format: `- [ ] [ID] [P?] [Story?] Description with file path`
- ✅ Tasks organized by user story from spec.md (US1-P1, US2-P1, US3-P2, US4-P2, US5-P3)
- ✅ Each user story has independent test criteria
- ✅ Foundation phase (Phase 2) blocks all user stories - clearly marked
- ✅ Dependencies section shows story completion order
- ✅ Parallel opportunities identified with [P] markers
- ✅ MVP scope defined (User Stories 1 & 2)
- ✅ File paths match plan.md project structure
- ✅ Constitutional principles respected in task design
