# acpctl Architecture

This document describes the architecture and design of acpctl.

## Overview

acpctl is a command-line tool that provides LangGraph-based workflows for spec-driven software development. It consists of two main layers:

1. **CLI Layer** (`acpctl`): User interface and command handling
2. **Workflow Library** (`acpctl_workflows`): Core workflow engine and implementations

## Components

### CLI Layer (`acpctl.cli`)

**Responsibilities:**
- Parse command-line arguments
- Load and initialize AI models
- Invoke workflows with user input
- Format and display results

**Key Functions:**

- `_load_factory()`: Import and instantiate custom model factories
- `_build_claude_model()`: Create Claude model instances
- `_resolve_model_selection()`: Choose between Claude and custom models
- `_initialise_context()`: Set up execution context with model
- `_run_workflow()`: Execute a workflow with given arguments
- `_print_output()`: Format results as JSON or YAML

**Command Structure:**

Each command (specify, plan, tasks, etc.) follows this pattern:

```python
@app.command()
def specify(
    arguments: Optional[List[str]],
    repo_root: Optional[Path],
    model_factory: Optional[str],
    claude_model: Optional[str],
    # ... more options
):
    # Resolve model configuration
    model_factory, prebuilt_model = _resolve_model_selection(...)

    # Execute workflow
    _common_options(
        arguments,
        workflow_cls=SpecifyWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        # ... more parameters
    )
```

### Workflow Library (`acpctl_workflows`)

#### Base Classes

**`SlashCommandState` (state.py)**

TypedDict defining the state structure for all workflows:

```python
class SlashCommandState(TypedDict):
    arguments: str           # User input
    context: Dict[str, Any]  # Additional context
    response: Any            # Workflow output
    script_result: Optional[ScriptResult]  # Setup script results
```

**`SlashCommandWorkflow` (workflow.py)**

Abstract base class for all workflows:

```python
class SlashCommandWorkflow:
    def __init__(self, repo_root: Path)
    def initial_state(arguments: str, context: Dict) -> SlashCommandState
    def prepare_context(state: SlashCommandState) -> Dict[str, Any]
    def compile(model: Runnable, agent: str, run_scripts: bool) -> CompiledGraph
```

**Workflow Execution Flow:**

```
1. Load template from disk
2. Run optional setup scripts
3. Prepare context (read files, gather data)
4. Render prompt with template + context
5. Send to AI model
6. Return structured response
```

#### Concrete Workflows (commands.py)

Each workflow implements `prepare_context()` to load relevant files:

- **`SpecifyWorkflow`**: Creates feature specifications
- **`PlanWorkflow`**: Generates implementation plans
- **`TasksWorkflow`**: Breaks down features into tasks
- **`ClarifyWorkflow`**: Identifies ambiguities
- **`ImplementWorkflow`**: Guides implementation
- **`AnalyzeWorkflow`**: Cross-artifact analysis
- **`ChecklistWorkflow`**: Quality checklists
- **`ConstitutionWorkflow`**: Project constitution management

**Example Implementation:**

```python
class SpecifyWorkflow(SlashCommandWorkflow):
    def prepare_context(self, state: SlashCommandState) -> Dict[str, Any]:
        # Load existing spec if it exists
        spec_file = self.repo_root / "spec.md"
        if spec_file.exists():
            return {"existing_spec": spec_file.read_text()}
        return {}
```

#### Template System (templates.py)

**Template Format:**

```markdown
---
description: Brief description
scripts:
  sh: path/to/setup.sh
  ps: path/to/setup.ps1
---

## Prompt Content

$ARGUMENTS will be replaced with user input
```

**Template Loading:**

```python
def load_template(command_name: str, root: Path = None) -> SlashCommandTemplate:
    # Discover template directory
    template_dir = get_template_dir() if root is None else root / "templates"

    # Load template file
    template_path = template_dir / "commands" / f"{command_name}.md"

    # Parse YAML front-matter
    # Extract body
    # Return SlashCommandTemplate object
```

#### Configuration System (config.py)

**Template Discovery:**

```python
def get_template_dir(override: Optional[Path] = None) -> Path:
    """
    Priority:
    1. override parameter
    2. ACPCTL_TEMPLATE_DIR env var
    3. .acpctl/templates/ in project
    4. ~/.config/acpctl/templates/
    5. examples/templates/ (fallback)
    """
```

**Script Discovery:**

```python
def get_script_dir(template_dir: Path) -> Path:
    """Returns template_dir/../scripts"""
```

#### Script Execution (scripts.py)

**Platform Detection:**

```python
def detect_variant() -> str:
    """Returns 'sh' for Unix, 'ps' for Windows"""
```

**Script Running:**

```python
def run_setup_script(
    template: SlashCommandTemplate,
    repo_root: Path,
    arguments: str,
    agent: Optional[str]
) -> ScriptResult:
    # Detect platform (sh/ps)
    # Get script command from template
    # Replace {ARGS} and {AGENT} placeholders
    # Execute with subprocess
    # Capture stdout/stderr
    # Return ScriptResult
```

## Data Flow

```
User Input
    ↓
CLI Parser (typer)
    ↓
Model Resolution (factory/claude/default)
    ↓
Workflow Selection (SpecifyWorkflow, etc.)
    ↓
Template Loading (config → templates)
    ↓
Setup Scripts (optional, scripts.py)
    ↓
Context Preparation (workflow.prepare_context)
    ↓
LangGraph Compilation (workflow.compile)
    ↓
Graph Execution (LangGraph)
    ↓
AI Model Invocation (Claude/Custom)
    ↓
Response Processing (state → output)
    ↓
Output Formatting (JSON/YAML)
    ↓
Display to User
```

## Extension Points

### Custom Workflows

Create a new workflow by subclassing `SlashCommandWorkflow`:

```python
from acpctl_workflows import SlashCommandWorkflow

class CustomWorkflow(SlashCommandWorkflow):
    def prepare_context(self, state):
        # Load your custom context
        return {"custom_data": "..."}
```

### Custom Templates

Add templates to discovery path:

```bash
mkdir -p .acpctl/templates/commands
# Create your-command.md
acpctl your-command "arguments"
```

### Custom Model Providers

Implement a factory function:

```python
from langchain_openai import ChatOpenAI

def create_model():
    return ChatOpenAI(model="gpt-4o")
```

Use it:

```bash
acpctl specify --model-factory mymodule:create_model "feature"
```

## Design Decisions

### Why LangGraph?

LangGraph provides:
- Stateful workflow management
- Conditional execution paths
- Built-in LangChain integration
- Extensibility for complex workflows

### Why TypedDict for State?

- Type safety without runtime overhead
- IDE autocomplete support
- Clear contract for workflow state
- Compatible with LangGraph requirements

### Why Template Discovery?

- **Flexibility**: Projects can customize workflows
- **Separation**: Templates separate from code
- **Reusability**: Share templates across projects
- **Evolution**: Update prompts without code changes

### Why Split CLI and Workflows?

- **Modularity**: Workflows usable outside CLI
- **Testing**: Test workflows independently
- **Reusability**: Import workflows in other tools
- **Clarity**: Clear separation of concerns

## Dependencies

### Core Dependencies

- **typer**: CLI framework
- **rich**: Terminal output formatting
- **langgraph**: Workflow engine
- **langchain-core**: LLM abstractions
- **pyyaml**: Template front-matter parsing
- **langchain-anthropic**: Claude integration (optional)

### Why These Dependencies?

- **typer**: Type-safe CLI with great UX
- **rich**: Beautiful terminal output
- **langgraph**: Purpose-built for LLM workflows
- **langchain-core**: Standard LLM interface
- **pyyaml**: De facto YAML parser

## Performance Considerations

### Template Caching

Templates are loaded on each invocation (no caching). This is intentional:
- Templates may change between runs
- Memory footprint stays small
- Simplifies implementation

### Model Initialization

Models are initialized once per CLI invocation and reused across workflow nodes. This avoids recreating connections.

### Script Execution

Setup scripts run synchronously before workflow execution. For long-running scripts, consider:
- Using `--skip-scripts` flag
- Moving heavy setup outside acpctl
- Caching script results

## Security

### Script Execution

Scripts from templates are executed with subprocess. Risks:
- Arbitrary code execution from templates
- Templates should be treated as code
- Review templates before use

### API Keys

API keys are passed via environment variables:
- Not logged or printed
- Not included in output by default
- Follow model provider security practices

### Template Injection

Template `$ARGUMENTS` are not escaped. If using untrusted input:
- Validate arguments before passing
- Sanitize user input
- Review templates for injection risks

## Future Enhancements

Potential improvements:

1. **Streaming Output**: Stream AI responses to terminal
2. **Parallel Workflows**: Run multiple workflows concurrently
3. **Workflow Chaining**: Pipe outputs between workflows
4. **Template Validation**: Lint templates for correctness
5. **Plugin System**: Load workflows from external packages
6. **Interactive Mode**: REPL for iterative development
7. **Workflow Observability**: Trace workflow execution
8. **Result Caching**: Cache expensive operations

## Testing Strategy

### Unit Tests

- Test individual functions in isolation
- Mock external dependencies (models, file I/O)
- Verify error handling

### Integration Tests

- Test full command execution
- Use test fixtures for templates
- Verify JSON/YAML output format

### End-to-End Tests

- Test with real AI models (optional)
- Verify template discovery
- Test script execution

## Troubleshooting

### Template Not Found

Check discovery order:
1. `echo $ACPCTL_TEMPLATE_DIR`
2. `ls .acpctl/templates/commands/`
3. `ls ~/.config/acpctl/templates/commands/`

### Model Errors

- Verify API keys: `echo $ANTHROPIC_API_KEY`
- Check model factory import path
- Test model factory independently

### Script Failures

- Run with `--skip-scripts` to isolate issue
- Check script executable permissions
- Verify script paths in template front-matter
