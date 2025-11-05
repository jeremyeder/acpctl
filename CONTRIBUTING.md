# Contributing to acpctl

Thank you for your interest in contributing to acpctl! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.11 or higher
- uv (recommended) or pip
- Git

### Development Setup

1. **Fork and clone the repository:**

```bash
git clone https://github.com/your-username/acpctl
cd acpctl
```

2. **Create a virtual environment:**

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install in development mode:**

```bash
uv pip install -e ".[dev]"
```

4. **Verify installation:**

```bash
acpctl --help
pytest
```

## Development Workflow

### Branching Strategy

- `main` - Stable release branch
- `develop` - Integration branch for features
- `feature/*` - Feature development
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

### Making Changes

1. **Create a feature branch:**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes:**
   - Write code following our style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests locally:**

```bash
pytest
black .
isort .
```

4. **Commit your changes:**

```bash
git add .
git commit -m "Brief description of changes"
```

5. **Push and create a pull request:**

```bash
git push origin feature/your-feature-name
```

## Code Style

### Python Code

We use:
- **black** for code formatting (88 char line length)
- **isort** for import sorting
- **Type hints** for all function signatures
- **Docstrings** for all public functions (Google style)

Run formatters:

```bash
black src/ tests/
isort src/ tests/
```

### Example

```python
"""Module docstring."""

from __future__ import annotations

from typing import Optional


def process_data(input_data: str, limit: Optional[int] = None) -> dict[str, any]:
    """Process input data and return results.

    Args:
        input_data: The input data to process
        limit: Optional limit for processing

    Returns:
        Dictionary containing processed results

    Raises:
        ValueError: If input_data is empty
    """
    if not input_data:
        raise ValueError("input_data cannot be empty")

    return {"processed": input_data, "limit": limit}
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_cli.py

# Specific test
pytest tests/test_cli.py::AcpctlCliTests::test_specify_with_model_factory

# With coverage
pytest --cov=acpctl --cov=acpctl_workflows
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names
- Include docstrings for complex tests

Example:

```python
def test_template_loading_with_custom_path():
    """Verify template loads from custom directory."""
    custom_dir = Path("/tmp/custom_templates")
    template = load_template("specify", root=custom_dir)
    assert template.name == "specify"
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief one-line description.

    Longer description if needed, explaining what the
    function does in more detail.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
```

### README Updates

When adding features:
- Update README.md with usage examples
- Update feature list
- Add to Quick Start if appropriate

### Documentation Files

- Architecture changes → Update `docs/ARCHITECTURE.md`
- New workflows → Document in README and examples
- Configuration changes → Update README configuration section

## Adding Features

### New Workflows

1. **Create workflow class in `acpctl_workflows/commands.py`:**

```python
class NewWorkflow(SlashCommandWorkflow):
    """Workflow for doing something new."""

    def prepare_context(self, state: SlashCommandState) -> dict[str, any]:
        """Prepare context specific to this workflow."""
        # Load necessary files
        # Return context dict
        return {}
```

2. **Export in `acpctl_workflows/__init__.py`:**

```python
from .commands import NewWorkflow

__all__ = [..., "NewWorkflow"]
```

3. **Add CLI command in `acpctl/cli.py`:**

```python
@app.command()
def new_command(arguments: Optional[List[str]] = None, ...):
    """Brief description of new command."""
    _common_options(
        arguments,
        workflow_cls=NewWorkflow,
        ...
    )
```

4. **Create example template in `examples/templates/commands/new_command.md`**

5. **Add tests in `tests/test_cli.py`**

6. **Update documentation**

### New Configuration Options

1. Add to `acpctl_workflows/config.py`
2. Update environment variable documentation
3. Add tests
4. Update README configuration section

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code is formatted (black, isort)
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. Maintainer reviews code
2. CI runs tests
3. Feedback addressed
4. Approved and merged

## Issue Reporting

### Bug Reports

Include:
- acpctl version (`acpctl --version`)
- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag: `git tag v0.2.0`
4. Push tag: `git push --tags`
5. Build: `uv build`
6. Publish: `uv publish`

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## License

By contributing to acpctl, you agree that your contributions will be licensed under the Apache License 2.0.

Thank you for contributing! 🎉
