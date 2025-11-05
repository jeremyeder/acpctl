"""Pytest configuration for acpctl tests."""

from pathlib import Path

import pytest


@pytest.fixture
def repo_root():
    """Return the repository root directory."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def example_templates(repo_root):
    """Return the example templates directory."""
    return repo_root / "examples" / "templates"
