# Test Fixtures

This directory contains test fixtures and mock data for integration tests.

## Structure

- `sample_specs/` - Example specification files
- `sample_plans/` - Example plan files
- `sample_constitutions/` - Example constitution templates
- `sample_checkpoints/` - Example checkpoint state files

## Usage

Fixtures are loaded via the `fixtures_dir` pytest fixture defined in `tests/conftest.py`:

```python
def test_something(fixtures_dir):
    spec_path = fixtures_dir / "sample_specs" / "001-example.md"
    content = spec_path.read_text()
    # ... test code
```

## Adding New Fixtures

1. Create appropriate subdirectory if needed
2. Add fixture files with descriptive names
3. Document the fixture purpose in this README
4. Use fixtures in integration tests via `fixtures_dir` fixture
