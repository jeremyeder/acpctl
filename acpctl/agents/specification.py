"""
acpctl Specification Agent

AI agent for generating feature specifications with pre-flight questionnaire.
Implements two-phase operation: clarification collection then spec generation.

Specification Philosophy:
- Specifications describe WHAT and WHY, never HOW
- No implementation details (languages, frameworks, databases)
- Focus on user scenarios, requirements, success criteria
- All ambiguities resolved before generation

Architecture:
- Extends BaseAgent with LangChain LLM integration
- Two-phase operation: pre-flight questions → spec generation
- Uses spec-template format for output
- Stores questions and answers in state for reproducibility

Reference: spec.md (User Story 2), CLAUDE.md (Agent Architecture)
"""

from typing import Any, Dict, List

from acpctl.agents.base import BaseAgent
from acpctl.core.state import ACPState


# ============================================================
# SPECIFICATION AGENT
# ============================================================


class SpecificationAgent(BaseAgent):
    """
    Agent for generating feature specifications with pre-flight questions.

    Two-phase workflow:
    1. Pre-flight Phase: Analyze feature description, generate clarifying questions
    2. Generation Phase: Create spec.md using answers and spec template

    Example:
        >>> agent = SpecificationAgent()
        >>> state = {
        ...     'feature_description': 'Add OAuth2 authentication',
        ...     'constitution': '...',
        ...     'clarifications': []
        ... }
        >>> updated_state = agent(state)
        >>> print(updated_state['spec'])
    """

    def __init__(
        self,
        llm: Any = None,
        max_questions: int = 10,
        mock_mode: bool = False,
    ):
        """
        Initialize Specification Agent.

        Args:
            llm: LangChain LLM instance (e.g., ChatOpenAI). If None, uses mock mode.
            max_questions: Maximum number of clarifying questions (default: 10)
            mock_mode: If True, use mock responses instead of LLM
        """
        super().__init__(
            agent_name="Specification Agent",
            agent_type="specification",
        )

        self.llm = llm
        self.max_questions = max_questions
        self.mock_mode = mock_mode or llm is None

    def execute(self, state: ACPState) -> ACPState:
        """
        Execute specification generation workflow.

        Args:
            state: Current workflow state

        Returns:
            Updated state with spec and clarifications

        Raises:
            ValueError: If required fields missing
        """
        # Validate required inputs
        self.validate_state_requirements(
            state,
            ["feature_description", "constitution"],
        )

        self.log("Starting specification generation", level="info")

        # Check if we have clarifications already (regeneration case)
        if state.get("clarifications") and len(state["clarifications"]) > 0:
            self.log("Using existing clarifications from previous run", level="info")
            spec = self._generate_spec_with_clarifications(state)
        else:
            # This is first run - questions should have been collected in CLI
            # If we reach here without clarifications, it means no questions were needed
            self.log(
                "No clarifications needed, generating spec directly", level="info"
            )
            spec = self._generate_spec_with_clarifications(state)

        # Update state with generated spec
        return self.update_state(
            state,
            {
                "spec": spec,
                "phase": "specify",  # Mark as in specification phase
            },
        )

    def generate_preflight_questions(self, feature_description: str) -> List[str]:
        """
        Analyze feature description and generate clarifying questions.

        This is called BEFORE workflow execution to collect all clarifications upfront.

        Args:
            feature_description: Natural language feature description

        Returns:
            List of clarifying questions (max: max_questions)

        Example:
            >>> agent = SpecificationAgent()
            >>> questions = agent.generate_preflight_questions("Add OAuth2 authentication")
            >>> print(questions[0])
            'Which OAuth2 providers should be supported (Google, GitHub, etc.)?'
        """
        self.log(
            f"Analyzing feature description for ambiguities: {feature_description[:50]}...",
            level="info",
        )

        if self.mock_mode:
            return self._generate_mock_questions(feature_description)

        # Use LLM to identify ambiguities
        prompt = self._build_preflight_prompt(feature_description)

        try:
            response = self.llm.invoke(prompt)
            questions = self._parse_questions_from_response(response.content)

            # Limit to max_questions
            if len(questions) > self.max_questions:
                self.log(
                    f"Truncating {len(questions)} questions to {self.max_questions}",
                    level="warning",
                )
                questions = questions[: self.max_questions]

            self.log(f"Generated {len(questions)} clarifying questions", level="info")
            return questions

        except Exception as e:
            self.log(f"LLM call failed: {e}", level="error")
            # Fall back to mock questions
            return self._generate_mock_questions(feature_description)

    def _generate_spec_with_clarifications(self, state: ACPState) -> str:
        """
        Generate specification using feature description and clarifications.

        Args:
            state: State containing feature_description, clarifications, constitution

        Returns:
            Generated specification as markdown string
        """
        feature_description = state["feature_description"]
        clarifications = state.get("clarifications", [])
        constitution = state.get("constitution", "")

        self.log("Generating specification document", level="info")

        if self.mock_mode:
            return self._generate_mock_spec(
                feature_description, clarifications, constitution
            )

        # Use LLM to generate spec
        prompt = self._build_spec_generation_prompt(
            feature_description, clarifications, constitution
        )

        try:
            response = self.llm.invoke(prompt)
            spec = response.content

            self.log(f"Generated spec ({len(spec)} characters)", level="info")
            return spec

        except Exception as e:
            self.log(f"LLM call failed: {e}", level="error")
            # Fall back to mock spec
            return self._generate_mock_spec(
                feature_description, clarifications, constitution
            )

    def _build_preflight_prompt(self, feature_description: str) -> str:
        """Build prompt for pre-flight question generation."""
        return f"""You are a technical product analyst helping to create a complete feature specification.

Your task is to analyze this feature description and identify all ambiguities that need clarification before writing a specification.

Feature Description:
{feature_description}

Instructions:
1. Identify aspects that are unclear or ambiguous
2. Ask specific, targeted questions that will help create a complete specification
3. Focus on WHAT and WHY, not HOW (no implementation details needed)
4. Generate no more than {self.max_questions} questions
5. Each question should be answerable and actionable

Return your questions as a numbered list, one per line.

Example format:
1. What is the primary user persona for this feature?
2. What specific problem does this solve for users?
3. Are there any security or compliance requirements?

Your questions:"""

    def _build_spec_generation_prompt(
        self,
        feature_description: str,
        clarifications: List[str],
        constitution: str,
    ) -> str:
        """Build prompt for specification generation."""
        clarifications_text = (
            "\n".join(f"{i+1}. {c}" for i, c in enumerate(clarifications))
            if clarifications
            else "No clarifications provided (feature description is complete)."
        )

        return f"""You are a technical specification writer creating a feature specification document.

Your task is to generate a complete feature specification following the provided template format.

Feature Description:
{feature_description}

Clarifications:
{clarifications_text}

Constitutional Principles (follow these):
{constitution[:1000]}...

Specification Requirements:
1. Describe WHAT and WHY, never HOW
2. NO implementation details (no languages, frameworks, databases, APIs)
3. Focus on user scenarios, requirements, and success criteria
4. Use clear, unambiguous language
5. Follow the spec-template format

Spec Template Format:
# Feature Specification: [Feature Name]

**Feature Branch**: `NNN-feature-name`
**Created**: YYYY-MM-DD
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - [Story Title] (Priority: P1/P2/P3)

[Description of who needs this and why]

**Why this priority**: [Explanation]

**Independent Test**: [How this can be tested independently]

**Acceptance Scenarios**:

1. **Given** [context], **When** [action], **Then** [expected outcome]
2. **Given** [context], **When** [action], **Then** [expected outcome]
...

### Edge Cases

- [Edge case 1]
- [Edge case 2]

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: [Requirement description using MUST/SHOULD/MAY keywords]
- **FR-002**: [Requirement description]
...

### Key Entities

- **Entity Name**: [Description of what this represents in the domain]
...

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: [Specific, measurable success criterion]
- **SC-002**: [Specific, measurable success criterion]
...

Generate a complete specification following this format:"""

    def _parse_questions_from_response(self, response_text: str) -> List[str]:
        """
        Parse questions from LLM response.

        Args:
            response_text: Raw LLM response

        Returns:
            List of parsed questions
        """
        questions = []
        lines = response_text.strip().split("\n")

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Remove numbering (1., 2., 1), 2), etc.)
            import re

            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)

            # Must be a question (ends with ?)
            if cleaned and cleaned.endswith("?"):
                questions.append(cleaned)

        return questions

    def _generate_mock_questions(self, feature_description: str) -> List[str]:
        """
        Generate mock questions for testing/development.

        Args:
            feature_description: Feature description

        Returns:
            List of mock clarifying questions
        """
        # Generate contextual mock questions based on feature description
        return [
            f"Who is the primary user persona for '{feature_description}'?",
            f"What specific problem does this feature solve?",
            "Are there any security or compliance requirements to consider?",
            "What are the expected performance characteristics?",
            "Are there any integration points with existing systems?",
        ]

    def _generate_mock_spec(
        self,
        feature_description: str,
        clarifications: List[str],
        constitution: str,
    ) -> str:
        """
        Generate mock specification for testing/development.

        Args:
            feature_description: Feature description
            clarifications: List of Q&A pairs
            constitution: Constitutional principles

        Returns:
            Mock specification as markdown
        """
        from datetime import datetime

        # Simple sanitization for feature name
        feature_name = feature_description[:60].strip()

        return f"""# Feature Specification: {feature_name}

**Feature Branch**: `NNN-{feature_name.lower().replace(' ', '-')}`
**Created**: {datetime.now().strftime('%Y-%m-%d')}
**Status**: Draft
**Input**: User description: "{feature_description}"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Implement Core Functionality (Priority: P1)

A user needs {feature_description.lower()} to accomplish their goals effectively.

**Why this priority**: Core functionality is essential for feature viability.

**Independent Test**: Can be tested by verifying the primary use case works end-to-end.

**Acceptance Scenarios**:

1. **Given** a user wants to use this feature, **When** they access the functionality, **Then** they can complete their primary task successfully
2. **Given** the feature is in use, **When** an error occurs, **Then** the user receives clear feedback with actionable next steps
3. **Given** the feature is complete, **When** validated against requirements, **Then** all acceptance criteria are met

### Edge Cases

- What happens when invalid input is provided?
- How does the system handle concurrent usage?
- What are the failure modes and recovery mechanisms?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement {feature_description.lower()} as described in the feature description
- **FR-002**: System MUST provide clear user feedback for all operations
- **FR-003**: System MUST handle errors gracefully with meaningful error messages
- **FR-004**: System MUST validate all inputs according to business rules
- **FR-005**: System MUST maintain data consistency throughout operations

### Key Entities

- **Primary Entity**: Represents the core concept in this feature domain
- **User Context**: Represents the user's current state and permissions
- **Operation Result**: Represents the outcome of feature operations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Primary use case completes successfully in under 5 seconds
- **SC-002**: Feature operates with 99.9% uptime under normal load
- **SC-003**: User satisfaction ratings indicate feature meets needs (score > 4.0/5.0)
- **SC-004**: Error rates remain below 1% of all operations
- **SC-005**: Feature handles expected load (X concurrent users) without degradation

---

**Note**: This is a mock specification generated for development/testing purposes.
Clarifications provided: {len(clarifications)}
"""


# ============================================================
# AGENT FACTORY
# ============================================================


def create_specification_agent(
    llm: Any = None,
    max_questions: int = 10,
    mock_mode: bool = False,
) -> SpecificationAgent:
    """
    Factory function to create Specification Agent.

    Args:
        llm: LangChain LLM instance (e.g., ChatOpenAI)
        max_questions: Maximum number of clarifying questions
        mock_mode: If True, use mock responses instead of LLM

    Returns:
        SpecificationAgent instance

    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> llm = ChatOpenAI(model="gpt-4")
        >>> agent = create_specification_agent(llm=llm)
    """
    return SpecificationAgent(
        llm=llm,
        max_questions=max_questions,
        mock_mode=mock_mode,
    )


# Export
__all__ = ["SpecificationAgent", "create_specification_agent"]
