# acpctl - Ambient Code Platform Control

**LangGraph workflow CLI for spec-driven development**

acpctl is a command-line tool that uses LangGraph workflows and AI models to help you with spec-driven software development. It provides workflows for creating specifications, planning implementations, generating tasks, and more.

## Features

- **Specification Generation**: Create comprehensive feature specifications from natural language descriptions
- **Implementation Planning**: Generate detailed technical implementation plans
- **Task Breakdown**: Convert specifications into actionable development tasks
- **Clarification**: Identify and resolve ambiguities in requirements
- **Analysis**: Cross-artifact analysis and validation
- **Flexible AI Integration**: Works with Claude, OpenAI, or custom model providers
- **Customizable Templates**: Bring your own workflow templates
- **Standalone**: No external dependencies on specific project structures

## Installation

```bash
# From PyPI (when published)
pip install acpctl

# Or with uv
uv tool install acpctl

# From source
git clone https://github.com/your-org/acpctl
cd acpctl
uv pip install -e .
```

## Quick Start

### Using with Claude

```bash
export ANTHROPIC_API_KEY=your_key_here
acpctl specify --claude-model claude-sonnet-4 "Add user authentication with OAuth2"
```

### Using with Custom Model Factory

```python
# myproject/ai.py
from langchain_openai import ChatOpenAI

def create_model():
    return ChatOpenAI(model="gpt-4")
```

```bash
acpctl specify --model-factory myproject.ai:create_model "Add user authentication"
```

### Available Commands

- `acpctl specify` - Create or update feature specifications
- `acpctl plan` - Generate implementation plans
- `acpctl tasks` - Break down features into tasks
- `acpctl clarify` - Identify and resolve ambiguities
- `acpctl implement` - Execute implementation workflows
- `acpctl analyze` - Perform cross-artifact analysis
- `acpctl checklist` - Generate quality checklists
- `acpctl constitution` - Manage project constitution

## Configuration

### Template Discovery

acpctl searches for templates in this order:

1. `ACPCTL_TEMPLATE_DIR` environment variable
2. `.acpctl/templates/` in current directory or parents
3. `~/.config/acpctl/templates/` (user config)
4. Built-in example templates

### Custom Templates

Create project-specific templates:

```bash
mkdir -p .acpctl/templates/commands
cat > .acpctl/templates/commands/review.md << 'EOF'
---
description: Review code for quality
---

## Code to Review

\```text
$ARGUMENTS
\```

Review the code above and provide feedback...
EOF

acpctl review "path/to/code.py"
```

See [examples/README.md](examples/README.md) for more details on creating custom templates.

## Model Configuration

### Option 1: Built-in Claude Support

```bash
acpctl specify --claude-model claude-sonnet-4 \
               --claude-temperature 0.0 \
               --claude-max-output-tokens 4096 \
               "your feature"
```

### Option 2: Custom Model Factory

Create a Python module with a callable that returns a LangChain Runnable:

```python
# myproject/models.py
from langchain_anthropic import ChatAnthropic

def get_claude():
    return ChatAnthropic(model="claude-sonnet-4")
```

Use it:

```bash
acpctl plan --model-factory myproject.models:get_claude "implementation plan"
```

### Option 3: Environment Variable

```bash
export ACPCTL_MODEL_FACTORY=myproject.models:get_claude
acpctl tasks "generate tasks"
```

## Repository Root

By default, acpctl uses the current directory. Override with `--repo-root`:

```bash
acpctl specify --repo-root /path/to/project "feature description"
```

## JSON Output

Get machine-readable output with `--json`:

```bash
acpctl specify --json "feature" | jq '.response'
```

## Skip Scripts

Templates can define setup scripts in their YAML front-matter. Skip them with `--skip-scripts`:

```bash
acpctl specify --skip-scripts "feature"
```

## Architecture

acpctl is built on two main components:

1. **CLI Layer** (`acpctl.cli`): Command-line interface using Typer
2. **Workflow Library** (`acpctl_workflows`): LangGraph-based workflow implementations

### Workflow Library

The `acpctl_workflows` package provides:

- **Base Classes**: `SlashCommandWorkflow`, `SlashCommandState`
- **Concrete Workflows**: `SpecifyWorkflow`, `PlanWorkflow`, `TasksWorkflow`, etc.
- **Template System**: Load and render workflow templates
- **Script Execution**: Run setup scripts before workflows
- **Configuration**: Flexible template and script discovery

### How It Works

1. User invokes a command (e.g., `acpctl specify "feature"`)
2. CLI loads the appropriate workflow class
3. Workflow loads its template from configured location
4. Optional setup scripts run
5. LangGraph compiles and executes the workflow
6. AI model processes the prompt with user context
7. Results are returned in YAML or JSON format

## Development

```bash
# Clone and setup
git clone https://github.com/your-org/acpctl
cd acpctl
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -e ".[dev]"

# Run tests
pytest

# Run specific test
pytest tests/test_cli.py::AcpctlCliTests::test_specify_with_model_factory
```

## Examples

See the [examples/](examples/) directory for:

- Example templates
- Custom workflow examples
- Integration examples

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/acpctl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/acpctl/discussions)

## Credits

acpctl was extracted from the [Spec Kit](https://github.com/github/spec-kit) project to provide a standalone, reusable workflow CLI for spec-driven development.
