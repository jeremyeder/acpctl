# acpctl UX Demo

This directory contains an asciinema recording demonstrating the proposed UX for **acpctl** (Ambient Code Platform CLI), the Phase 1 implementation of the spec-kit → LangGraph workflow system.

## 🎬 Watch the Demo

**Live recording**: https://asciinema.org/a/OWR3Vroa0ie2pytj9HHY5qNWi

[![asciicast](https://asciinema.org/a/OWR3Vroa0ie2pytj9HHY5qNWi.svg)](https://asciinema.org/a/OWR3Vroa0ie2pytj9HHY5qNWi)

## 📁 Contents

- **`mock-acpctl.py`** - Mock CLI implementation that simulates all acpctl commands without implementing actual LangGraph agents
- **`record-demo.sh`** - Automated script that runs through a complete workflow demonstration
- **`acpctl-demo.cast`** - Recorded asciinema session (playable recording)
- **`README.md`** - This file

## 🎬 Viewing the Demo

### Option 1: Play in Terminal (Recommended)

```bash
asciinema play demo/acpctl-demo.cast
```

Press `Space` to pause/resume, `q` to quit.

### Option 2: View on asciinema.org

View the uploaded recording at: https://asciinema.org/a/OWR3Vroa0ie2pytj9HHY5qNWi

To upload a new version:

```bash
asciinema upload demo/acpctl-demo.cast
```

### Option 3: Convert to GIF

```bash
# Install agg (asciinema GIF generator)
brew install agg

# Convert to GIF
agg demo/acpctl-demo.cast demo/acpctl-demo.gif
```

### Option 4: Embed in Markdown

For GitHub/GitLab markdown:

```markdown
[![asciicast](https://asciinema.org/a/OWR3Vroa0ie2pytj9HHY5qNWi.svg)](https://asciinema.org/a/OWR3Vroa0ie2pytj9HHY5qNWi)
```

## 🎯 What the Demo Shows

The recording demonstrates a complete acpctl workflow:

1. **`acpctl init`** - Initialize project with constitution template
2. **`acpctl specify`** - Generate specification with pre-flight questionnaire (4 questions)
3. **`acpctl status`** - View current workflow progress
4. **`acpctl plan`** - Generate architecture plan with moderate verbosity
5. **Interruption simulation** - Shows checkpoint/resume capability
6. **`acpctl resume`** - Resume from last checkpoint
7. **`acpctl implement --verbose`** - Implementation with full agent reasoning
8. **`acpctl status`** - Final workflow state
9. **`acpctl history`** - View all workflows

### Key UX Features Demonstrated

- ✅ **Pre-flight questionnaire** - All clarifications collected upfront (no workflow interruptions)
- ✅ **Constitutional governance** - Validation gates at each phase boundary
- ✅ **Automatic checkpointing** - State saved after each phase completion
- ✅ **Resume from checkpoint** - Workflow can be interrupted and resumed
- ✅ **Configurable verbosity** - `--quiet`, default (moderate), `--verbose` modes
- ✅ **Progress visibility** - Real-time phase transitions and sub-task tracking
- ✅ **Complete audit trail** - Full workflow history and state inspection

## 🔧 Testing the Mock CLI

You can manually test individual commands:

```bash
# Initialize
./demo/mock-acpctl.py init

# Specify (with pre-flight questionnaire)
./demo/mock-acpctl.py specify "Add OAuth2 authentication"

# Plan with different verbosity
./demo/mock-acpctl.py plan
./demo/mock-acpctl.py plan --quiet
./demo/mock-acpctl.py plan --verbose

# Implementation
./demo/mock-acpctl.py implement
./demo/mock-acpctl.py implement --verbose

# State management
./demo/mock-acpctl.py status
./demo/mock-acpctl.py resume
./demo/mock-acpctl.py history
```

## 🎥 Re-recording the Demo

If you want to modify and re-record:

```bash
# Edit the demo script
vim demo/record-demo.sh

# Or edit the mock CLI
vim demo/mock-acpctl.py

# Re-record
asciinema rec demo/acpctl-demo.cast -c "./demo/record-demo.sh" --overwrite
```

### Recording Tips

- Set terminal to 80x24 or similar standard size for best compatibility
- Use `--idle-time-limit 2` to cap maximum pause time in recording
- Use `--title "acpctl Demo"` to set a title for asciinema.org

Example with options:

```bash
asciinema rec demo/acpctl-demo.cast \
  -c "./demo/record-demo.sh" \
  --overwrite \
  --idle-time-limit 2 \
  --title "acpctl - Ambient Code Platform CLI Demo"
```

## 🏗️ Implementation Status

**Current Status**: UX Demo Only (Mock)

This demo shows the **proposed UX** for Phase 1. The actual implementation with LangGraph agents, state management, and constitutional governance is not yet built.

### Next Steps

1. ✅ UX design and demo (this)
2. ⏸️ Implement `ACPState` schema and persistence
3. ⏸️ Build LangGraph StateGraph workflow
4. ⏸️ Implement core agents (Governance, Specification, Architect, Implementation)
5. ⏸️ Build CLI framework with all commands
6. ⏸️ Add pre-flight questionnaire system
7. ⏸️ Implement checkpoint/resume logic

## 📋 Demo Scenario Details

The demo uses a realistic scenario: **"Add OAuth2 authentication to REST API"**

### Pre-flight Questions

The demo answers these clarifications upfront:

1. **OAuth2 Flow**: Authorization Code (recommended for web apps)
2. **Token Storage**: httpOnly cookies (most secure for web)
3. **Token Expiration**: OWASP recommended policy
4. **MFA Support**: Required for all users

### Generated Artifacts (Simulated)

```
specs/001-oauth2-auth/
├── spec.md              # Functional specification
├── plan.md              # Architecture plan
├── data-model.md        # Database schema
└── contracts/
    └── oauth2_api.yaml  # API contracts
```

## 🎨 UX Design Principles

The demo showcases these design decisions:

1. **spec-kit Familiarity** - Command structure mirrors original spec-kit
2. **Pre-flight Questionnaire** - No workflow interruptions
3. **Smart Defaults** - Moderate verbosity by default
4. **Checkpoint Everything** - Automatic state persistence
5. **Resume Anywhere** - Never lose work
6. **Progressive Disclosure** - Verbosity levels for different needs

## 📚 References

- [Original Architecture Document](../speckit-langgraph-architecture.md)
- [GitHub spec-kit Repository](https://github.com/github/spec-kit)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [asciinema Documentation](https://docs.asciinema.org/)

---

**Created**: 2025-11-04
**Purpose**: UX demonstration for Phase 1 acpctl implementation
