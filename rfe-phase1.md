# acpctl Phase 1: Sequential Governed Workflow MVP

**Feature Overview:**

acpctl Phase 1 delivers a minimal viable product (MVP) of the Ambient Code Platform CLI—a sequential, LangGraph-based agent system that validates GitHub's spec-kit workflow concept with constitutional governance and checkpoint/resume capabilities. This phase focuses on proving the core architecture with a linear workflow (Governance → Specification → Architecture → Implementation) before adding parallel execution and advanced features in Phase 2+. Red Hat engineering teams will gain a working system that transforms feature descriptions into validated code artifacts while enforcing organizational principles and providing complete audit trails.

**Goals:**

* **Prove Constitutional Governance Concept**: Validate that automated enforcement of organizational principles (security, licensing, architecture) at workflow phase boundaries catches violations reliably and provides actionable remediation guidance.

* **Establish Sequential Workflow Foundation**: Build working LangGraph StateGraph connecting four core agents (Governance, Specification, Architect, Implementation) with deterministic state transitions and conditional routing.

* **Deliver Checkpoint/Resume Capability**: Enable workflow interruption and resumption without context loss—critical validation for long-running enterprise workflows planned in Phase 2+.

* **Achieve spec-kit Feature Parity**: Match original spec-kit command structure (init, specify, plan, implement) and artifact generation (spec.md, plan.md, data-model.md, contracts/) to ensure familiar migration path.

* **Validate Pre-flight Questionnaire UX**: Test hypothesis that upfront clarification collection (before workflow starts) eliminates mid-workflow interruptions and improves agent output quality.

**Out of Scope:**

* **Parallel Execution**: Research agent fanout, parallel implementation workers, concurrent task execution (Phase 2)
* **Task Decomposition**: Dependency graph analysis, parallel batch identification (Phase 2)
* **Validation Agent**: Automated rework loops, gap analysis, semantic comparison (Phase 2)
* **Research Agent**: Unknown resolution, documentation analysis, web search (Phase 2)
* **Enterprise Integrations**: Red Hat internal systems (Confluence, Jira, approval workflows) (Phase 3)
* **Multi-Model Coordination**: Different LLMs for different agents, cost optimization (Phase 2)
* **Performance Optimization**: Large codebase handling, speed improvements (Phase 2)

**Requirements:**

**MVP Requirements (Phase 1 Completion Criteria):**

* **CLI Framework** (MVP): Implement 6 core commands using Click or Typer:
  - `acpctl init` - Create .acp/ directory structure with constitution.md template
  - `acpctl specify "<description>"` - Generate specification with pre-flight Q&A
  - `acpctl plan` - Generate architecture artifacts from specification
  - `acpctl implement` - Generate code from architecture plan
  - `acpctl status` - Display current workflow state and progress
  - `acpctl resume [spec-id]` - Resume from last checkpoint

  Each command must support `--quiet`/`-q` (minimal output) and `--verbose`/`-v` (full agent reasoning) flags.

* **ACPState Schema** (MVP): Define complete TypedDict in state.py with these layers:
  - Constitution layer: `constitution: str`, `governance_passes: bool`
  - Specification layer: `feature_description: str`, `spec: str`, `clarifications: List[str]`
  - Planning layer: `unknowns: List[str]`, `research: str`, `plan: str`, `data_model: str`, `contracts: dict`
  - Implementation layer: `completed_tasks: List[str]`, `code_artifacts: dict`, `validation_status: str`

  State must serialize to/from JSON without data loss and support deterministic transitions.

* **Checkpoint Persistence** (MVP): Implement automatic state saving to `.acp/state/NNN-feature.json` after:
  - `SPECIFICATION_COMPLETE` - spec.md generated and governance validated
  - `PLANNING_COMPLETE` - plan.md, data-model.md, contracts/ generated and validated
  - `IMPLEMENTATION_COMPLETE` - Code generated with tests passing

  Resume logic must load checkpoint, skip completed phases, continue from breakpoint.

* **Governance Agent** (MVP): Implement constitutional validator with these capabilities:
  - Input: constitution.md (project principles), artifact to validate (spec.md, plan.md, code)
  - Output: Pass/fail decision, violation list with file:line references, suggested fixes
  - Validation logic: Pattern matching against principles (security, licensing, architecture)
  - Interactive remediation: Present options [R]egenerate, [E]dit constitution, [A]bort, [I]gnore (requires --force)

  Agent must catch 100% of constitutional violations in test scenarios.

* **Specification Agent** (MVP): Implement requirements analyzer with pre-flight questionnaire:
  - Input: Natural language feature description
  - Phase 1 (Pre-flight): Identify all ambiguities, generate clarifying questions, collect user answers
  - Phase 2 (Generation): Generate specs/NNN-feature/spec.md with user stories, acceptance criteria, edge cases
  - Output: Structured spec.md validated against constitution
  - Constraint: Zero mid-workflow interruptions after pre-flight phase completes

* **Architect Agent** (MVP): Implement technical planner generating four artifacts:
  - `plan.md` - Implementation approach, tech stack, phases
  - `data-model.md` - Database schemas, type definitions
  - `contracts/api.yaml` (or similar) - API endpoints, interfaces
  - `quickstart.md` - Getting started guide

  All artifacts validated against constitution before phase completion.

* **Implementation Agent** (MVP): Implement code generator with TDD approach:
  - Input: plan.md, spec.md, constitution.md
  - Phase 1 (Tests): Generate test files first (e.g., test_oauth_flow.py)
  - Phase 2 (Code): Generate implementation passing tests (e.g., oauth_handler.py)
  - Tool access: File operations (create, edit), git commands (branch, commit)
  - Output: Working code artifacts with >80% test coverage

* **LangGraph Workflow** (MVP): Build StateGraph in workflow.py connecting agents:
  ```python
  # Nodes
  - governance_check (conditional entry/exit from each phase)
  - specify (specification generation)
  - architect (planning artifacts generation)
  - implement (code generation)

  # Edges
  - Entry: governance_check (validate constitution exists)
  - specify → governance_check (validate spec)
  - governance_check → architect (if spec passes)
  - architect → governance_check (validate plan)
  - governance_check → implement (if plan passes)
  - implement → END (after implementation complete)

  # Conditional routing
  - governance_check: Continue if passes, halt with violation report if fails
  ```

* **Rich Terminal UX** (MVP): Implement professional formatting using Rich library:
  - Phase transitions: Clear headers with emoji indicators (⚙️ Specifying, ✅ Complete, 💾 Checkpoint saved)
  - Verbosity modes:
    - `--quiet`: Only phase names and final results
    - Default: Phase names + sub-task bullets + progress indicators
    - `--verbose`: Full agent reasoning stream + timing + file operations
  - Progress indicators: Spinners for long operations, progress bars for multi-step phases
  - Error formatting: Box-drawn violation reports with color coding

**Post-MVP Requirements (Nice-to-Have for Phase 1):**

* **acpctl history** (Post-MVP): List all workflow runs with timestamps, status, checkpoint availability
* **Artifact numbering**: Auto-increment spec IDs (001, 002, 003...) with persistent counter
* **Git integration**: Automatic feature branch creation, commit message generation
* **Violation categories**: Group violations by type (security, licensing, architecture) in reports
* **State inspection**: `acpctl inspect <checkpoint.json>` utility for debugging

**Done - Acceptance Criteria:**

Phase 1 is complete when all these criteria pass:

1. **End-to-End OAuth2 Workflow**: Developer runs sequence `acpctl init → acpctl specify "Add OAuth2 authentication with Google and GitHub providers" → acpctl plan → acpctl implement` and receives:
   - specs/001-oauth2-auth/spec.md with user stories and acceptance criteria
   - specs/001-oauth2-auth/plan.md with implementation phases
   - specs/001-oauth2-auth/data-model.md with user table schema
   - specs/001-oauth2-auth/contracts/auth-api.yaml with OAuth endpoints
   - Working code files: oauth_handler.py, token_manager.py
   - Passing tests: test_oauth_flow.py with >80% coverage

2. **Constitutional Violation Detection**: Workflow correctly halts when:
   - Specification suggests localStorage token storage (security violation)
   - Plan includes unapproved dependency (licensing violation)
   - Code uses deprecated API pattern (architecture violation)

   Each violation report includes: violated principle name, file:line reference, violation explanation, suggested fix.

3. **Checkpoint Resume After Interruption**:
   - Workflow interrupted during planning phase (Ctrl+C, network timeout, laptop close)
   - `acpctl status` shows "Workflow 001-oauth2-auth: PLANNING incomplete. Last checkpoint: SPECIFICATION_COMPLETE"
   - `acpctl resume` loads checkpoint, skips specification phase, resumes planning
   - Planning completes successfully with no data loss

4. **Pre-flight Questionnaire**: Specification Agent asks all questions upfront:
   - "Which OAuth providers to support?" → User: "Google, GitHub"
   - "Token storage strategy?" → User: "HttpOnly cookies"
   - "Session timeout duration?" → User: "24 hours"
   - "Permission scopes required?" → User: "profile, email"

   After answering, workflow proceeds with zero additional user prompts until completion.

5. **Verbosity Modes Work Correctly**:
   - `acpctl specify "..." --quiet` shows: "⚙️ Specifying... ✅ Complete (12s)"
   - `acpctl specify "..."` (default) shows: Phase name + 5 sub-task bullets + spinner
   - `acpctl specify "..." --verbose` shows: Full agent reasoning + LLM calls + timing + file operations

6. **Interactive Violation Remediation**: When constitutional violation occurs:
   - System displays violation report with [R]egenerate, [E]dit constitution, [A]bort, [I]gnore options
   - User selects [R]egenerate
   - Agent regenerates artifact with fix applied
   - Governance validation passes, workflow continues

7. **State Serialization Integrity**:
   - Checkpoint JSON file loads without errors
   - All ACPState fields present and correctly typed
   - State transitions are deterministic (same inputs → same state)

8. **Test Coverage >80%**: Core modules achieve test coverage:
   - state.py: Serialization, transitions, validation
   - agents/*.py: Each agent's generation and validation logic
   - workflow.py: StateGraph routing, checkpoint hooks
   - cli.py: Command parsing, flag handling

**Use Cases - i.e. User Experience & Workflow:**

**Use Case 1: First-Time Setup and Feature Development**

*Actor*: Developer new to acpctl, familiar with spec-kit

*Precondition*: Fresh repository, no .acp/ directory

*Main Success Scenario*:

1. Developer runs `acpctl init` in project root.

2. System creates directory structure:
   ```
   .acp/
   ├── templates/
   │   └── constitution.md (pre-populated template)
   └── state/
   ```

3. System displays: "✅ Initialized .acp/ directory. Edit .acp/templates/constitution.md to define project principles."

4. Developer edits constitution.md, adds principles:
   - Security #1: Sensitive data must use encrypted storage
   - Licensing #1: Only MIT/Apache2 dependencies allowed
   - Architecture #1: Follow REST API conventions

5. Developer runs `acpctl specify "Add OAuth2 authentication with Google and GitHub providers"`.

6. Specification Agent analyzes description, identifies unknowns:
   - Token storage strategy?
   - Session timeout duration?
   - Refresh token handling?
   - Permission scopes?

7. System enters pre-flight questionnaire:
   ```
   ⚙️ Specifying feature: OAuth2 authentication

   Pre-flight questionnaire (4 questions):

   1. Token storage strategy?
      Options: HttpOnly cookies, localStorage, sessionStorage, server-side sessions
      > HttpOnly cookies

   2. Session timeout duration?
      > 24 hours

   3. Refresh token handling?
      > Automatic refresh 5 minutes before expiry

   4. Permission scopes required?
      > profile, email, openid
   ```

8. User answers all questions interactively.

9. Specification Agent generates specs/001-oauth2-auth/spec.md with:
   - Feature description
   - User stories (As a user, I want to...)
   - Acceptance criteria
   - Edge cases (expired tokens, invalid providers, network failures)
   - Security considerations (based on constitution)

10. Governance Agent validates spec.md against constitution.md, finds no violations.

11. System displays: "✅ Specification complete (45s). 💾 Checkpoint saved."

12. Developer runs `acpctl plan`.

13. Architect Agent generates:
    - plan.md: Implementation phases, tech stack (Python, httpx, jwt), API design
    - data-model.md: User table schema, token table schema
    - contracts/auth-api.yaml: OAuth endpoints, request/response schemas
    - quickstart.md: Setup instructions

14. Governance Agent validates planning artifacts, finds no violations.

15. System displays: "✅ Planning complete (2m 15s). 💾 Checkpoint saved."

16. Developer runs `acpctl implement`.

17. Implementation Agent generates (TDD approach):
    - First: test_oauth_flow.py (auth flow tests), test_token_manager.py (token validation tests)
    - Then: oauth_handler.py (OAuth logic), token_manager.py (token storage), config.py (provider configs)

18. All tests pass, coverage 87%.

19. System displays: "✅ Implementation complete (5m 30s). 💾 Checkpoint saved."

20. Developer reviews generated code, runs manual tests, commits to feature branch.

*Outcome*: Complete OAuth2 feature implemented with validated artifacts in 8 minutes total agent time.

**Use Case 2: Constitutional Violation During Planning**

*Actor*: Developer working on payment processing feature

*Precondition*: Constitution includes "Security #3: Payment card data must be PCI-DSS compliant"

*Main Success Scenario*:

1. Developer completes specification phase for "Add credit card payment processing".

2. Developer runs `acpctl plan`.

3. Architect Agent generates plan.md suggesting storing credit card numbers in application database.

4. Governance Agent validates plan.md against constitution.md.

5. Governance Agent detects violation: Plan stores PCI data locally (violates Security #3).

6. System halts workflow, displays:
   ```
   ❌ Constitutional Violation Detected

   ┌─ Principle Violated ─────────────────────────────────────┐
   │ Security #3: Payment card data must be PCI-DSS compliant │
   └──────────────────────────────────────────────────────────┘

   Location: specs/002-payment/plan.md:47

   Violation:
     "Store encrypted credit card numbers in payments table"

   Why this violates the principle:
     Storing PCI data in application database requires PCI-DSS
     Level 1 compliance (expensive, complex). Constitution requires
     avoiding direct PCI data storage.

   Suggested fix:
     Use payment processor tokenization (Stripe, Square).
     Store processor tokens only, not raw card data.

   Options:
     [R]egenerate plan with fix
     [E]dit constitution to allow PCI storage
     [A]bort workflow
     [I]gnore violation (requires --force flag)

   Choose:
   ```

7. User types `R` (Regenerate).

8. Architect Agent regenerates plan.md using Stripe tokenization approach.

9. Governance Agent re-validates, finds no violations.

10. Workflow continues to implementation phase.

*Outcome*: Constitutional governance prevented security violation before code generation, suggested compliant alternative.

*Alternative Flow A: User Edits Constitution*

7a. User types `E` (Edit constitution).

7b. System opens .acp/templates/constitution.md in $EDITOR.

7c. User adds exception: "Security #3: ... EXCEPTION: Payment features may store PCI data if certified."

7d. User saves, exits editor.

7e. Governance Agent re-validates with updated constitution.

7f. Validation passes, workflow continues.

*Alternative Flow B: User Aborts*

7a. User types `A` (Abort).

7b. System displays: "Workflow aborted. Resume with: acpctl resume 002-payment"

7c. State checkpoint saved at SPECIFICATION_COMPLETE phase.

**Use Case 3: Resume After Interruption**

*Actor*: Developer experiencing network timeout during implementation

*Precondition*: Workflow started for feature "Add two-factor authentication", planning phase complete

*Main Success Scenario*:

1. Developer runs `acpctl implement` for 2FA feature.

2. Implementation Agent begins generating test_2fa_flow.py.

3. LLM API call times out after 60 seconds (network issue).

4. System displays error: "⚠️ Implementation failed: LLM timeout. Checkpoint saved at PLANNING_COMPLETE."

5. Developer checks network, resolves issue.

6. Developer runs `acpctl status`.

7. System displays:
   ```
   📊 Workflow Status

   Active Workflows:

   003-two-factor-auth
     Feature: Add two-factor authentication
     Last phase: PLANNING_COMPLETE ✅
     Current phase: IMPLEMENTATION (incomplete)
     Started: 2025-11-05 14:23:15
     Last checkpoint: .acp/state/003-two-factor-auth.json

   Resume with: acpctl resume 003-two-factor-auth
   ```

8. Developer runs `acpctl resume 003-two-factor-auth` (or just `acpctl resume` if only one workflow).

9. System loads checkpoint from .acp/state/003-two-factor-auth.json.

10. System displays:
    ```
    🔄 Resuming workflow: 003-two-factor-auth

    Skipping completed phases:
      ✅ Specification
      ✅ Planning

    Continuing from: Implementation
    ```

11. Implementation Agent re-starts code generation with full context from checkpoint.

12. test_2fa_flow.py, test_totp_validator.py generated.

13. totp_validator.py, qr_code_generator.py generated.

14. All tests pass, implementation complete.

15. System displays: "✅ Implementation complete (3m 45s). 💾 Checkpoint saved."

*Outcome*: Workflow resumed seamlessly after interruption with no manual intervention or context loss.

**Use Case 4: Verbosity Mode Comparison**

*Actor*: Developer learning acpctl behavior

*Scenario*: Running specification phase with different verbosity levels

*Quiet Mode (`--quiet`):*
```
$ acpctl specify "Add user profile editing" --quiet
✅ Specification complete (32s)
```

*Default Mode (no flag):*
```
$ acpctl specify "Add user profile editing"
⚙️ Specifying: Add user profile editing

Pre-flight questionnaire:
  • Collecting clarifications...
  • Question 1/3: Which profile fields are editable?
  • Question 2/3: Validation requirements?
  • Question 3/3: Permission requirements?

📝 Generating specification...
  • Analyzing requirements
  • Writing user stories
  • Defining acceptance criteria
  • Identifying edge cases

🔍 Validating against constitution...
  • Checking security principles
  • Checking licensing constraints
  • Checking architecture guidelines

✅ Specification complete (32s)
💾 Checkpoint saved: .acp/state/004-profile-edit.json
```

*Verbose Mode (`--verbose`):*
```
$ acpctl specify "Add user profile editing" --verbose
⚙️ Specifying: Add user profile editing

[14:30:15] Specification Agent initialized
[14:30:15] Analyzing feature description...
[14:30:16] LLM call: analyze_requirements (model: gpt-4, tokens: 234)
[14:30:18] Identified ambiguities: 3

Pre-flight questionnaire:
[14:30:18] Generating clarification questions...
[14:30:19] Question 1: Which profile fields are editable? (username, email, bio, avatar)
[14:30:25] User response: "username, email, bio, avatar, phone"
[14:30:25] Question 2: Validation requirements? (email format, username length, etc.)
[14:30:32] User response: "email must be valid, username 3-20 chars alphanumeric"
[14:30:32] Question 3: Permission requirements? (own profile only, admin can edit any)
[14:30:38] User response: "own profile only, admins can edit any"

📝 Generating specification...
[14:30:38] LLM call: generate_spec (model: gpt-4, tokens: 1,245)
[14:30:45] Writing specs/004-profile-edit/spec.md (234 lines)
[14:30:45] Spec sections: Overview, User Stories (5), Acceptance Criteria (12), Edge Cases (8)

🔍 Validating against constitution...
[14:30:45] Governance Agent initialized
[14:30:45] Loading constitution: .acp/templates/constitution.md (15 principles)
[14:30:46] LLM call: validate_artifact (model: gpt-3.5-turbo, tokens: 2,103)
[14:30:48] Validation complete: 0 violations

✅ Specification complete (33s)
[14:30:48] Saving checkpoint: .acp/state/004-profile-edit.json
💾 Checkpoint saved: .acp/state/004-profile-edit.json
```

*Outcome*: Different verbosity levels meet different user needs (glanceable vs. debuggable).

**Documentation Considerations:**

**Phase 1 Required Documentation:**

* **README.md** (Phase 1 MVP):
  - Project overview and Phase 1 scope
  - Installation: `pip install acpctl` or `pip install -e .`
  - Quick start: init → specify → plan → implement example
  - Links to detailed documentation

* **Installation Guide**:
  - Prerequisites: Python 3.9+, LLM API key (OpenAI/Anthropic)
  - Virtual environment setup: `python -m venv .venv && source .venv/bin/activate`
  - Dependency installation: `pip install -e ".[dev]"` for development
  - Environment variables: `ACP_LLM_PROVIDER`, `ACP_API_KEY`, `ACP_MODEL`

* **Getting Started Tutorial**:
  - Step 1: `acpctl init` - Create constitution template
  - Step 2: Edit constitution.md with project principles (include examples)
  - Step 3: `acpctl specify "..."` - Generate first specification with pre-flight Q&A walkthrough
  - Step 4: `acpctl plan` - Generate architecture artifacts
  - Step 5: `acpctl implement` - Generate code
  - Step 6: Review generated artifacts, test, commit

* **Command Reference**:
  - `acpctl init`: Create .acp/ structure, constitution template
  - `acpctl specify "<description>"`: Generate specification
    - Flags: `--quiet`, `--verbose`, `--model <name>`
    - Example: `acpctl specify "Add OAuth2 authentication with Google"`
  - `acpctl plan`: Generate architecture from specification
    - Flags: `--quiet`, `--verbose`
    - Requires: Completed specification phase
  - `acpctl implement`: Generate code from plan
    - Flags: `--quiet`, `--verbose`, `--tdd` (default true)
    - Requires: Completed planning phase
  - `acpctl status`: Display workflow state
  - `acpctl resume [spec-id]`: Resume from checkpoint

* **Constitutional Governance Guide**:
  - What is a constitution.md? (Project governing principles)
  - Principle categories: Security, Licensing, Architecture
  - Example principles with explanations:
    - Security: "Passwords must be hashed with bcrypt (cost factor ≥12)"
    - Licensing: "Only MIT, Apache2, BSD-3 dependencies allowed"
    - Architecture: "All API endpoints must follow REST conventions"
  - How governance validation works (pattern matching, LLM analysis)
  - Writing effective principles (specific, actionable, enforceable)
  - Handling violations: Regenerate, Edit, Abort, Ignore

* **State Schema Documentation**:
  - ACPState TypedDict structure diagram
  - Field descriptions: constitution, governance_passes, feature_description, spec, plan, etc.
  - Checkpoint file format: JSON example with annotations
  - State transitions: INIT → SPECIFYING → SPECIFICATION_COMPLETE → PLANNING → ... → COMPLETE
  - Manual state inspection: `python -m json.tool .acp/state/NNN-feature.json`

* **Troubleshooting Guide**:
  - LLM API errors: Timeout, rate limit, invalid key
  - Checkpoint corruption: Backup, manual edit, resume from earlier phase
  - Constitutional violations: Understanding reports, common fixes
  - Pre-flight questionnaire: How to skip (not recommended), editing answers
  - Verbose debugging: `--verbose` flag, log file location

**Phase 2+ Deferred Documentation:**

* Agent customization guide (custom agents, plugin architecture)
* Enterprise integration guide (Confluence, Jira, approval workflows)
* Performance optimization guide (parallel execution, caching)
* Migration from spec-kit guide (directory structure conversion, constitution porting)

**Questions to answer:**

**Phase 1 Critical Questions (Must answer before implementation):**

1. **LLM Provider**: OpenAI only, or support Anthropic/open-source in Phase 1?
   - Recommendation: Start with OpenAI (simpler), add others Phase 2
   - Configuration: Environment variable `ACP_LLM_PROVIDER=openai`, `ACP_API_KEY=sk-...`

2. **Constitution Template Content**: What specific principles in default template?
   - Recommendation: Generic template with examples, users customize
   - Template sections: Security (3 examples), Licensing (2 examples), Architecture (3 examples)

3. **Pre-flight Question Limit**: Maximum clarifying questions before proceeding?
   - Recommendation: Cap at 10 questions, prioritize highest-impact ambiguities
   - If >10, agent must consolidate or proceed with best effort

4. **Governance Validation Granularity**: Validate entire artifact or diff from previous version?
   - Recommendation Phase 1: Validate entire artifact (simpler)
   - Phase 2+: Optimize with incremental validation

5. **Checkpoint Conflict Handling**: What if two developers run workflows concurrently?
   - Recommendation Phase 1: Sequential IDs with file locking
   - Phase 2+: Add workflow ID to checkpoint filename, support multi-user

6. **Test Framework Selection**: pytest only, or support unittest/nose?
   - Recommendation: pytest only Phase 1 (most popular)
   - Implementation Agent generates pytest-compatible tests

7. **Error Recovery on Agent Failure**: Save partial progress or only completed phases?
   - Recommendation: Only completed phases saved to checkpoints
   - Partial progress discarded, agent retries entire phase on resume

8. **Artifact Naming**: How to generate spec IDs (001, 002...)?
   - Recommendation: Auto-increment counter in .acp/state/counter.txt
   - Format: `{counter:03d}-{slug-from-description}`

**Phase 1 Nice-to-Answer Questions (Can decide during implementation):**

9. **Verbose Mode Detail Level**: How much agent reasoning to stream?
   - Recommendation: LLM calls with model/tokens, file operations, timing
   - Balance: Useful for debugging, not overwhelming

10. **Violation Report Format**: Plain text or structured (JSON)?
    - Recommendation: Rich-formatted terminal output Phase 1
    - Phase 2+: Add `--json` flag for programmatic parsing

**Background & Strategic Fit:**

**Phase 1 Strategic Positioning:**

acpctl Phase 1 is a proof-of-concept that validates the core hypothesis: **Constitutional governance + LangGraph orchestration + checkpoint/resume = trusted enterprise development workflow**. This phase intentionally limits scope to sequential execution and four core agents to prove the architecture works before investing in advanced features.

**Why Phase 1 Matters:**

* **Derisks LangGraph Investment**: Validates that LangGraph's StateGraph, checkpointing, and conditional routing work for complex agent workflows before committing to Phase 2 parallelization.

* **Tests Constitutional Governance Value**: Real developers will reveal if automated principle enforcement catches meaningful violations or produces false positives—critical data for Phase 2 tuning.

* **Establishes Baseline Metrics**: Phase 1 generates performance data (workflow completion time, agent success rate, violation frequency) that informs Phase 2 optimization priorities.

* **Validates User Experience**: Pre-flight questionnaire, verbosity modes, violation remediation UX get real-world testing—adjustments cheaper now than after Phase 2 complexity increases.

**spec-kit Migration Path:**

Existing spec-kit users recognize familiar command structure (init, specify, plan, implement), easing adoption. Key enhancements over spec-kit:

* **Constitutional gates**: Prevents violations that spec-kit catches only in manual review
* **Checkpoint/resume**: Handles interruptions that force spec-kit users to restart
* **Pre-flight Q&A**: Eliminates mid-workflow interruptions that break spec-kit flow
* **Agent intelligence**: LangGraph routing improves on spec-kit's rigid linear flow

**Red Hat AI Engineering Alignment:**

Phase 1 deliverables directly support Red Hat's Q1 2026 objectives:

* **Governance-First Development**: Constitutional enforcement aligns with Red Hat security/licensing standards
* **Audit Trail Foundation**: Checkpoint state files provide compliance validation artifacts
* **Workflow Automation**: Reduces manual spec-to-code translation effort (current bottleneck)
* **Enterprise Resilience**: Resume capability critical for features with approval gates

**Phase 2+ Roadmap Context:**

Phase 1 intentionally defers features that require architectural complexity:

* **Parallel execution**: Requires concurrent agent orchestration, resource pooling
* **Task decomposition**: Requires dependency graph analysis, batch optimization
* **Validation loops**: Requires rework detection, convergence criteria

These features add significant value but would triple Phase 1 implementation time. Sequential workflow proves the concept faster.

**Technology Foundation Validation:**

Phase 1 validates technology choices before lock-in:

* **LangGraph**: Confirms StateGraph + checkpointing handle enterprise workflow complexity
* **Click/Typer**: Validates CLI framework meets UX requirements
* **Rich**: Confirms terminal formatting achieves professional polish
* **Pydantic**: Validates state schema type safety

If any component fails Phase 1 requirements, pivot before Phase 2 investment.

**Customer Considerations**

**Phase 1 Target Users:**

* **Early Adopters**: Red Hat AI Engineering team members willing to test alpha software
* **Feedback Providers**: Developers comfortable filing detailed bug reports, UX feedback
* **spec-kit Users**: Teams already using GitHub's spec-kit, seeking governance + resume features

**Phase 1 NOT Intended For:**

* Production critical paths (alpha stability)
* Large teams (no multi-user coordination yet)
* Complex codebases (no performance optimization yet)

**Phase 1 Onboarding Requirements:**

* **Setup Time**: 15 minutes (install, configure LLM API, create constitution)
* **Learning Curve**: 30 minutes (read getting started, run first workflow)
* **Prerequisites**: Familiarity with spec-kit concepts, Python CLI tools, git workflows

**Support Model for Phase 1:**

* **Channel**: GitHub Issues for bug reports, Slack #acpctl-alpha for questions
* **Response Time**: 2-3 business days for P1 bugs, 1 week for feature requests
* **Known Limitations**: Document Phase 1 scope boundaries prominently in README
* **Escalation Path**: Critical failures escalate to LangGraph/LangChain support if library issues

**Phase 1 Success Metrics:**

* **Functional**: 10+ real features implemented by Red Hat engineers using acpctl
* **Quality**: <5 critical bugs per month (checkpoint corruption, data loss)
* **Adoption**: 3+ teams using acpctl for alpha testing
* **Feedback**: 80%+ satisfaction with constitutional governance value
* **Performance**: Average workflow completion <10 minutes for simple features

**Data Collection for Phase 2 Planning:**

* **Timing**: Average duration per phase (specification, planning, implementation)
* **Violations**: Frequency/type of constitutional violations (security > licensing?)
* **Interruptions**: How often workflows interrupted, which phases most fragile
* **Verbosity Usage**: Which mode most popular (default vs. verbose)
* **Feature Requests**: What advanced features most requested (parallel execution, validation loops, integrations)

**Migration from Phase 1 to Phase 2:**

* **State Schema**: Design ACPState to support Phase 2 additions (research, task dependencies) without breaking Phase 1 checkpoints
* **Constitution Format**: Keep constitution.md schema stable across phases
* **CLI Compatibility**: Phase 2 must support all Phase 1 commands without breaking changes
* **Deprecation Policy**: 6-month notice for any Phase 1 API/CLI changes
