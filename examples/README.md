# acpctl Examples

This directory contains example templates for using acpctl workflows.

## Using Custom Templates

### Option 1: Environment Variable

Set the `ACPCTL_TEMPLATE_DIR` environment variable to point to your templates directory:

```bash
export ACPCTL_TEMPLATE_DIR=/path/to/your/templates
acpctl specify "your feature description"
```

### Option 2: Project-Local Templates

Create a `.acpctl/templates/` directory in your project:

```bash
mkdir -p .acpctl/templates/commands
cp examples/templates/commands/* .acpctl/templates/commands/
acpctl specify "your feature description"
```

acpctl will automatically discover templates in `.acpctl/templates/` in the current directory or any parent directory.

### Option 3: User Config Directory

Install templates in your user configuration directory:

```bash
mkdir -p ~/.config/acpctl/templates/commands
cp examples/templates/commands/* ~/.config/acpctl/templates/commands/
```

## Template Discovery Priority

acpctl searches for templates in this order:

1. `ACPCTL_TEMPLATE_DIR` environment variable
2. `.acpctl/templates/` in current directory or parents
3. `~/.config/acpctl/templates/` (user config directory)
4. `examples/templates/` (included examples)

## Template Format

Templates are markdown files with optional YAML front-matter:

```markdown
---
description: Brief description of what this workflow does
scripts:
  sh: path/to/setup-script.sh
  ps: path/to/setup-script.ps1
---

## User Input

\```text
$ARGUMENTS
\```

Your prompt text here...
```

### Front-Matter Fields

- `description`: Brief description shown in help text
- `scripts`: Optional setup scripts to run before the workflow
  - `sh`: Bash script for Unix-like systems
  - `ps`: PowerShell script for Windows
- `agent_scripts`: Optional agent-specific scripts

### Template Variables

- `$ARGUMENTS`: User-provided arguments to the command

## Example Templates

This directory includes minimal example templates for:

- `specify.md` - Create feature specifications
- `plan.md` - Generate implementation plans
- `tasks.md` - Break down features into actionable tasks

These examples don't require external scripts and work standalone with acpctl.

## Creating Custom Templates

To create your own templates:

1. Create a markdown file in `templates/commands/`
2. Add YAML front-matter if needed (optional)
3. Write your prompt using `$ARGUMENTS` for user input
4. Use the template with `acpctl <command-name> "arguments"`

Example:

```bash
# Create custom template
cat > .acpctl/templates/commands/review.md << 'EOF'
---
description: Review code for quality and best practices
---

## Code to Review

\```text
$ARGUMENTS
\```

## Task

Review the code above and provide feedback on:
1. Code quality and style
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Best practice recommendations
EOF

# Use it
acpctl review "path/to/code.py"
```
