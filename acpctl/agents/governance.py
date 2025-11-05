"""
acpctl Governance Agent

AI agent for constitutional validation of generated artifacts.
Validates specifications, plans, and code against constitutional principles.

Governance Philosophy:
- Every artifact must pass constitutional validation
- Violations reported with specific locations and suggested fixes
- Actionable feedback enables quick remediation
- Constitutional principles enforce security, quality, and architectural standards

Architecture:
- Extends BaseAgent with LangChain LLM integration
- Loads constitution from state
- Validates artifacts against principles
- Returns structured violation reports

Reference: spec.md (User Story 2), CLAUDE.md (Constitutional Governance)
"""

import re
from typing import Any, Dict, List, Optional

from acpctl.agents.base import BaseAgent
from acpctl.core.state import ACPState


# ============================================================
# VIOLATION MODEL
# ============================================================


class ConstitutionalViolation:
    """
    Represents a constitutional principle violation.

    Attributes:
        principle: Name of violated principle
        location: File location or section reference
        explanation: What was violated and why
        suggestion: Actionable fix recommendation
    """

    def __init__(
        self,
        principle: str,
        location: str,
        explanation: str,
        suggestion: str,
    ):
        """
        Initialize violation.

        Args:
            principle: Violated principle name
            location: Location reference (section, line number, etc.)
            explanation: Violation explanation
            suggestion: Suggested fix
        """
        self.principle = principle
        self.location = location
        self.explanation = explanation
        self.suggestion = suggestion

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Violation(principle={self.principle}, location={self.location})"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "principle": self.principle,
            "location": self.location,
            "explanation": self.explanation,
            "suggestion": self.suggestion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ConstitutionalViolation":
        """Create from dictionary."""
        return cls(
            principle=data["principle"],
            location=data["location"],
            explanation=data["explanation"],
            suggestion=data["suggestion"],
        )


# ============================================================
# GOVERNANCE AGENT
# ============================================================


class GovernanceAgent(BaseAgent):
    """
    Agent for constitutional validation of artifacts.

    Validates generated specifications, plans, and code against
    constitutional principles. Reports violations with specific
    locations and suggested fixes.

    Example:
        >>> agent = GovernanceAgent()
        >>> state = {
        ...     'constitution': '...',
        ...     'spec': '# Feature Spec...',
        ...     'phase': 'specify'
        ... }
        >>> updated_state = agent(state)
        >>> print(updated_state['governance_passes'])
        True
    """

    def __init__(
        self,
        llm: Any = None,
        mock_mode: bool = False,
        strict_mode: bool = True,
    ):
        """
        Initialize Governance Agent.

        Args:
            llm: LangChain LLM instance for validation
            mock_mode: If True, use rule-based validation instead of LLM
            strict_mode: If True, fail on any violation (default: True)
        """
        super().__init__(
            agent_name="Governance Agent",
            agent_type="governance",
        )

        self.llm = llm
        self.mock_mode = mock_mode or llm is None
        self.strict_mode = strict_mode

    def execute(self, state: ACPState) -> ACPState:
        """
        Execute constitutional validation.

        Args:
            state: Current workflow state

        Returns:
            Updated state with governance_passes and violations

        Raises:
            ValueError: If required fields missing
        """
        # Validate required inputs
        self.validate_state_requirements(
            state,
            ["constitution"],
        )

        self.log("Starting constitutional validation", level="info")

        # Determine what artifact to validate based on phase
        phase = state.get("phase", "init")
        artifact = None
        artifact_name = None

        if phase == "specify" and state.get("spec"):
            artifact = state["spec"]
            artifact_name = "specification"
        elif phase == "plan" and state.get("plan"):
            artifact = state["plan"]
            artifact_name = "implementation plan"
        elif phase == "implement" and state.get("code_artifacts"):
            # For implementation, validate all code artifacts
            artifact = str(state["code_artifacts"])
            artifact_name = "code artifacts"
        else:
            # No artifact to validate yet
            self.log(
                f"No artifact ready for validation in phase: {phase}", level="info"
            )
            return self.update_state(
                state,
                {
                    "governance_passes": True,
                    "validation_status": "pending",
                },
            )

        self.log(f"Validating {artifact_name}", level="info")

        # Perform validation
        violations = self._validate_artifact(
            artifact=artifact,
            constitution=state["constitution"],
            artifact_type=artifact_name,
        )

        # Determine if governance passes
        governance_passes = len(violations) == 0

        if governance_passes:
            self.log("Constitutional validation passed", level="info")
        else:
            self.log(
                f"Constitutional validation failed with {len(violations)} violations",
                level="warning",
            )

        # Store violations in state (as JSON string for compatibility)
        # Note: code_artifacts dict expects string values, so we serialize violations
        violations_data = [v.to_dict() for v in violations]

        # Update code_artifacts with violations as JSON string
        import json

        updated_artifacts = state.get("code_artifacts", {}).copy()
        if violations_data:
            updated_artifacts["_governance_violations.json"] = json.dumps(
                violations_data
            )

        return self.update_state(
            state,
            {
                "governance_passes": governance_passes,
                "validation_status": "passed" if governance_passes else "failed",
                "code_artifacts": updated_artifacts,
            },
        )

    def _validate_artifact(
        self,
        artifact: str,
        constitution: str,
        artifact_type: str,
    ) -> List[ConstitutionalViolation]:
        """
        Validate artifact against constitution.

        Args:
            artifact: Artifact content to validate
            constitution: Constitutional principles
            artifact_type: Type of artifact (specification, plan, code)

        Returns:
            List of constitutional violations (empty if passes)
        """
        if self.mock_mode:
            return self._validate_artifact_rules_based(artifact, artifact_type)

        # Use LLM for validation
        prompt = self._build_validation_prompt(artifact, constitution, artifact_type)

        try:
            response = self.llm.invoke(prompt)
            violations = self._parse_violations_from_response(response.content)

            self.log(f"LLM validation found {len(violations)} violations", level="info")
            return violations

        except Exception as e:
            self.log(f"LLM validation failed: {e}", level="error")
            # Fall back to rule-based validation
            return self._validate_artifact_rules_based(artifact, artifact_type)

    def _validate_artifact_rules_based(
        self,
        artifact: str,
        artifact_type: str,
    ) -> List[ConstitutionalViolation]:
        """
        Rule-based validation for mock mode or LLM fallback.

        Args:
            artifact: Artifact content
            artifact_type: Type of artifact

        Returns:
            List of violations detected by rules
        """
        violations = []

        # Rule 1: Specifications must not contain implementation details
        if artifact_type == "specification":
            violations.extend(self._check_implementation_details(artifact))

        # Rule 2: Check for hardcoded secrets
        violations.extend(self._check_for_secrets(artifact))

        # Rule 3: Check for proper structure (has required sections)
        if artifact_type == "specification":
            violations.extend(self._check_spec_structure(artifact))

        return violations

    def _check_implementation_details(self, spec: str) -> List[ConstitutionalViolation]:
        """Check for implementation details in specification."""
        violations = []

        # Common implementation detail keywords
        impl_keywords = [
            # Languages
            r"\bpython\b",
            r"\bjava\b",
            r"\bjavascript\b",
            r"\btypescript\b",
            r"\bgo\b",
            r"\brust\b",
            r"\bruby\b",
            # Frameworks
            r"\bdjango\b",
            r"\bflask\b",
            r"\breact\b",
            r"\bvue\b",
            r"\bangular\b",
            r"\bspring\b",
            # Databases
            r"\bpostgres\b",
            r"\bmysql\b",
            r"\bmongodb\b",
            r"\bredis\b",
            # APIs/Protocols (be careful with REST as it's sometimes OK in specs)
            r"\bgraphql\b",
            r"\bgrpc\b",
            # Libraries
            r"\bnumpy\b",
            r"\bpandas\b",
            r"\btensorflow\b",
            r"\bpytorch\b",
        ]

        for pattern in impl_keywords:
            matches = re.finditer(pattern, spec, re.IGNORECASE)
            for match in matches:
                # Find line number
                line_num = spec[: match.start()].count("\n") + 1

                violations.append(
                    ConstitutionalViolation(
                        principle="Specifications as First-Class Artifacts",
                        location=f"Line {line_num}",
                        explanation=f"Specification contains implementation detail: '{match.group()}'",
                        suggestion="Remove specific technology mentions. Focus on WHAT and WHY, not HOW. Describe capabilities and requirements without naming technologies.",
                    )
                )

        return violations

    def _check_for_secrets(self, artifact: str) -> List[ConstitutionalViolation]:
        """Check for potential hardcoded secrets."""
        violations = []

        # Secret patterns
        secret_patterns = [
            (r"(api[_-]?key|apikey)\s*[:=]\s*['\"][^'\"]{10,}", "API key"),
            (r"(secret|password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{5,}", "Secret/Password"),
            (r"(token|auth[_-]?token)\s*[:=]\s*['\"][^'\"]{10,}", "Auth token"),
            (r"(access[_-]?key|accesskey)\s*[:=]\s*['\"][^'\"]{10,}", "Access key"),
        ]

        for pattern, secret_type in secret_patterns:
            matches = re.finditer(pattern, artifact, re.IGNORECASE)
            for match in matches:
                line_num = artifact[: match.start()].count("\n") + 1

                violations.append(
                    ConstitutionalViolation(
                        principle="Security & Compliance",
                        location=f"Line {line_num}",
                        explanation=f"Potential hardcoded {secret_type.lower()} detected",
                        suggestion=f"Remove hardcoded {secret_type.lower()}. Use environment variables, secret management systems, or configuration files (excluded from version control).",
                    )
                )

        return violations

    def _check_spec_structure(self, spec: str) -> List[ConstitutionalViolation]:
        """Check if specification has required sections."""
        violations = []

        required_sections = [
            ("## User Scenarios", "User Scenarios & Testing"),
            ("## Requirements", "Requirements"),
            ("## Success Criteria", "Success Criteria"),
        ]

        for section_marker, section_name in required_sections:
            if section_marker not in spec:
                violations.append(
                    ConstitutionalViolation(
                        principle="Specifications as First-Class Artifacts",
                        location="Document structure",
                        explanation=f"Missing required section: {section_name}",
                        suggestion=f"Add {section_name} section following spec-template format. This section is mandatory for complete specifications.",
                    )
                )

        return violations

    def _build_validation_prompt(
        self,
        artifact: str,
        constitution: str,
        artifact_type: str,
    ) -> str:
        """Build prompt for LLM-based validation."""
        return f"""You are a governance validator ensuring artifacts follow constitutional principles.

Your task is to validate this {artifact_type} against the constitutional principles.

Constitutional Principles:
{constitution[:2000]}...

Artifact to Validate:
{artifact[:3000]}...

Validation Instructions:
1. Check if the artifact violates any constitutional principles
2. For each violation, identify:
   - Which principle was violated
   - Where in the artifact (section, line, or general location)
   - What the violation is (clear explanation)
   - How to fix it (actionable suggestion)
3. Be strict but fair - only report actual violations
4. Focus on the most important principles for this artifact type

Return your findings as a numbered list of violations.
If no violations found, return "NO_VIOLATIONS".

Format each violation as:
VIOLATION: [Principle Name]
LOCATION: [Section/line reference]
EXPLANATION: [What is wrong]
SUGGESTION: [How to fix]

Your validation:"""

    def _parse_violations_from_response(
        self, response_text: str
    ) -> List[ConstitutionalViolation]:
        """Parse violations from LLM response."""
        if "NO_VIOLATIONS" in response_text.upper():
            return []

        violations = []

        # Split by VIOLATION: markers
        violation_blocks = re.split(r"VIOLATION:", response_text)

        for block in violation_blocks[1:]:  # Skip first split (before first VIOLATION:)
            try:
                # Extract fields using regex
                principle_match = re.search(r"^([^\n]+)", block)
                location_match = re.search(r"LOCATION:\s*([^\n]+)", block)
                explanation_match = re.search(r"EXPLANATION:\s*([^\n]+)", block)
                suggestion_match = re.search(r"SUGGESTION:\s*([^\n]+)", block)

                if (
                    principle_match
                    and location_match
                    and explanation_match
                    and suggestion_match
                ):
                    violations.append(
                        ConstitutionalViolation(
                            principle=principle_match.group(1).strip(),
                            location=location_match.group(1).strip(),
                            explanation=explanation_match.group(1).strip(),
                            suggestion=suggestion_match.group(1).strip(),
                        )
                    )
            except Exception as e:
                # Skip malformed violation blocks
                continue

        return violations

    def get_violations_from_state(
        self, state: ACPState
    ) -> List[ConstitutionalViolation]:
        """
        Extract violations from state.

        Args:
            state: Workflow state

        Returns:
            List of violations (empty if none)
        """
        import json

        violations_json = (
            state.get("code_artifacts", {}).get("_governance_violations.json", "[]")
        )

        try:
            violations_data = json.loads(violations_json)
            return [
                ConstitutionalViolation.from_dict(v)
                for v in violations_data
                if isinstance(v, dict)
            ]
        except (json.JSONDecodeError, TypeError):
            return []


# ============================================================
# AGENT FACTORY
# ============================================================


def create_governance_agent(
    llm: Any = None,
    mock_mode: bool = False,
    strict_mode: bool = True,
) -> GovernanceAgent:
    """
    Factory function to create Governance Agent.

    Args:
        llm: LangChain LLM instance
        mock_mode: If True, use rule-based validation
        strict_mode: If True, fail on any violation

    Returns:
        GovernanceAgent instance

    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> llm = ChatOpenAI(model="gpt-4")
        >>> agent = create_governance_agent(llm=llm)
    """
    return GovernanceAgent(
        llm=llm,
        mock_mode=mock_mode,
        strict_mode=strict_mode,
    )


# Export
__all__ = [
    "GovernanceAgent",
    "ConstitutionalViolation",
    "create_governance_agent",
]
