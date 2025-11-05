# acpctl Quickstart Guide

**Feature**: Governed Spec-Driven Development CLI
**Version**: 1.0.0
**Last Updated**: 2025-11-05

Get started with acpctl in 5 minutes. This guide walks through the complete workflow from initialization to code generation.

---

## Prerequisites

- Python 3.11 or higher
- Git repository (recommended but not required)
- Terminal with color support for Rich UI

---

## Installation

```bash
# Install from source (Phase 1)
git clone https://github.com/your-org/acpctl.git
cd acpctl
pip install -e .

# Verify installation
acpctl --version
# Output: acpctl version 1.0.0
```

---

## 5-Minute Workflow

### Step 1: Initialize Project (30 seconds)

```bash
# Navigate to your project directory
cd my-project

# Initialize acpctl with constitutional governance
acpctl init

# Output:
# ✓ Created .acp/templates/constitution.md
# Next: Edit constitution to define project principles
```

**What happened?**
- Created `.acp/` directory structure
- Generated constitutional template with example principles
- Ready to define your project's governance rules

**Edit the constitution** (optional but recommended):
```bash
# Open constitution template
vim .acp/templates/constitution.md

# Define your principles (or keep examples):
# - Security requirements
# - Licensing constraints
# - Architectural standards
# - Testing requirements
```

---

### Step 2: Generate Specification (2 minutes)

```bash
# Describe your feature in natural language
acpctl specify "Add OAuth2 authentication for user login with Google and GitHub providers"

# Interactive pre-flight questionnaire:
# Q1: Should authentication support session cookies or JWT tokens?
# A1: JWT tokens with refresh token rotation

# Q2: What user information should be stored after authentication?
# A2: Email, name, profile picture URL, and OAuth provider ID

# Q3: How should authentication errors be handled?
# A3: Return 401 with error message, log to monitoring system

# Output:
# ✓ Pre-flight questionnaire: 3 questions answered
# ✓ Specification generated: specs/001-oauth-auth/spec.md
# ✓ Constitutional validation: PASS
# ✓ Feature branch created: 001-oauth-auth
# Next: Run 'acpctl plan' to generate implementation plan
```

**What happened?**
- Specification Agent analyzed your description
- Identified ambiguities and asked clarifying questions
- Generated `specs/001-oauth-auth/spec.md` with:
  - User scenarios and acceptance criteria
  - Functional requirements (no implementation details)
  - Success criteria
- Validated against constitutional principles
- Created feature branch `001-oauth-auth`

---

### Step 3: Generate Implementation Plan (1 minute)

```bash
# Generate technical plan and architecture
acpctl plan

# Output:
# Phase 0: Research
# ✓ Researching OAuth2 best practices...
# ✓ Researching JWT token security...
# ✓ Research complete: research.md

# Phase 1: Design
# ✓ Generating implementation plan...
# ✓ Generating data model...
# ✓ Generating API contracts...
# ✓ Constitutional validation: PASS

# Artifacts created:
# - specs/001-oauth-auth/plan.md
# - specs/001-oauth-auth/research.md
# - specs/001-oauth-auth/data-model.md
# - specs/001-oauth-auth/contracts/auth-api.yaml
# - specs/001-oauth-auth/quickstart.md

# Next: Run 'acpctl implement' to generate code
```

**What happened?**
- **Phase 0 (Research)**: Architect Agent researched OAuth2 patterns, JWT security, session management
- **Phase 1 (Design)**:
  - Generated `plan.md` with implementation approach
  - Generated `data-model.md` defining entities (User, AuthSession, OAuth Provider)
  - Generated `contracts/` with API endpoint definitions
- Validated all artifacts against constitution
- Updated agent context with new technology decisions

---

### Step 4: Generate Code with TDD (1 minute)

```bash
# Generate tests and implementation
acpctl implement

# Output:
# ✓ Generating test files...
#   - tests/unit/test_auth_service.py (15 tests)
#   - tests/integration/test_oauth_flow.py (8 tests)

# ✓ Generating implementation files...
#   - acpctl/services/auth_service.py
#   - acpctl/models/user.py
#   - acpctl/lib/oauth_client.py

# ✓ Running tests...
#   23 tests, 23 passed, 0 failed

# ✓ Constitutional validation: PASS
#   - No secrets in code ✓
#   - Open source licenses ✓
#   - Test coverage 87% (target: 80%) ✓

# Next: Review generated code and commit changes
```

**What happened?**
- Implementation Agent generated test files first (TDD)
- Generated implementation code that makes tests pass
- Ran all tests automatically (100% pass rate)
- Validated code against constitutional principles
- Code is ready to review and commit

---

## Checkpoint & Resume Example

### Scenario: Workflow Interrupted

```bash
# Start workflow
acpctl specify "Add payment processing with Stripe integration"

# ... pre-flight questionnaire answered ...
# ✓ Specification complete
# Checkpoint saved: .acp/state/002-payment.json

# [Process interrupted - laptop closes, network failure, etc.]

# Resume from checkpoint (later)
acpctl resume

# Output:
# Resuming workflow 002-payment from checkpoint: SPECIFICATION_COMPLETE
# Skipping phases: INIT, SPECIFICATION
# Continuing from: PLANNING
# Phase 0: Research...
```

**Key Features:**
- Automatic checkpoint after each phase
- No state loss on interruption
- Skips completed phases on resume
- Preserves all pre-flight Q&A answers

---

## Verbosity Modes

### Quiet Mode (Errors Only)
```bash
acpctl specify "Add admin dashboard" --quiet

# Output: (silent until completion or error)
```

### Default Mode (Progress Indicators)
```bash
acpctl plan

# Output:
# Phase 0: Research [████████████████░░░░] 75%
# Phase 1: Design  [██░░░░░░░░░░░░░░░░░░] 10%
```

### Verbose Mode (Full Agent Reasoning)
```bash
acpctl plan --verbose

# Output:
# ╔═══════════════════════════════════════════════╗
# ║          Agent Execution Trace                ║
# ╠═══════════════════╦═══════════╦═══════════════╣
# ║ Node              ║ Action    ║ Details       ║
# ╠═══════════════════╬═══════════╬═══════════════╣
# ║ governance_agent  ║ → Process ║ Input: const  ║
# ║ governance_agent  ║ ✓ Complete║ Updated: pass ║
# ║ architect_agent   ║ → Process ║ Input: spec   ║
# ...
```

---

## Status & History Commands

### Check Current Status
```bash
acpctl status

# Output:
# Feature: 002-payment (payment-processing)
# Status: IN_PROGRESS
# Current Phase: PLANNING
# Last Checkpoint: SPECIFICATION_COMPLETE
# Phases Completed: INIT, SPECIFICATION
# Next Phase: PLANNING
# Created: 2025-01-05 12:00:00
# Last Updated: 2025-01-05 12:15:00
```

### List All Workflows
```bash
acpctl history

# Output:
# ┌──────────┬──────────────────┬────────────┬─────────────────────┐
# │ ID       │ Name             │ Status     │ Last Checkpoint     │
# ├──────────┼──────────────────┼────────────┼─────────────────────┤
# │ 001      │ oauth-auth       │ COMPLETED  │ IMPLEMENTATION_COMP │
# │ 002      │ payment          │ IN_PROGRESS│ SPECIFICATION_COMP  │
# │ 003      │ admin-dashboard  │ PAUSED     │ PLANNING_COMPLETE   │
# └──────────┴──────────────────┴────────────┴─────────────────────┘
```

---

## Constitutional Violation Handling

### Example: Violation Detected

```bash
acpctl specify "Build REST API using PostgreSQL database"

# Output:
# ✓ Pre-flight questionnaire: 2 questions answered
# ✗ Specification generated but constitutional violation detected

# Violation Report:
# ┌────────────────────────────────────────────────────────────┐
# │ Principle: I. Specifications as First-Class Artifacts     │
# │ File: specs/004-rest-api/spec.md                          │
# │ Line: 42                                                   │
# │ Issue: Implementation detail in specification             │
# │                                                            │
# │ Found: "using PostgreSQL database"                        │
# │ Fix:   Remove database technology; describe data needs:   │
# │        "persistent storage for relational data"           │
# └────────────────────────────────────────────────────────────┘

# Choose action:
# [R] Regenerate specification with fix
# [E] Edit constitution to allow this
# [A] Abort workflow
# [I] Ignore and proceed (--force)

# User selects: R

# Regenerating specification...
# ✓ Specification regenerated: specs/004-rest-api/spec.md
# ✓ Constitutional validation: PASS
# (Pre-flight questions NOT re-asked - answers preserved)
```

**Key Features:**
- Specific file and line number
- Principle violated clearly stated
- Actionable fix suggestion
- Interactive remediation options
- Preserves answered questions on regeneration

---

## Project Structure After Workflow

```
my-project/
├── .acp/                                # acpctl runtime directory
│   ├── templates/
│   │   └── constitution.md              # Project principles
│   └── state/
│       ├── 001-oauth-auth.json          # Checkpoint metadata
│       └── 002-payment.json
│
├── specs/                               # Generated specifications
│   ├── 001-oauth-auth/
│   │   ├── spec.md                      # Functional specification
│   │   ├── plan.md                      # Implementation plan
│   │   ├── research.md                  # Research decisions
│   │   ├── data-model.md                # Entity definitions
│   │   ├── quickstart.md                # Getting started guide
│   │   └── contracts/
│   │       └── auth-api.yaml            # API contract
│   └── 002-payment/
│       └── ...
│
└── acpctl/                              # Generated code (example)
    ├── services/
    │   └── auth_service.py              # Implementation
    ├── models/
    │   └── user.py
    └── tests/
        ├── unit/
        │   └── test_auth_service.py     # Tests (TDD)
        └── integration/
            └── test_oauth_flow.py
```

---

## Common Patterns

### Pattern 1: Iterate on Specification
```bash
# Generate initial spec
acpctl specify "Add search functionality"

# Review spec.md, realize more clarification needed
# Re-run with additional context
acpctl specify "Add search functionality with fuzzy matching and filters" --regenerate

# Pre-flight questions will reflect new context
```

### Pattern 2: Review Before Implementation
```bash
# Generate spec and plan only
acpctl specify "Add caching layer"
acpctl plan

# Review specs/NNN-caching/plan.md
# Make manual edits if needed

# Then implement
acpctl implement
```

### Pattern 3: Resume Specific Workflow
```bash
# List all workflows
acpctl history

# Resume specific one
acpctl resume 003

# Or by name
acpctl resume admin-dashboard
```

---

## Tips & Best Practices

### 1. Edit Constitution First
Define your project's principles before generating specs. This ensures all artifacts follow your standards from the start.

### 2. Be Specific in Feature Descriptions
Better: "Add OAuth2 authentication with Google and GitHub providers, using JWT tokens"
Worse: "Add login"

### 3. Answer Pre-flight Questions Thoughtfully
These answers shape the entire specification. Take time to consider implications.

### 4. Review Generated Artifacts
acpctl generates drafts. Always review `spec.md` and `plan.md` before implementation.

### 5. Use Verbose Mode for Learning
Run with `--verbose` to see agent reasoning and understand decisions.

### 6. Commit Frequently
```bash
# After each phase
git add .acp/ specs/
git commit -m "feat(spec): add OAuth authentication specification"

git add acpctl/
git commit -m "feat(auth): implement OAuth2 authentication"
```

---

## Troubleshooting

### Issue: "No checkpoint found"
**Cause**: Workflow was never started or checkpoint file deleted
**Solution**: Start new workflow with `acpctl specify`

### Issue: Constitutional violations persist
**Cause**: Constitution may be too restrictive or unclear
**Solution**:
1. Review `.acp/templates/constitution.md`
2. Either clarify principle or adjust if too strict
3. Use `[E]dit constitution` option in violation prompt

### Issue: Pre-flight questionnaire has too many questions
**Cause**: Feature description is too vague or ambitious
**Solution**: Narrow scope or provide more context in description

---

## What's Next?

### Phase 2 Features (Future)
- Parallel research agents for faster planning
- Task decomposition with dependency graphs
- Validation agent with automatic rework loops
- Team collaboration (shared checkpoints)

### Integration (Future)
- CI/CD pipeline integration
- Jira/Confluence sync
- Enterprise approval workflows

---

## Getting Help

```bash
# CLI help
acpctl --help
acpctl specify --help

# Check documentation
cat specs/001-feature/README.md

# View this guide
cat specs/001-feature/quickstart.md
```

---

## Summary

**acpctl Workflow**:
1. `acpctl init` → Define governance
2. `acpctl specify` → Generate spec with pre-flight Q&A
3. `acpctl plan` → Research + design artifacts
4. `acpctl implement` → TDD code generation
5. Review, commit, deploy

**Key Advantages**:
- ✅ Constitutional governance ensures compliance
- ✅ Pre-flight Q&A eliminates interruptions
- ✅ Automatic checkpoints enable resume
- ✅ TDD approach ensures quality
- ✅ Complete audit trail for compliance

Start with a small feature, learn the workflow, then scale to complex projects. acpctl handles the tedious parts so you focus on requirements and architecture.
