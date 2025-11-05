# acpctl Constitution

## Core Principles

### I. Specifications as First-Class Artifacts

**What before How**: Specifications describe user needs and business value, never implementation details. No programming languages, frameworks, databases, or APIs in spec.md files. Code serves specifications, not vice versa.

**Traceability**: Every code artifact must trace back to a specification requirement. Every specification requirement must have acceptance scenarios.

**Governance Gates**: All artifacts (specs, plans, code) validated against constitutional principles at phase boundaries. Violations block progress unless explicitly justified.

### II. Constitutional Governance (NON-NEGOTIABLE)

**Validation Required**: Every workflow phase must pass constitutional validation before proceeding. Violations must be reported with file locations, line numbers, violated principles, and actionable corrections.

**Actionable Errors**: Constitutional violation reports must include specific fixes. Never report problems without solutions.

**Interactive Remediation**: Developers choose: [R]egenerate with fixes, [E]dit constitution, [A]bort workflow, or [I]gnore with --force flag. No silent failures.

### III. Checkpoint Everything

**Automatic State Persistence**: Save complete workflow state after EVERY phase completion (specification, planning, implementation). State includes all decisions, artifacts, and progress.

**Resume Capability**: Any workflow must be resumable from last checkpoint. System skips completed phases, continues from breakpoint. No manual state reconstruction required.

**Serializable State**: All workflow state must be JSON-serializable for cross-platform compatibility and version control.

### IV. Pre-flight Over Interruption

**Collect Questions Upfront**: Specification Agent asks ALL clarifying questions before workflow execution begins. No mid-workflow interruptions for clarifications.

**Preserve Answers**: When regenerating artifacts after violations, preserve all previously answered questions. Never ask same question twice.

**Single Interactive Session**: Complete pre-flight questionnaire in one session (<10 minutes). After questions answered, workflow runs uninterrupted to completion.

### V. Progressive Disclosure

**Three Verbosity Modes**:
- `--quiet`: Final results only (file paths, success/failure)
- Default: Phases and sub-tasks with progress indicators
- `--verbose`: Full agent reasoning, thinking steps, timing data

**Rich Terminal UI**: Use boxes, spinners, progress bars for professional appearance. Clear visual hierarchy. Color-coded status (green=success, red=error, yellow=warning).

### VI. Library-First Architecture

**Core as Library**: All business logic in reusable library modules. CLI is thin wrapper calling library functions.

**Independently Testable**: Libraries must be testable without CLI layer. Unit tests don't invoke CLI commands.

**Clear Boundaries**: Separate concerns: agents/, state/, storage/, cli/, core/. No circular dependencies.

### VII. Test-First (NON-NEGOTIABLE)

**TDD Cycle**: Tests written → User approved → Tests fail → Then implement → Tests pass. No implementation before tests.

**Coverage Requirements**: 80% minimum code coverage for core library. 100% coverage for state management and checkpoint logic.

**Integration Tests**: Required for: Phase boundaries, Checkpoint/resume flows, Constitutional validation gates, Multi-phase workflows.

## Enterprise Requirements

### Security & Compliance

**No Secrets in Code**: Never commit API keys, credentials, or tokens. Use environment variables or secure vaults.

**Audit Trails**: Complete state history for compliance. All decisions, artifacts, timestamps preserved.

**Open Source Licensing**: Apache 2.0 or compatible licenses only. No GPL or proprietary dependencies without explicit approval.

### Performance Standards

**Responsiveness**: Initialization <10s, Status checks <2s, Pre-flight Q&A <10min, Full workflow <30min for standard features.

**Graceful Degradation**: Long operations show progress. Timeout handling with clear error messages. Network failures don't corrupt state.

**Resource Constraints**: Respect token limits. Chunk large artifacts. Stream output for long generations.

## Development Workflow

### Code Review Gates

**Constitutional Compliance**: Every PR verified against all principles. Violations must be justified in PR description.

**Test Evidence**: PRs include test results demonstrating TDD. Show tests failing before implementation.

**Documentation Updates**: Changes to public APIs require docstring and quickstart.md updates.

### Quality Standards

**Type Safety**: Pydantic models for all state structures. mypy strict mode for type checking.

**Error Handling**: Descriptive error messages with actionable next steps. Never bare exceptions.

**Logging**: Structured logging for debugging. Debug logs show agent reasoning. Info logs show phase progress.

## Governance

This constitution supersedes all other practices. Amendments require:
1. Documentation of rationale (why change needed)
2. Team review and approval
3. Migration plan for existing code
4. Version bump and ratification date update

All PRs and reviews must verify constitutional compliance. Complexity must be justified using Complexity Tracking table in plan.md.

Use CLAUDE.md for development guidance and architectural context.

**Version**: 1.0.0 | **Ratified**: 2025-11-05 | **Last Amended**: 2025-11-05
