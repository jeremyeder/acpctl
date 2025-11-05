"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides shared fixtures
for all test modules.
"""

import json
from pathlib import Path
from typing import Any, Generator

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "integration" / "fixtures"


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary project directory for testing.

    Yields:
        Path to temporary project directory with .acp structure
    """
    # Create .acp directory structure
    acp_dir = tmp_path / ".acp"
    acp_dir.mkdir()
    (acp_dir / "templates").mkdir()
    (acp_dir / "state").mkdir()

    yield tmp_path


@pytest.fixture
def sample_constitution() -> str:
    """Return sample constitution content for testing."""
    return """# Project Constitution

## Core Principles

1. **Specifications as First-Class Artifacts**: Code serves specs, not vice versa
2. **Constitutional Governance**: Every artifact validated against principles
3. **Checkpoint Everything**: Save state after every phase completion

## Enterprise Requirements

- No secrets in code
- Apache 2.0 license compliance
- Complete audit trails

## Quality Standards

- Type safety with Pydantic
- 80% test coverage minimum
- Clear error messages
"""


@pytest.fixture
def sample_spec() -> dict[str, Any]:
    """Return sample specification data for testing."""
    return {
        "feature_id": "001",
        "feature_name": "test-feature",
        "description": "A test feature for unit testing",
        "acceptance_criteria": [
            "System creates test artifacts",
            "Validation passes",
        ],
        "success_metrics": [
            "Feature works as expected",
        ],
    }


@pytest.fixture
def sample_checkpoint_state() -> dict[str, Any]:
    """Return sample checkpoint state for testing."""
    return {
        "feature_id": "001",
        "feature_name": "test-feature",
        "thread_id": "test-thread-123",
        "status": "SPECIFICATION_COMPLETE",
        "phases_completed": ["INIT", "SPECIFICATION"],
        "constitution": "# Test Constitution\n\n## Principles\n\n- Test principle",
        "governance_passes": True,
        "feature_description": "A test feature",
        "spec": "# Test Spec\n\n## Overview\n\nTest specification content",
        "clarifications": ["What is the expected behavior?"],
        "version": "1.0.0",
    }


@pytest.fixture
def mock_llm_response() -> dict[str, str]:
    """Return mock LLM response for testing."""
    return {
        "spec": "# Feature Specification\n\n## Overview\n\nGenerated specification",
        "questions": json.dumps(
            [
                "What is the primary use case?",
                "Are there any constraints?",
            ]
        ),
    }
