# acpctl

**Ambient Code Platform (acpctl)** - A LangGraph-based agent system for spec-driven development with constitutional governance.

> Porting GitHub's [spec-kit](https://github.com/github/spec-kit) workflow into an intelligent, governed, multi-agent architecture designed for enterprise engineering at scale.

---

## 🎯 Vision

Transform spec-driven development from a linear CLI workflow into an **intelligent agent orchestration system** that:

- ✅ **Enforces constitutional governance** at every workflow stage
- ✅ **Automatically checkpoints** progress for resume-anywhere capability
- ✅ **Collects requirements upfront** via pre-flight questionnaires (no workflow interruptions)
- ✅ **Provides complete audit trails** for enterprise compliance
- ✅ **Scales to parallel execution** (future phases)

Built for **Red Hat AI Engineering** workflows, designed to be governed, auditable, and enterprise-ready.

---

## 📊 Current Status

**🚧 Design Phase** - UX demo complete, implementation not yet started

### What Exists Now

- ✅ **Complete architecture design** ([speckit-langgraph-architecture.md](./speckit-langgraph-architecture.md))
- ✅ **Detailed Phase 1 implementation plan** ([acpctl-phase1-implementation-plan.md](./acpctl-phase1-implementation-plan.md))
- ✅ **Interactive UX demo** with asciinema recording ([demo/](./demo/))
- ✅ **Project guidance** for future developers ([CLAUDE.md](./CLAUDE.md))

### What's Next

- ⏸️ Implement `ACPState` schema and persistence layer
- ⏸️ Build LangGraph StateGraph workflow
- ⏸️ Implement core agents (Governance, Specification, Architect, Implementation)
- ⏸️ Build CLI framework with all commands
- ⏸️ Add checkpoint/resume functionality

---

## 🎬 Try the UX Demo

See the proposed acpctl user experience in action:

[![asciicast](https://asciinema.org/a/placeholder.svg)](demo/acpctl-demo.cast)

```bash
# Watch the recorded demo locally
asciinema play demo/acpctl-demo.cast

# Or test the mock CLI interactively
./demo/mock-acpctl.py init
./demo/mock-acpctl.py specify "Add OAuth2 authentication to REST API"
./demo/mock-acpctl.py plan --verbose
./demo/mock-acpctl.py status
```

**Demo showcases**:
- Pre-flight questionnaire (4 clarifying questions upfront)
- Constitutional governance gates
- Automatic checkpointing after each phase
- Resume from checkpoint after interruption
- Three verbosity modes (`--quiet`, default, `--verbose`)
- Complete workflow history and audit trail

See [demo/README.md](./demo/README.md) for full details.

---

## 🏗️ Architecture Overview

### From spec-kit to acpctl

**spec-kit** (GitHub's CLI):
```
/speckit.constitution → /speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

**acpctl** (LangGraph agents):
```
Governance → Specify → Governance → Plan → Governance → Implement
    ↓            ↓          ↓         ↓         ↓           ↓
 [Gate]    [Pre-flight]  [Gate]  [Artifacts] [Gate]    [TDD Code]
                                                            ↓
                                                     [Checkpoint]
```

### Core Agents (Phase 1)

1. **Governance Agent** - Constitutional validator
   - Validates artifacts against `.acp/templates/constitution.md`
   - Reports violations with specific line numbers and suggested fixes
   - Gates progression between workflow stages

2. **Specification Agent** - Requirements analyzer
   - Transforms natural language into structured `spec.md`
   - Asks clarifying questions upfront (pre-flight questionnaire)
   - Focuses on "what" and "why", not "how"

3. **Architect Agent** - Technical planner
   - Generates `plan.md`, `data-model.md`, API `contracts/`
   - Selects tech stack following constitutional constraints
   - Designs implementation approach

4. **Implementation Agent** - Code generator
   - Executes plan using TDD approach (tests first)
   - Generates code, tests, documentation
   - Validates against spec and plan

### State Management

Complete workflow state captured in `ACPState` TypedDict:

```python
ACPState = {
    "constitution": "...",           # Governing principles
    "governance_passes": bool,       # Latest validation result
    "feature_description": "...",    # User's request
    "spec": "...",                   # Generated specification
    "plan": "...",                   # Implementation plan
    "data_model": "...",             # Database schema
    "contracts": {...},              # API contracts
    "code_artifacts": {...},         # Generated code
    # ... and more
}
```

Checkpoints saved as JSON in `.acp/state/NNN-feature.json` after each phase.

---

## 🎯 Target User Experience

### Workflow Commands (Not Yet Implemented)

```bash
# Initialize project with constitution
acpctl init

# Generate specification (with pre-flight Q&A)
acpctl specify "Add OAuth2 authentication to our REST API"
# → Asks 4 clarifying questions upfront
# → Generates specs/001-oauth2-auth/spec.md
# → Validates against constitution
# → Saves checkpoint: SPECIFICATION_COMPLETE

# Generate architecture plan
acpctl plan
# → Creates plan.md, data-model.md, contracts/
# → Re-validates against constitution
# → Saves checkpoint: PLANNING_COMPLETE

# Generate implementation
acpctl implement
# → Writes tests first (TDD)
# → Generates code following plan
# → Saves checkpoint: IMPLEMENTATION_COMPLETE

# Check workflow status
acpctl status
# → Shows progress: 60% (PLANNING_COMPLETE)
# → Lists generated artifacts
# → Displays governance check results

# Resume after interruption
acpctl resume
# → Loads latest checkpoint
# → Skips completed phases
# → Continues from breakpoint

# View workflow history
acpctl history
# → Lists all workflows with status
# → Shows checkpoint timestamps
```

### Verbosity Modes

```bash
acpctl plan --quiet              # Minimal: just results
acpctl plan                      # Moderate: phases + sub-tasks (default)
acpctl plan --verbose            # Full: agent reasoning + timing
```

### Generated Artifacts

```
.acp/
├── templates/
│   └── constitution.md          # Project governing principles
└── state/
    └── 001-oauth2-auth.json     # Checkpoint state

specs/001-oauth2-auth/
├── spec.md                      # Functional specification
├── plan.md                      # Implementation plan
├── data-model.md                # Database schema
└── contracts/
    └── oauth2_api.yaml          # API contracts
```

---

## 📚 Key Documents

### Architecture & Design

- **[speckit-langgraph-architecture.md](./speckit-langgraph-architecture.md)**
  - Complete agent architecture (7 agent types)
  - LangGraph StateGraph design
  - Strategic rationale for Red Hat context
  - Comparison with original spec-kit

- **[acpctl-phase1-implementation-plan.md](./acpctl-phase1-implementation-plan.md)**
  - Detailed Phase 1 implementation plan
  - Week-by-week sequence
  - Technology stack (LangGraph, LangChain, Click/Typer, Rich, Pydantic)
  - Validation criteria for completion
  - Phase 1 vs Phase 2 scope boundaries

### Demo & Development

- **[demo/README.md](./demo/README.md)**
  - UX demonstration details
  - How to view/re-record asciinema demo
  - Mock CLI testing instructions

- **[CLAUDE.md](./CLAUDE.md)**
  - Guidance for AI-assisted development
  - Architecture principles
  - Implementation conventions

---

## 🎨 Design Principles

1. **Specifications as First-Class Artifacts**
   - Code serves specs, not the other way around
   - Specs are versioned, reviewed, and enforced

2. **Constitutional Governance**
   - Every artifact validated against project principles
   - Violations reported with actionable fixes
   - Gates prevent progression until compliance achieved

3. **Checkpoint Everything**
   - State persists after every phase completion
   - Workflows can be interrupted and resumed anywhere
   - Complete audit trail for enterprise compliance

4. **Pre-flight Over Interruption**
   - All clarifications collected upfront
   - No mid-workflow interruptions
   - Smoother execution, better planning

5. **Progressive Disclosure**
   - Three verbosity modes for different needs
   - Quiet for automation, verbose for debugging
   - Moderate (default) balances visibility and clarity

6. **Human-in-the-Loop at Strategic Gates**
   - Approval required at constitutional validation points
   - Clarifications during specification phase
   - Override capability with `--force` flag

---

## 🚀 Phase Roadmap

### Phase 1: Core Sequential Flow (Current Target)

**Scope**: Linear workflow with constitutional gates

- Sequential agent execution (no parallelism)
- Pre-flight questionnaire for specifications
- Checkpoint/resume functionality
- Constitutional governance at phase boundaries
- Professional UX with 3 verbosity modes

**Validation Criteria**:
- ✅ Full workflow runs end-to-end
- ✅ Constitutional violations caught 100% of the time
- ✅ Checkpoints save/resume correctly
- ✅ Pre-flight questionnaire works without interruptions
- ✅ All acpctl commands functional

### Phase 2: Add Intelligence (Future)

**Scope**: Parallel execution and advanced agents

- Research agent with parallel fanout
- Task decomposition with dependency analysis
- Validation agent with rework loops
- Performance optimization
- Multi-model coordination (different LLMs for different agents)

### Phase 3: Enterprise Integration (Future)

**Scope**: Red Hat-specific production readiness

- Internal tool integration (Jira, Confluence, internal registries)
- Red Hat compliance automation
- Multi-team coordination
- Production CI/CD integration

---

## 🎯 Strategic Value for Red Hat

### Alignment with Red Hat AI Engineering Mission

- **Governed Development**: Constitutional principles enforce security, licensing, architectural standards
- **Audit Trails**: Complete state history for compliance and debugging
- **Resume-from-Failure**: Critical for long-running enterprise workflows
- **Scale**: Parallel execution (Phase 2+) leverages enterprise compute
- **Trust**: Spec-driven approach with validation gates ensures quality

### Differentiation from spec-kit

LangGraph enables capabilities spec-kit cannot provide:

- **Dynamic Routing**: Smart decisions about when to skip/repeat phases
- **Parallel Execution**: Concurrent research and implementation
- **State Checkpointing**: Resume across sessions, even after crashes
- **Multi-Model Coordination**: Optimize cost/performance per agent type
- **Human-in-the-Loop Gates**: Strategic approval points, not just clarification

---

## 📖 Background: What is spec-kit?

[GitHub's spec-kit](https://github.com/github/spec-kit) is a CLI tool that enforces spec-driven development through a linear workflow:

1. **Constitution** - Define project principles
2. **Specify** - Write functional specifications
3. **Plan** - Create technical implementation plans
4. **Tasks** - Break down into actionable work items
5. **Implement** - Execute with validation against specs

**spec-kit philosophy**: "Specifications as executable artifacts" - code must conform to specs, not the reverse.

**acpctl** preserves this philosophy while adding:
- Agent-based intelligence
- Parallel execution capability
- Constitutional enforcement at every stage
- Enterprise-grade checkpointing and audit trails

---

## 🤝 Contributing

This project is in the design phase. Contributions welcome for:

- Architecture feedback and improvements
- UX demo enhancements
- Documentation clarifications
- Phase 1 implementation (coming soon)

---

## 📄 License

*(License to be determined)*

---

## 🔗 References

- **GitHub spec-kit**: https://github.com/github/spec-kit
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **LangChain Documentation**: https://python.langchain.com/

---

**Status**: 🚧 Design Phase | **Next Milestone**: Phase 1 Implementation Kickoff

*Built for Red Hat AI Engineering by Jeremy Eder, Distinguished Engineer*
