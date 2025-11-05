"""
acpctl Architect Agent

AI agent for generating technical implementation plans from specifications.
Implements multi-phase planning workflow: Research → Design → Data Model → Contracts.

Planning Philosophy:
- Plans describe HOW to build (technical approach), not exact code
- Technology-agnostic where possible (no "use PostgreSQL", but "persistent storage")
- Multiple phases: Research (Phase 0) identifies unknowns, Design (Phase 1) creates plan
- All planning artifacts validated against constitutional principles

Architecture:
- Extends BaseAgent with LangChain LLM integration
- Multi-phase operation: research → design → data model → contracts → quickstart
- Reads spec.md from state
- Generates multiple planning artifacts (plan.md, data-model.md, contracts/, quickstart.md)

Reference: spec.md (User Story 4), plan.md (Phase 1 Design)
"""

from typing import Any, Dict, List, Optional

from acpctl.agents.base import BaseAgent
from acpctl.core.state import ACPState


# ============================================================
# ARCHITECT AGENT
# ============================================================


class ArchitectAgent(BaseAgent):
    """
    Agent for generating implementation plans and technical design.

    Multi-phase workflow:
    1. Phase 0 (Research): Analyze spec, identify technical challenges, research options
    2. Phase 1 (Design): Generate plan.md with implementation approach
    3. Data Model: Generate data-model.md if feature requires data storage
    4. Contracts: Generate API contract files if feature exposes interfaces
    5. Quickstart: Generate quickstart.md with usage examples

    Example:
        >>> agent = ArchitectAgent()
        >>> state = {
        ...     'spec': '# Feature Specification...',
        ...     'constitution': '...',
        ... }
        >>> updated_state = agent(state)
        >>> print(updated_state['plan'])
    """

    def __init__(
        self,
        llm: Any = None,
        mock_mode: bool = False,
    ):
        """
        Initialize Architect Agent.

        Args:
            llm: LangChain LLM instance (e.g., ChatOpenAI). If None, uses mock mode.
            mock_mode: If True, use mock responses instead of LLM
        """
        super().__init__(
            agent_name="Architect Agent",
            agent_type="architect",
        )

        self.llm = llm
        self.mock_mode = mock_mode or llm is None

    def execute(self, state: ACPState) -> ACPState:
        """
        Execute full planning workflow (all phases).

        This is the main entry point for comprehensive planning.
        For phase-specific execution, use run_research() or run_design().

        Args:
            state: Current workflow state

        Returns:
            Updated state with all planning artifacts

        Raises:
            ValueError: If required fields missing
        """
        # Validate required inputs
        self.validate_state_requirements(
            state,
            ["spec", "constitution"],
        )

        self.log("Starting planning workflow", level="info")

        # Phase 0: Research
        state = self.run_research(state)

        # Phase 1: Design
        state = self.run_design(state)

        return state

    def run_research(self, state: ACPState) -> ACPState:
        """
        Execute Phase 0: Research technical approach.

        Analyzes specification to identify:
        - Technical challenges and unknowns
        - Technology options and trade-offs
        - Recommended approach with rationale
        - Risk assessment

        Args:
            state: Current workflow state

        Returns:
            Updated state with research field populated
        """
        self.log("Phase 0: Research - Analyzing technical challenges", level="info")

        # Validate we have spec
        if not state.get("spec"):
            raise ValueError("Research phase requires spec")

        spec = state["spec"]
        constitution = state.get("constitution", "")

        # Generate research document
        research = self._generate_research(spec, constitution)

        return self.update_state(
            state,
            {
                "research": research,
                "unknowns": [],  # Research resolves unknowns
            },
        )

    def run_design(self, state: ACPState) -> ACPState:
        """
        Execute Phase 1: Design implementation plan.

        Generates multiple artifacts:
        - plan.md: Technical implementation approach
        - data-model.md: Entity definitions (if feature requires data storage)
        - contracts/*.yaml: API contracts (if feature exposes interfaces)
        - quickstart.md: Usage examples and getting started guide

        Args:
            state: Current workflow state

        Returns:
            Updated state with plan, data_model, contracts, and quickstart populated
        """
        self.log("Phase 1: Design - Creating implementation plan", level="info")

        # Validate prerequisites
        if not state.get("spec"):
            raise ValueError("Design phase requires spec")

        spec = state["spec"]
        research = state.get("research", "")
        constitution = state.get("constitution", "")

        # Generate plan.md
        self.log("Generating plan.md", level="info")
        plan = self._generate_plan(spec, research, constitution)

        # Generate data-model.md (if needed)
        self.log("Analyzing need for data model", level="info")
        data_model = self._generate_data_model(spec, plan, constitution)

        # Generate API contracts (if needed)
        self.log("Analyzing need for API contracts", level="info")
        contracts = self._generate_contracts(spec, plan, constitution)

        # Generate quickstart.md
        self.log("Generating quickstart.md", level="info")
        quickstart = self._generate_quickstart(spec, plan)

        # Store quickstart in code_artifacts
        code_artifacts = state.get("code_artifacts", {}).copy()
        if quickstart:
            code_artifacts["quickstart.md"] = quickstart

        return self.update_state(
            state,
            {
                "plan": plan,
                "data_model": data_model,
                "contracts": contracts,
                "code_artifacts": code_artifacts,
                "phase": "plan",  # Mark as in planning phase
            },
        )

    # ========================================================
    # PHASE 0: RESEARCH GENERATION (T051)
    # ========================================================

    def _generate_research(self, spec: str, constitution: str) -> str:
        """
        Generate research.md analyzing technical challenges.

        Args:
            spec: Feature specification
            constitution: Constitutional principles

        Returns:
            Research document as markdown
        """
        if self.mock_mode:
            return self._generate_mock_research(spec)

        # Use LLM for research
        prompt = self._build_research_prompt(spec, constitution)

        try:
            response = self.llm.invoke(prompt)
            research = response.content

            self.log(f"Generated research ({len(research)} characters)", level="info")
            return research

        except Exception as e:
            self.log(f"LLM call failed: {e}", level="error")
            return self._generate_mock_research(spec)

    def _build_research_prompt(self, spec: str, constitution: str) -> str:
        """Build prompt for research generation."""
        return f"""You are a senior technical architect researching implementation approaches for a feature.

Your task is to analyze the specification and create a comprehensive technical research document.

Feature Specification:
{spec[:3000]}...

Constitutional Principles (follow these):
{constitution[:1000]}...

Research Requirements:
1. Identify technical challenges and unknowns
2. Research relevant technologies, patterns, and frameworks
3. Evaluate multiple options with trade-offs
4. Recommend an approach with clear rationale
5. Assess risks and mitigation strategies
6. Keep technology-agnostic where appropriate (no "use PostgreSQL", but "persistent storage")

Research Document Format:
# Phase 0 Research: [Feature Name] Technical Decisions

**Feature**: [Feature name]
**Date**: YYYY-MM-DD
**Status**: Complete

## 1. [Technical Challenge 1]

### Decision
[What technology/approach to use]

### Rationale
- [Why this approach]
- [Benefits]
- [Alignment with constitutional principles]

### Alternatives Considered
- **[Alternative 1]**: [Why rejected]
- **[Alternative 2]**: [Why rejected]

## 2. [Technical Challenge 2]
...

## Implementation Priorities
[High-level roadmap]

Generate a complete research document following this format:"""

    def _generate_mock_research(self, spec: str) -> str:
        """Generate mock research for testing/development."""
        from datetime import datetime

        # Extract feature name from spec (simple heuristic)
        feature_name = "Feature"
        if "# Feature Specification:" in spec:
            lines = spec.split("\n")
            for line in lines:
                if line.startswith("# Feature Specification:"):
                    feature_name = line.replace("# Feature Specification:", "").strip()
                    break

        return f"""# Phase 0 Research: {feature_name} Technical Decisions

**Feature**: {feature_name}
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Status**: Complete

This document consolidates all technical research decisions for implementing this feature.

---

## 1. Core Architecture Pattern

### Decision
Use **modular architecture** with clear separation of concerns between business logic and infrastructure.

### Rationale
- Enables independent testing of core functionality
- Aligns with library-first architecture (Constitutional Principle VI)
- Facilitates future extensibility
- Reduces coupling and improves maintainability

### Alternatives Considered
- **Monolithic approach**: Rejected due to poor testability and tight coupling
- **Microservices**: Over-engineered for current scope; adds unnecessary complexity

---

## 2. Data Storage Strategy

### Decision
Use **persistent storage layer** with abstract interface to support multiple backends.

### Rationale
- Separation of concerns between data access and business logic
- Technology-agnostic design (can swap storage implementation)
- Enables comprehensive testing with mock storage
- Aligns with specifications as first-class artifacts principle

### Alternatives Considered
- **Hardcoded database choice**: Rejected as too prescriptive for specification phase
- **In-memory only**: Insufficient for production requirements

---

## 3. Error Handling & Validation

### Decision
Implement **defensive validation** at API boundaries with structured error responses.

### Rationale
- Early detection of invalid inputs prevents downstream errors
- Clear error messages improve user experience
- Aligns with quality standards (Constitutional Principle)
- Facilitates debugging and troubleshooting

### Alternatives Considered
- **Optimistic validation**: Rejected due to higher risk of runtime failures
- **No validation**: Violates quality standards and security requirements

---

## Implementation Priorities

### Phase 1: Core Infrastructure
- Setup project structure following library-first pattern
- Implement data models and validation
- Create storage abstraction layer

### Phase 2: Business Logic
- Implement core feature functionality
- Add error handling and validation
- Integration with existing systems

### Phase 3: Testing & Validation
- Unit tests for all components
- Integration tests for end-to-end flows
- Performance testing against success criteria

---

**Note**: This is a mock research document generated for development/testing purposes.
All technical decisions align with constitutional principles and specification requirements.
"""

    # ========================================================
    # PHASE 1: PLAN GENERATION (T052)
    # ========================================================

    def _generate_plan(self, spec: str, research: str, constitution: str) -> str:
        """
        Generate plan.md implementation plan.

        Args:
            spec: Feature specification
            research: Research findings
            constitution: Constitutional principles

        Returns:
            Implementation plan as markdown
        """
        if self.mock_mode:
            return self._generate_mock_plan(spec, research, constitution)

        # Use LLM for plan generation
        prompt = self._build_plan_prompt(spec, research, constitution)

        try:
            response = self.llm.invoke(prompt)
            plan = response.content

            self.log(f"Generated plan ({len(plan)} characters)", level="info")
            return plan

        except Exception as e:
            self.log(f"LLM call failed: {e}", level="error")
            return self._generate_mock_plan(spec, research, constitution)

    def _build_plan_prompt(self, spec: str, research: str, constitution: str) -> str:
        """Build prompt for plan generation."""
        return f"""You are a senior technical architect creating an implementation plan from a specification.

Your task is to generate a comprehensive technical plan following the plan-template format.

Feature Specification:
{spec[:3000]}...

Research Findings:
{research[:2000]}...

Constitutional Principles (validate against these):
{constitution[:1000]}...

Plan Requirements:
1. Describe HOW to build (technical approach), not exact code
2. Stay technology-agnostic where possible
3. Include technical context (language, dependencies, constraints)
4. Define project structure (directories, files)
5. Validate against constitutional principles at start and end
6. Include post-design constitution check

Plan Template Format:
# Implementation Plan: [Feature Name]

**Branch**: `NNN-feature-name` | **Date**: YYYY-MM-DD | **Spec**: [spec.md](./spec.md)

## Summary

[What are we building - 2-3 sentences]

## Technical Context

**Language/Version**: [Programming language and version]
**Primary Dependencies**: [Key libraries/frameworks]
**Storage**: [Data storage approach]
**Testing**: [Testing framework and strategy]
**Target Platform**: [Deployment environment]
**Project Type**: [Single app, microservice, library, etc.]
**Performance Goals**: [Specific targets]
**Constraints**: [Technical limitations or requirements]
**Scale/Scope**: [Expected usage and complexity]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Evaluation (Initial)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specifications as First-Class Artifacts** | ✅/⚠️ | [Evaluation] |
| **II. Constitutional Governance** | ✅/⚠️ | [Evaluation] |
...

**Overall Status**: ✅ **PASS** / ⚠️ **PENDING** / ❌ **FAIL**

## Project Structure

### Source Code (repository structure)

```
[project-root]/
├── [package-name]/           # Main package
│   ├── __init__.py
│   ├── [module1]/
│   └── [module2]/
├── tests/
│   ├── unit/
│   └── integration/
└── [config files]
```

## Post-Design Constitution Check

*Re-evaluated after Phase 1 design artifacts generated*

### Evaluation (After research.md, data-model.md, contracts/, quickstart.md)

| Principle | Status | Notes |
|-----------|--------|-------|
...

**Overall Status**: ✅ **PASS** - All constitutional principles satisfied by design artifacts.

Generate a complete implementation plan following this format:"""

    def _generate_mock_plan(self, spec: str, research: str, constitution: str) -> str:
        """Generate mock plan for testing/development."""
        from datetime import datetime

        # Extract feature name
        feature_name = "Feature"
        if "# Feature Specification:" in spec:
            lines = spec.split("\n")
            for line in lines:
                if line.startswith("# Feature Specification:"):
                    feature_name = line.replace("# Feature Specification:", "").strip()
                    break

        return f"""# Implementation Plan: {feature_name}

**Branch**: `NNN-feature-name` | **Date**: {datetime.now().strftime('%Y-%m-%d')} | **Spec**: [spec.md](./spec.md)

## Summary

This plan outlines the technical approach for implementing {feature_name}. The implementation follows a modular architecture with clear separation between business logic and infrastructure, enabling comprehensive testing and future extensibility.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Core language libraries, testing framework
**Storage**: File-based storage with abstract interface for future extensibility
**Testing**: pytest with comprehensive unit and integration test coverage
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Library-first architecture with CLI wrapper
**Performance Goals**: Sub-second response times for primary operations
**Constraints**: Must support workflow interruption and resume without data loss
**Scale/Scope**: Enterprise development teams, features ranging from simple to complex

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Evaluation (Initial)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specifications as First-Class Artifacts** | ✅ PASS | Spec correctly focuses on WHAT/WHY without implementation details |
| **II. Constitutional Governance** | ✅ PASS | Plan includes governance gates and validation |
| **III. Checkpoint Everything** | ✅ PASS | Design includes state persistence at phase boundaries |
| **VI. Library-First Architecture** | ✅ PASS | Clear separation between core logic and CLI |
| **VII. Test-First** | ✅ PASS | TDD approach with comprehensive test coverage |
| **Enterprise: Security & Compliance** | ✅ PASS | No hardcoded secrets, proper error handling |

**Overall Status**: ✅ **PASS** - No blocking violations.

## Project Structure

### Source Code (repository structure)

```
project-root/
├── src/                      # Source code
│   ├── __init__.py
│   ├── core/                 # Core business logic
│   │   ├── __init__.py
│   │   └── [modules]
│   ├── storage/              # Data persistence
│   │   ├── __init__.py
│   │   └── [storage_layer]
│   └── utils/                # Shared utilities
│       ├── __init__.py
│       └── [helpers]
├── tests/
│   ├── unit/                 # Unit tests
│   │   └── test_*.py
│   └── integration/          # Integration tests
│       └── test_*.py
└── [config files]            # pyproject.toml, etc.
```

**Structure Decision**: Selected library-first pattern with clear separation of concerns. Core logic in `src/core/` can be imported and tested independently of infrastructure layers.

## Post-Design Constitution Check

*Re-evaluated after Phase 1 design artifacts generated*

### Evaluation (After research.md, data-model.md, contracts/, quickstart.md)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specifications as First-Class Artifacts** | ✅ PASS | All design artifacts remain technology-agnostic where appropriate |
| **II. Constitutional Governance** | ✅ PASS | Governance validation integrated at all phase boundaries |
| **III. Checkpoint Everything** | ✅ PASS | State persistence designed with resume capability |
| **VI. Library-First Architecture** | ✅ PASS | Project structure shows clear library/wrapper separation |
| **VII. Test-First** | ✅ PASS | TDD workflow defined with test-first approach |
| **Enterprise: Security & Compliance** | ✅ PASS | Security validation in all design artifacts |

**Overall Status**: ✅ **PASS** - All constitutional principles satisfied by design artifacts.

**Phase 1 Design Complete**: Ready for implementation.

---

**Note**: This is a mock implementation plan generated for development/testing purposes.
"""

    # ========================================================
    # DATA MODEL GENERATION (T053)
    # ========================================================

    def _generate_data_model(self, spec: str, plan: str, constitution: str) -> str:
        """
        Generate data-model.md if feature requires data storage.

        Args:
            spec: Feature specification
            plan: Implementation plan
            constitution: Constitutional principles

        Returns:
            Data model document as markdown (empty string if not needed)
        """
        # Check if feature needs data model (look for keywords in spec)
        needs_data_model = self._check_needs_data_model(spec)

        if not needs_data_model:
            self.log("Feature does not require data model", level="info")
            return ""

        if self.mock_mode:
            return self._generate_mock_data_model(spec, plan)

        # Use LLM for data model generation
        prompt = self._build_data_model_prompt(spec, plan, constitution)

        try:
            response = self.llm.invoke(prompt)
            data_model = response.content

            self.log(f"Generated data model ({len(data_model)} characters)", level="info")
            return data_model

        except Exception as e:
            self.log(f"LLM call failed: {e}", level="error")
            return self._generate_mock_data_model(spec, plan)

    def _check_needs_data_model(self, spec: str) -> bool:
        """
        Check if specification indicates need for data model.

        Args:
            spec: Feature specification

        Returns:
            True if data model needed
        """
        # Keywords that suggest data storage needs
        data_keywords = [
            "store",
            "persist",
            "save",
            "database",
            "entity",
            "entities",
            "model",
            "record",
            "data",
            "checkpoint",
            "state",
        ]

        spec_lower = spec.lower()
        return any(keyword in spec_lower for keyword in data_keywords)

    def _build_data_model_prompt(self, spec: str, plan: str, constitution: str) -> str:
        """Build prompt for data model generation."""
        return f"""You are a data architect creating a technology-agnostic data model.

Your task is to define entities, attributes, and relationships without specifying implementation.

Feature Specification:
{spec[:2000]}...

Implementation Plan:
{plan[:1500]}...

Constitutional Principles:
{constitution[:800]}...

Data Model Requirements:
1. Define entities and their attributes (NO database specifics)
2. Describe relationships between entities
3. Specify constraints and validation rules
4. Stay technology-agnostic (not "PostgreSQL table", but "Entity with attributes")
5. Focus on what data needs to be stored, not how

Data Model Format:
# Data Model: [Feature Name]

**Feature**: [Feature name]
**Date**: YYYY-MM-DD
**Version**: 1.0.0

## Core Entities

### 1. [Entity Name]

**Purpose**: [What this entity represents]

**Attributes**:
- **[Attribute Name]**: [Type and description]
- **[Attribute Name]**: [Type and description]

**Relationships**:
- [Relationship to other entities]

**State Transitions**: [If applicable]

**Validation Rules**:
- [Rule 1]
- [Rule 2]

### 2. [Entity Name]
...

## Relationships Diagram

```
[ASCII diagram showing relationships]
```

Generate a complete data model following this format:"""

    def _generate_mock_data_model(self, spec: str, plan: str) -> str:
        """Generate mock data model for testing/development."""
        from datetime import datetime

        # Extract feature name
        feature_name = "Feature"
        if "# Feature Specification:" in spec:
            lines = spec.split("\n")
            for line in lines:
                if line.startswith("# Feature Specification:"):
                    feature_name = line.replace("# Feature Specification:", "").strip()
                    break

        return f"""# Data Model: {feature_name}

**Feature**: {feature_name}
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Version**: 1.0.0

This document defines all data entities for this feature without specifying implementation details.

---

## Core Entities

### 1. Primary Entity

**Purpose**: Represents the core concept in the feature domain.

**Attributes**:
- **ID**: Unique identifier for the entity
- **Name**: Human-readable name
- **Status**: Current state (ACTIVE, INACTIVE, PENDING)
- **Created At**: Timestamp when entity was created
- **Updated At**: Timestamp of last modification

**Relationships**:
- Has many Related Entities (one-to-many)
- Belongs to one Parent Entity (many-to-one)

**State Transitions**:
```
PENDING → ACTIVE (when validated)
ACTIVE → INACTIVE (when deactivated)
INACTIVE → ACTIVE (when reactivated)
```

**Validation Rules**:
- ID must be unique within system
- Name must be non-empty
- Status must be one of allowed values
- Cannot transition to ACTIVE without passing validation

---

### 2. Related Entity

**Purpose**: Represents supporting data linked to primary entities.

**Attributes**:
- **ID**: Unique identifier
- **Primary Entity ID**: Reference to parent entity
- **Content**: Main content or value
- **Type**: Classification of this related entity
- **Metadata**: Additional structured information

**Relationships**:
- Belongs to one Primary Entity (many-to-one)

**Validation Rules**:
- Primary Entity ID must reference existing entity
- Content must be non-empty
- Type must be from predefined list

---

## Relationships Diagram

```
┌─────────────────┐
│ Primary Entity  │
│ - id            │
│ - name          │
│ - status        │
└────────┬────────┘
         │
         │ has many
         │
┌────────▼────────────┐
│ Related Entity      │
│ - id                │
│ - primary_entity_id │
│ - content           │
└─────────────────────┘
```

---

## Persistence Strategy

**Entity Storage**:
- Each entity stored independently with unique identifier
- Relationships maintained through ID references
- Support for querying by any attribute

**State Management**:
- All state transitions validated before persistence
- Audit trail maintained for all changes
- Support for concurrent access with conflict resolution

---

**Note**: This is a mock data model generated for development/testing purposes.
All entities align with feature specification and constitutional principles.
"""

    # ========================================================
    # API CONTRACTS GENERATION (T054)
    # ========================================================

    def _generate_contracts(self, spec: str, plan: str, constitution: str) -> Dict[str, str]:
        """
        Generate API contract files if feature exposes interfaces.

        Args:
            spec: Feature specification
            plan: Implementation plan
            constitution: Constitutional principles

        Returns:
            Dictionary of contract filename → content (empty if no contracts needed)
        """
        # Check if feature needs API contracts
        needs_contracts = self._check_needs_contracts(spec)

        if not needs_contracts:
            self.log("Feature does not require API contracts", level="info")
            return {}

        if self.mock_mode:
            return self._generate_mock_contracts(spec, plan)

        # Use LLM for contract generation
        prompt = self._build_contracts_prompt(spec, plan, constitution)

        try:
            response = self.llm.invoke(prompt)

            # Parse response into contract files
            contracts = self._parse_contracts_from_response(response.content)

            self.log(f"Generated {len(contracts)} API contract(s)", level="info")
            return contracts

        except Exception as e:
            self.log(f"LLM call failed: {e}", level="error")
            return self._generate_mock_contracts(spec, plan)

    def _check_needs_contracts(self, spec: str) -> bool:
        """
        Check if specification indicates need for API contracts.

        Args:
            spec: Feature specification

        Returns:
            True if API contracts needed
        """
        # Keywords that suggest API needs
        api_keywords = [
            "api",
            "endpoint",
            "interface",
            "service",
            "command",
            "operation",
            "request",
            "response",
        ]

        spec_lower = spec.lower()
        return any(keyword in spec_lower for keyword in api_keywords)

    def _build_contracts_prompt(self, spec: str, plan: str, constitution: str) -> str:
        """Build prompt for contracts generation."""
        return f"""You are an API architect creating interface contracts from a specification.

Your task is to define API contracts (endpoints, parameters, responses) without implementation.

Feature Specification:
{spec[:2000]}...

Implementation Plan:
{plan[:1500]}...

API Contract Requirements:
1. Define endpoints/operations with clear purpose
2. Specify request parameters and validation
3. Define response schemas
4. Include error responses
5. Use OpenAPI 3.0 or similar format
6. Stay technology-agnostic (no server implementation details)

Generate API contracts in YAML format.
If multiple APIs, separate with "---FILE: filename.yaml---" markers.

Example format:
---FILE: main-api.yaml---
openapi: 3.0.0
info:
  title: [Feature Name] API
  version: 1.0.0
paths:
  /resource:
    get:
      summary: [Description]
      parameters: [...]
      responses: [...]

Generate complete API contracts:"""

    def _parse_contracts_from_response(self, response: str) -> Dict[str, str]:
        """Parse contract files from LLM response."""
        contracts = {}

        # Look for ---FILE: filename--- markers
        import re
        files = re.split(r'---FILE:\s*([^\n]+)---', response)

        if len(files) == 1:
            # No markers, treat as single contract
            contracts["api-contract.yaml"] = response
        else:
            # Parse marked files
            for i in range(1, len(files), 2):
                if i + 1 < len(files):
                    filename = files[i].strip()
                    content = files[i + 1].strip()
                    contracts[filename] = content

        return contracts

    def _generate_mock_contracts(self, spec: str, plan: str) -> Dict[str, str]:
        """Generate mock API contracts for testing/development."""
        # Extract feature name
        feature_name = "Feature"
        if "# Feature Specification:" in spec:
            lines = spec.split("\n")
            for line in lines:
                if line.startswith("# Feature Specification:"):
                    feature_name = line.replace("# Feature Specification:", "").strip()
                    break

        contract_content = f"""openapi: 3.0.0
info:
  title: {feature_name} API
  version: 1.0.0
  description: API contract for {feature_name}

paths:
  /resource:
    get:
      summary: List all resources
      description: Retrieve a list of all available resources
      parameters:
        - name: limit
          in: query
          description: Maximum number of results to return
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: offset
          in: query
          description: Number of results to skip
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/Resource'
                  total:
                    type: integer
                  limit:
                    type: integer
                  offset:
                    type: integer
        '400':
          description: Invalid request parameters
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

    post:
      summary: Create a new resource
      description: Create a new resource with provided data
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ResourceInput'
      responses:
        '201':
          description: Resource created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'
        '400':
          description: Invalid input data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /resource/{{id}}:
    get:
      summary: Get resource by ID
      description: Retrieve a specific resource by its unique identifier
      parameters:
        - name: id
          in: path
          required: true
          description: Unique resource identifier
          schema:
            type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Resource'
        '404':
          description: Resource not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  schemas:
    Resource:
      type: object
      required:
        - id
        - name
        - status
      properties:
        id:
          type: string
          description: Unique resource identifier
        name:
          type: string
          description: Resource name
        status:
          type: string
          enum: [active, inactive, pending]
          description: Current resource status
        created_at:
          type: string
          format: date-time
          description: Creation timestamp
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp

    ResourceInput:
      type: object
      required:
        - name
      properties:
        name:
          type: string
          description: Resource name
          minLength: 1
          maxLength: 100

    Error:
      type: object
      required:
        - error
        - message
      properties:
        error:
          type: string
          description: Error code
        message:
          type: string
          description: Human-readable error message
        details:
          type: object
          description: Additional error details
"""

        return {"api-contract.yaml": contract_content}

    # ========================================================
    # QUICKSTART GENERATION (T055)
    # ========================================================

    def _generate_quickstart(self, spec: str, plan: str) -> str:
        """
        Generate quickstart.md with usage examples.

        Note: Quickstart is stored in code_artifacts (not a separate state field).

        Args:
            spec: Feature specification
            plan: Implementation plan

        Returns:
            Quickstart document as markdown
        """
        if self.mock_mode:
            return self._generate_mock_quickstart(spec, plan)

        # Use LLM for quickstart generation
        prompt = self._build_quickstart_prompt(spec, plan)

        try:
            response = self.llm.invoke(prompt)
            quickstart = response.content

            self.log(f"Generated quickstart ({len(quickstart)} characters)", level="info")
            return quickstart

        except Exception as e:
            self.log(f"LLM call failed: {e}", level="error")
            return self._generate_mock_quickstart(spec, plan)

    def _build_quickstart_prompt(self, spec: str, plan: str) -> str:
        """Build prompt for quickstart generation."""
        return f"""You are creating a quickstart guide for developers implementing a feature.

Your task is to generate a practical getting started guide with examples.

Feature Specification:
{spec[:2000]}...

Implementation Plan:
{plan[:1500]}...

Quickstart Requirements:
1. Show how to use the feature after implementation
2. Provide example commands/API calls
3. Include configuration requirements
4. Add common troubleshooting
5. Keep examples practical and runnable

Quickstart Format:
# Quickstart: [Feature Name]

## Prerequisites

- [Requirement 1]
- [Requirement 2]

## Installation

```bash
[Installation commands]
```

## Basic Usage

### Example 1: [Common scenario]

```[language]
[Example code]
```

### Example 2: [Another scenario]

```[language]
[Example code]
```

## Configuration

[Configuration options and examples]

## Common Issues

### Issue: [Problem description]
**Solution**: [How to fix]

Generate a complete quickstart guide:"""

    def _generate_mock_quickstart(self, spec: str, plan: str) -> str:
        """Generate mock quickstart for testing/development."""
        from datetime import datetime

        # Extract feature name
        feature_name = "Feature"
        if "# Feature Specification:" in spec:
            lines = spec.split("\n")
            for line in lines:
                if line.startswith("# Feature Specification:"):
                    feature_name = line.replace("# Feature Specification:", "").strip()
                    break

        return f"""# Quickstart: {feature_name}

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}

This guide helps you get started with {feature_name} quickly.

---

## Prerequisites

- Basic understanding of the system
- Access to the development environment
- Required dependencies installed

## Installation

```bash
# Install the feature
pip install [package-name]

# Verify installation
[command] --version
```

## Basic Usage

### Example 1: Common Scenario

The most common use case is to perform the primary feature operation:

```python
# Import required modules
from feature import FeatureClient

# Initialize client
client = FeatureClient()

# Perform operation
result = client.execute(
    param1="value1",
    param2="value2"
)

# Check result
print(f"Operation completed: {{result.status}}")
```

### Example 2: Advanced Configuration

For more complex scenarios, you can customize the configuration:

```python
# Custom configuration
config = {{
    "option1": "custom_value",
    "option2": True,
    "option3": 100
}}

# Initialize with config
client = FeatureClient(config=config)

# Execute with additional parameters
result = client.execute_advanced(
    param1="value1",
    options={{"retry": 3, "timeout": 30}}
)
```

## Configuration

### Environment Variables

Set these environment variables for proper operation:

```bash
export FEATURE_API_KEY="your-api-key"
export FEATURE_ENVIRONMENT="development"
export FEATURE_LOG_LEVEL="info"
```

### Configuration File

Alternatively, create a configuration file at `~/.feature/config.yaml`:

```yaml
api_key: your-api-key
environment: development
log_level: info
options:
  retry_attempts: 3
  timeout_seconds: 30
```

## Common Issues

### Issue: Authentication Failed

**Symptom**: Error message "Authentication failed: invalid credentials"

**Solution**: Ensure your API key is properly set in environment variables or config file. Verify the key is valid and has not expired.

```bash
# Check current API key
echo $FEATURE_API_KEY

# Set new API key
export FEATURE_API_KEY="your-new-api-key"
```

### Issue: Connection Timeout

**Symptom**: Operation fails with "Connection timeout after 30 seconds"

**Solution**: Check network connectivity and increase timeout in configuration:

```python
config = {{"timeout": 60}}  # Increase to 60 seconds
client = FeatureClient(config=config)
```

### Issue: Resource Not Found

**Symptom**: Error message "Resource not found: [resource-id]"

**Solution**: Verify the resource exists and you have proper access permissions. Use the list command to see available resources:

```python
# List available resources
resources = client.list_resources()
for resource in resources:
    print(f"{{resource.id}}: {{resource.name}}")
```

## Next Steps

- Read the full documentation: [link to docs]
- Review API reference: [link to API docs]
- Check out example projects: [link to examples]
- Join the community: [link to community]

---

**Need Help?**

- File an issue: [link to issue tracker]
- Ask questions: [link to forum/chat]
- Read FAQ: [link to FAQ]

---

**Note**: This is a mock quickstart guide generated for development/testing purposes.
"""


# ============================================================
# AGENT FACTORY
# ============================================================


def create_architect_agent(
    llm: Any = None,
    mock_mode: bool = False,
) -> ArchitectAgent:
    """
    Factory function to create Architect Agent.

    Args:
        llm: LangChain LLM instance (e.g., ChatOpenAI)
        mock_mode: If True, use mock responses instead of LLM

    Returns:
        ArchitectAgent instance

    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> llm = ChatOpenAI(model="gpt-4")
        >>> agent = create_architect_agent(llm=llm)
    """
    return ArchitectAgent(
        llm=llm,
        mock_mode=mock_mode,
    )


# Export
__all__ = ["ArchitectAgent", "create_architect_agent"]
