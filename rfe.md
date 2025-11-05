# acpctl: Ambient Code Platform CLI - Governed Spec-Driven Development System

**Feature Overview:**

acpctl is a LangGraph-based intelligent agent system that transforms GitHub's spec-kit workflow into a governed, multi-agent architecture for enterprise software development. It enables Red Hat AI Engineering teams to deliver high-quality features through constitutional governance, automatic checkpointing, and spec-first development, ensuring every artifact—from specifications to implementation—adheres to organizational principles while providing complete audit trails for compliance and debugging.

**Goals:**

* **Governed Development at Scale**: Enable Red Hat engineering teams to develop features with built-in enforcement of security, licensing, and architectural principles through constitutional governance gates at every workflow phase.

* **Resume-from-Failure Workflows**: Provide checkpoint/resume capability for long-running enterprise development workflows, allowing interruption and resumption without loss of context or progress.

* **Specification-First Architecture**: Transform natural language feature descriptions into complete, validated implementation plans through intelligent multi-agent orchestration, ensuring code serves specifications rather than vice versa.

* **Enterprise Audit Trails**: Create complete state history for all development workflows, enabling compliance validation, debugging, and process improvement analysis.

* **Developer Experience Excellence**: Deliver a professional CLI interface with progressive disclosure (quiet/moderate/verbose modes) that matches spec-kit familiarity while adding intelligent agent capabilities.

**Out of Scope:**

* Phase 1 excludes parallel execution capabilities (deferred to Phase 2+)
* Advanced enterprise integrations with Red Hat internal systems (Confluence, Jira, approval workflows)
* Multi-model coordination and cost optimization
* Performance optimization for large-scale codebases
* Task decomposition with complex dependency graphs
* Validation agents with automatic rework loops

**Requirements:**

**MVP Requirements:**

* **CLI Framework** (MVP): Implement all core commands (init, specify, plan, implement, status, resume, history) with Click/Typer, supporting --quiet/-q and --verbose/-v flags across all commands.

* **State Management** (MVP): Define ACPState TypedDict schema covering constitution, specification, planning, task, and implementation layers with JSON-based checkpoint persistence and deterministic state transitions.

* **Constitutional Governance** (MVP): Implement Governance Agent that validates all artifacts against constitution.md principles, reports violations with specific line numbers and actionable fixes, and provides interactive remediation options (Regenerate/Edit/Abort/Ignore).

* **Sequential Workflow Orchestration** (MVP): Build LangGraph StateGraph connecting Governance → Specification → Architect → Implementation agents with conditional routing based on governance validation results.

* **Pre-flight Questionnaire** (MVP): Implement Specification Agent that identifies all ambiguities upfront, collects clarifying questions before workflow execution, and generates spec.md without mid-workflow interruptions.

* **Automatic Checkpointing** (MVP): Save workflow state to .acp/state/ after SPECIFICATION_COMPLETE, PLANNING_COMPLETE, and IMPLEMENTATION_COMPLETE phases.

* **Resume Capability** (MVP): Load checkpoint state from JSON, skip completed phases, and continue execution from last successful checkpoint.

**Post-MVP Requirements:**

* **Technical Planning**: Architect Agent generates plan.md (implementation approach), data-model.md (schemas), contracts/ (API definitions), and quickstart.md.

* **TDD Implementation**: Implementation Agent generates code following test-driven development approach with tests written before implementation.

* **Artifact Structure**: Generate artifacts matching spec-kit directory structure (specs/NNN-feature/ containing spec.md, plan.md, data-model.md, contracts/).

* **Progress Visualization**: Rich terminal formatting with phase transition indicators, sub-task progress for moderate verbosity, spinners for long operations, and box-drawing section headers.

* **Comprehensive History**: List all workflow runs with status, timestamps, and checkpoint availability via acpctl history command.

**Done - Acceptance Criteria:**

* **End-to-End Workflow**: User can run acpctl init → specify "Add OAuth2 authentication" → plan → implement and produce working code with complete documentation.

* **Constitutional Enforcement**: Constitutional violations halt workflow with clear reports showing which principle was violated, where (file:line), why, and suggested fixes.

* **Checkpoint Resilience**: Workflow interrupted at any point can be resumed via acpctl resume, skipping completed phases and continuing from last checkpoint without loss of context.

* **Verbosity Modes**: --quiet shows only final results, default shows phases + sub-tasks, --verbose streams full agent reasoning with timing information.

* **Pre-flight Q&A**: Specification Agent asks all clarifying questions before workflow begins, user answers interactively, workflow proceeds without further interruptions.

* **Artifact Validation**: Generated artifacts (spec.md, plan.md, data-model.md, contracts/) match spec-kit structure and pass governance validation.

* **Audit Trail**: Complete workflow history inspectable via acpctl status and JSON checkpoint files showing all state transitions, agent decisions, and validation results.

* **Test Coverage**: Core functionality (state management, agents, workflow orchestration, CLI) achieves >80% test coverage with pytest.

**Use Cases - i.e. User Experience & Workflow:**

**Use Case 1: New Feature Development**

*Main Success Scenario:*

1. Developer runs `acpctl init` to create .acp/templates/constitution.md with project principles (security, licensing, architecture standards).

2. Developer runs `acpctl specify "Add OAuth2 authentication with Google and GitHub providers"`.

3. Specification Agent identifies ambiguities: token storage strategy, session management approach, permission scopes.

4. User answers pre-flight questions interactively.

5. Specification Agent generates specs/001-oauth2-auth/spec.md validated against constitution.

6. Checkpoint saved automatically.

7. Developer runs `acpctl plan`.

8. Architect Agent generates plan.md (implementation phases), data-model.md (user table schema), contracts/auth-api.yaml (OAuth endpoints).

9. Governance Agent validates plan against constitutional principles, reports no violations.

10. Checkpoint saved.

11. Developer runs `acpctl implement`.

12. Implementation Agent generates tests first (test_oauth_flow.py), then implementation (oauth_handler.py, token_manager.py).

13. All tests pass, checkpoint saved.

14. Developer reviews generated code, commits to feature branch.

*Alternative Flow: Constitutional Violation*

6a. Governance Agent detects violation: spec.md specifies storing tokens in localStorage (violates security principle).

6b. System displays: "VIOLATION: Security Principle #3 - Sensitive data must not be stored in browser localStorage. Suggested fix: Use HttpOnly cookies or server-side sessions."

6c. User selects [R]egenerate.

6d. Specification Agent regenerates spec.md with HttpOnly cookie approach.

6e. Governance validation passes, workflow continues.

**Use Case 2: Resume Interrupted Workflow**

*Main Success Scenario:*

1. Developer starts `acpctl specify "Add two-factor authentication"`, completes pre-flight Q&A.

2. Specification phase completes, checkpoint saved to .acp/state/002-2fa.json.

3. Developer starts `acpctl plan`, planning phase begins.

4. Process interrupted (laptop closes, network failure, etc.).

5. Developer runs `acpctl status`, sees: "Workflow 002-2fa: PLANNING phase incomplete. Last checkpoint: SPECIFICATION_COMPLETE."

6. Developer runs `acpctl resume`.

7. System loads state from .acp/state/002-2fa.json, skips specification phase, resumes planning from beginning.

8. Planning completes successfully, implementation proceeds.

**Use Case 3: Enterprise Governance Enforcement**

*Main Success Scenario:*

1. Red Hat team lead creates .acp/templates/constitution.md with mandatory principles: RHEL compatibility, approved dependency list, security scanning requirements.

2. Developer runs workflow to add new Python package dependency.

3. Architect Agent generates plan.md specifying FastAPI framework.

4. Governance Agent validates: FastAPI not in approved dependency list (constitution principle #5).

5. System reports violation with options: [R]egenerate with approved framework, [E]dit constitution to add FastAPI, [A]bort.

6. Team lead reviews, decides to update constitution after security review.

7. Developer uses [A]bort, awaits approval process.

8. After approval, constitution.md updated, workflow resumed successfully.

**Documentation Considerations:**

* **Installation Guide**: pyproject.toml setup, dependency installation (LangGraph, LangChain, Click/Typer, Rich, Pydantic), Python 3.9+ requirement.

* **Getting Started Tutorial**: Step-by-step walkthrough of init → specify → plan → implement for sample feature (e.g., OAuth2 authentication).

* **Constitutional Governance Guide**: How to write effective constitution.md, example principles (security, licensing, architecture), governance agent validation logic.

* **Command Reference**: Detailed documentation for all CLI commands (init, specify, plan, implement, status, resume, history) with examples and flag descriptions.

* **State Schema Documentation**: ACPState TypedDict structure, checkpoint file format, state transition diagram.

* **Agent Architecture**: Design documentation for Governance, Specification, Architect, and Implementation agents with inputs/outputs/capabilities.

* **Workflow Orchestration**: LangGraph StateGraph structure, conditional edges, checkpoint hooks, resume logic.

* **Migration from spec-kit**: Command mapping (spec-kit → acpctl), workflow differences, constitutional governance additions.

* **Troubleshooting Guide**: Common errors (checkpoint corruption, governance violations, agent failures), debugging with --verbose, state inspection techniques.

* **Extension Documentation**: How to customize agents, add new governance principles, integrate with enterprise tools (Phase 2+).

**Questions to answer:**

* **LLM Provider Integration**: Which LLM provider(s) will be supported in Phase 1 (OpenAI, Anthropic, open-source models)? How will API keys be configured?

* **Constitution Template Structure**: What is the exact schema for constitution.md? How are principles categorized (security, licensing, architecture)?

* **Specification Agent Q&A UX**: How many clarifying questions maximum before workflow proceeds? How does interactive input work in CI/CD environments?

* **Governance Validation Granularity**: Does Governance Agent validate entire artifacts or incremental changes? How are line-number references maintained across edits?

* **Checkpoint Storage Strategy**: Are checkpoints versioned? How are conflicts handled if multiple workflows run concurrently? What is retention policy?

* **Implementation Agent TDD Approach**: How does Implementation Agent decide test structure? How are edge cases identified? What testing frameworks are supported?

* **Error Recovery Strategy**: If an agent fails mid-execution (LLM timeout, network error), does checkpoint include partial results or only completed phases?

* **State Migration**: How will state schema evolve between versions? Is there a migration path for existing checkpoint files?

* **Artifact Naming Convention**: How are spec IDs generated (NNN-feature)? Is auto-increment persistent across project lifetime?

* **Multi-user Coordination**: Can multiple developers work on separate workflows in same repository? How are .acp/ directory conflicts prevented?

**Background & Strategic Fit:**

acpctl aligns directly with Red Hat AI Engineering's strategic mission to deliver governed, auditable, enterprise-ready development workflows. The project addresses critical gaps in current AI-assisted development tools:

**Industry Context**: GitHub's spec-kit demonstrates the value of specification-first development, but its linear CLI workflow lacks enterprise governance, state persistence, and intelligent orchestration. Existing AI coding assistants (Copilot, Cursor) focus on code generation without specification validation or constitutional enforcement.

**Red Hat Strategic Value**:

* **Compliance & Audit**: Complete state history enables regulatory compliance validation, security reviews, and process audits—critical for enterprise software development.

* **Governance Enforcement**: Constitutional principles codify Red Hat's security, licensing, and architectural standards, preventing violations before code reaches review.

* **Long-Running Workflow Support**: Checkpoint/resume capability essential for enterprise features with multi-day development cycles, cross-team dependencies, and approval gates.

* **Future Integration Platform**: Phase 2+ integrations with Red Hat internal systems (Confluence docs, Jira issues, approval workflows, CI/CD pipelines) position acpctl as central development orchestration platform.

**Differentiation from spec-kit**:

* **LangGraph Architecture**: Dynamic routing, parallel execution potential, state checkpointing, human-in-the-loop gates.

* **Constitutional Governance**: Automated validation against organizational principles at every phase boundary.

* **Multi-Agent Intelligence**: Specialized agents (Governance, Specification, Architect, Implementation) with distinct capabilities and validation logic.

* **Enterprise Resilience**: Resume-from-failure, complete audit trails, progressive disclosure UX.

**Technology Foundation**: LangGraph provides production-ready agent orchestration with proven state management, checkpointing, and conditional execution—eliminating need for custom workflow engine development.

**Customer Considerations**

* **Red Hat Engineering Teams**: Primary users require seamless integration with existing workflows (git, CI/CD, code review). Constitutional principles must be customizable per team/project without requiring agent modifications.

* **Enterprise Security Requirements**: All LLM API calls must support enterprise authentication, data residency requirements, and audit logging. No proprietary code or sensitive data should leave Red Hat infrastructure without explicit approval.

* **Onboarding & Training**: Internal developer documentation must be comprehensive—assume users familiar with spec-kit but new to LangGraph concepts. Include runbooks for common scenarios (resolving constitutional violations, debugging checkpoint issues).

* **Performance Expectations**: Initial Phase 1 focus on correctness over speed—sequential workflow acceptable if governance validation is reliable. Phase 2+ will address performance optimization with parallel execution.

* **Support & Maintenance**: Clear escalation path for agent failures, LLM API issues, checkpoint corruption. Monitoring dashboard for workflow success rates, average completion times, common violation patterns.

* **Migration Strategy**: Existing spec-kit users need migration guide—how to convert .specify/ directory to .acp/, port constitution principles, convert existing specs to new format. Consider providing migration utility.

* **Cost Management**: LLM API costs must be predictable—provide estimates per workflow phase, recommendations for model selection (cheaper models for validation, expensive models for generation), cost tracking per project.

* **Customization Requirements**: Teams may need custom validation logic beyond constitutional principles—design plugin architecture for custom governance rules, specialized agents, enterprise tool integrations.
