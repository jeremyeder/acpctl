# Phase 1: acpctl Implementation Plan

**Date**: 2025-11-04
**Purpose**: Detailed implementation plan for Phase 1 of acpctl (Ambient Code Platform CLI)

---

## Project Setup

- Initialize Python project structure for `acpctl` CLI
- Set up LangGraph dependencies and state management
- Create `.acp/` directory structure for constitutions and state

---

## Core Components (Priority Order)

### 1. State Schema & Persistence (Foundation)

**Purpose**: Define the complete workflow state and enable checkpoint/resume functionality

**Tasks**:
- Define `ACPState` TypedDict with all workflow layers:
  - Constitution layer (constitution text, governance passes)
  - Specification layer (feature description, spec, clarifications)
  - Planning layer (unknowns, research, plan, data model, contracts)
  - Task layer (tasks, dependencies, parallel batches)
  - Implementation layer (completed tasks, code artifacts, validation status)
- Implement JSON-based checkpoint save/load system
- Build state transition logic for phase progression
- Create state inspection utilities

**Validation**:
- State can be serialized to JSON
- State can be loaded from JSON checkpoint
- State transitions are deterministic

---

### 2. CLI Framework (acpctl commands)

**Purpose**: Provide user-facing command interface matching spec-kit familiarity

**Commands to implement**:
- **`init`** - Create constitution template in `.acp/templates/`
- **`specify`** - Specification generation with pre-flight Q&A
- **`plan`** - Architecture planning from specification
- **`implement`** - Code generation from plan
- **`status`** - Display current workflow progress and artifacts
- **`resume`** - Resume workflow from last checkpoint
- **`history`** - List all workflow runs with status

**Global flags**:
- `--quiet` / `-q` - Minimal output (just phase transitions)
- `--verbose` / `-v` - Full agent reasoning streaming
- Default: Moderate verbosity (phases + sub-tasks)

**Validation**:
- All commands parse arguments correctly
- Verbosity flags work across all commands
- Help text is clear and accurate

---

### 3. Agent Implementations (Sequential)

**Purpose**: Implement the core LangGraph agents for each workflow phase

#### 3.1 Governance Agent

**Role**: Constitutional validator with violation reporting

**Inputs**:
- Constitution.md
- Current artifact (spec, plan, code)

**Outputs**:
- Pass/fail decision
- Violation reports with specific line numbers
- Suggested fixes

**Key capabilities**:
- Pattern matching against constitutional principles
- Clear violation reporting
- Actionable recommendations

#### 3.2 Specification Agent

**Role**: Requirements analyzer with pre-flight questionnaire

**Inputs**:
- Natural language feature description
- User answers to clarifying questions

**Outputs**:
- spec.md with user stories, acceptance criteria, edge cases

**Key capabilities**:
- Identify ambiguities and unknowns
- Generate clarifying questions
- Collect all questions upfront (pre-flight)
- Avoid making assumptions

#### 3.3 Architect Agent

**Role**: Technical planner

**Inputs**:
- spec.md
- constitution.md
- Research findings (Phase 2)

**Outputs**:
- plan.md - Implementation approach
- data-model.md - Database schema, types
- contracts/ - API contracts, interfaces
- quickstart.md - Getting started guide

**Key capabilities**:
- Tech stack selection (following constitution)
- API design
- Data modeling
- Breaking down implementation phases

#### 3.4 Implementation Agent

**Role**: Code generator with TDD approach

**Inputs**:
- plan.md
- spec.md
- All supporting documentation

**Outputs**:
- Code files
- Test files
- Documentation updates

**Key capabilities**:
- Test-driven development (write tests first)
- Code generation following plan
- Tool use (file operations, git, linters)

**Validation**:
- Each agent produces expected outputs
- Agents respect constitutional constraints
- Agent reasoning is traceable

---

### 4. LangGraph Workflow Orchestration

**Purpose**: Connect agents into intelligent workflow with conditional routing

**Tasks**:
- Build StateGraph with these nodes:
  - `governance_check` - Validate against constitution
  - `specify` - Generate specification
  - `architect` - Create implementation plan
  - `implement` - Generate code

- Implement conditional edges:
  - After `governance_check`: Route to next phase if passed, else halt with violation report
  - Between phases: Re-validate against constitution
  - Entry point: `governance_check`
  - Exit point: After implementation complete

- Add checkpoint hooks:
  - After `SPECIFICATION_COMPLETE`
  - After `PLANNING_COMPLETE`
  - After `IMPLEMENTATION_COMPLETE`

- Create resume-from-checkpoint logic:
  - Load state from JSON
  - Skip completed phases
  - Continue from last checkpoint

**Validation**:
- Workflow executes end-to-end
- Constitutional violations halt workflow
- Checkpoints save at correct points
- Resume loads correct state

---

### 5. UX Polish

**Purpose**: Create professional, informative user experience

**Features**:

#### 5.1 Progress Indicators
- Phase transitions with emoji/symbols (⚙️ ✅ 💾 ✨)
- Sub-task progress for moderate verbosity
- Spinners for long-running operations
- Clear section headers using box drawing characters

#### 5.2 Verbose Mode (`--verbose`)
- Stream agent reasoning in real-time
- Show all sub-steps and decisions
- Display file operations
- Include timing information

#### 5.3 Quiet Mode (`--quiet`)
- Only show final results
- Minimal progress indicators
- One-line status updates

#### 5.4 Constitutional Violation Handling
- Clear violation messages with:
  - Which principle was violated
  - Where in the artifact (file:line)
  - Why it's a violation
  - Suggested fix
- Interactive options:
  - `[R]egenerate` - Re-run agent with fix
  - `[E]dit constitution` - Modify principle
  - `[A]bort` - Stop workflow
  - `[I]gnore` - Override (requires `--force`)

**Validation**:
- Output is readable and professional
- Progress is clear at all verbosity levels
- Errors are actionable

---

## Validation Criteria

Phase 1 is complete when:

- ✅ Can run full workflow: `acpctl init → specify → plan → implement`
- ✅ Pre-flight questionnaire collects all clarifications upfront
- ✅ Constitutional violations are caught and reported with clear guidance
- ✅ Checkpoints save automatically after each phase
- ✅ Workflow can be interrupted and resumed from checkpoint
- ✅ Verbosity flags (`--quiet`, `--verbose`) work as expected
- ✅ Generated artifacts match spec-kit directory structure:
  ```
  specs/NNN-feature/
  ├── spec.md
  ├── plan.md
  ├── data-model.md
  └── contracts/
  ```
- ✅ Complete workflow can be audited via state inspection
- ✅ UX is polished and professional

---

## Phase 1 Scope Boundaries

### What's Included ✅

- Sequential workflow (no parallelism)
- Constitutional governance at phase boundaries
- Pre-flight questionnaire for specifications
- Checkpoint/resume functionality
- All core acpctl commands
- Basic agent implementations
- Professional UX with configurable verbosity

### What's Deferred to Phase 2 ❌

- Parallel research agent fanout
- Task decomposition with dependency analysis
- Parallel implementation workers
- Validation agent with rework loops
- Advanced enterprise integrations (Red Hat specific)
- Performance optimization
- Multi-model coordination

---

## Technology Stack

**Core Dependencies**:
- **LangGraph** - Agent orchestration and state management
- **LangChain** - Agent framework and tool integration
- **Click** or **Typer** - CLI framework
- **Rich** - Terminal formatting and progress indicators
- **Pydantic** - Type validation for state schema

**Development Dependencies**:
- **pytest** - Testing framework
- **black** - Code formatting
- **isort** - Import sorting
- **mypy** - Type checking

---

## Project Structure

```
acpctl/
├── pyproject.toml              # Project metadata and dependencies
├── README.md                   # Project documentation
├── .acp/                       # User-facing directory
│   ├── templates/              # Constitution and templates
│   ├── state/                  # Checkpoint files
│   └── memory/                 # Agent memory (Phase 2)
├── src/
│   └── acpctl/
│       ├── __init__.py
│       ├── cli.py              # Click/Typer CLI entry point
│       ├── state.py            # ACPState schema and persistence
│       ├── workflow.py         # LangGraph StateGraph definition
│       ├── agents/             # Agent implementations
│       │   ├── __init__.py
│       │   ├── governance.py
│       │   ├── specification.py
│       │   ├── architect.py
│       │   └── implementation.py
│       ├── ui/                 # User interface utilities
│       │   ├── __init__.py
│       │   ├── progress.py     # Progress indicators
│       │   └── formatting.py   # Rich formatting utilities
│       └── utils/              # Shared utilities
│           ├── __init__.py
│           └── checkpoint.py   # Checkpoint save/load
├── tests/                      # Test suite
│   ├── test_state.py
│   ├── test_agents.py
│   ├── test_workflow.py
│   └── test_cli.py
└── demo/                       # UX demo (already created)
    ├── mock-acpctl.py
    ├── record-demo.sh
    ├── acpctl-demo.cast
    └── README.md
```

---

## Implementation Sequence

1. **Week 1: Foundation**
   - Set up project structure
   - Define `ACPState` schema
   - Implement checkpoint save/load
   - Build basic CLI skeleton

2. **Week 2: Agents**
   - Implement Governance Agent
   - Implement Specification Agent with pre-flight Q&A
   - Implement Architect Agent
   - Implement basic Implementation Agent

3. **Week 3: Workflow**
   - Build LangGraph StateGraph
   - Connect agents with conditional edges
   - Add checkpoint hooks
   - Implement resume logic

4. **Week 4: Polish**
   - Add progress indicators
   - Implement verbosity modes
   - Polish constitutional violation reporting
   - Write tests and documentation

---

## Success Metrics

**Functional**:
- Workflow completes end-to-end for sample OAuth2 feature
- All checkpoints save and resume correctly
- Constitutional violations are caught 100% of the time

**Quality**:
- Test coverage > 80%
- Type hints on all public APIs
- Documentation covers all commands

**UX**:
- User can understand workflow progress without reading code
- Errors are actionable within 30 seconds
- Verbosity modes meet different user needs

---

## Next Steps After Phase 1

Once Phase 1 validation criteria are met:

1. **User Testing** - Get feedback from Red Hat engineers
2. **Performance Benchmarking** - Compare to spec-kit baseline
3. **Phase 2 Planning** - Design parallel execution and task decomposition
4. **Enterprise Hardening** - Add Red Hat-specific integrations

---

## References

- [Architecture Document](./speckit-langgraph-architecture.md)
- [UX Demo](./demo/README.md)
- [GitHub spec-kit](https://github.com/github/spec-kit)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
