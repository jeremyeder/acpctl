#!/bin/bash
# Demo script for recording acpctl UX with asciinema
# This simulates a complete workflow from init to implementation

ACPCTL="./demo/mock-acpctl.py"

# Helper function to simulate typing
type_command() {
    local cmd="$1"
    local delay="${2:-0.05}"

    echo -n "$ "
    for ((i=0; i<${#cmd}; i++)); do
        echo -n "${cmd:$i:1}"
        sleep "$delay"
    done
    echo
}

# Helper function for pauses
pause() {
    sleep "${1:-1.0}"
}

# Clear screen and start
clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  acpctl Demo - Ambient Code Platform Workflow           ║"
echo "║  Spec-Kit → LangGraph Agent System                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo
pause 2

# 1. Initialize project
echo "# Step 1: Initialize a new project"
pause 1
type_command "acpctl init"
pause 0.5
$ACPCTL init
pause 3

# 2. Specify feature with pre-flight questionnaire
echo "# Step 2: Specify a new feature (with pre-flight questionnaire)"
pause 1
type_command "acpctl specify \"Add OAuth2 authentication to REST API\""
pause 0.5
$ACPCTL specify "Add OAuth2 authentication to REST API"
pause 3

# 3. Check status
echo "# Step 3: Check workflow status"
pause 1
type_command "acpctl status"
pause 0.5
$ACPCTL status
pause 3

# 4. Generate plan
echo "# Step 4: Generate architecture plan"
pause 1
type_command "acpctl plan"
pause 0.5
$ACPCTL plan
pause 3

# 5. Show interruption scenario
echo "# Step 5: Simulating workflow interruption..."
pause 1
echo "(Imagine Ctrl+C was pressed here)"
pause 2

# 6. Resume workflow
echo "# Step 6: Resume from checkpoint"
pause 1
type_command "acpctl resume"
pause 0.5
$ACPCTL resume
pause 3

# 7. Implement with verbose mode
echo "# Step 7: Implementation phase (verbose mode)"
pause 1
type_command "acpctl implement --verbose"
pause 0.5
$ACPCTL implement --verbose
pause 3

# 8. Final status
echo "# Step 8: Final workflow status"
pause 1
type_command "acpctl status"
pause 0.5
$ACPCTL status
pause 3

# 9. Show workflow history
echo "# Step 9: View all workflow history"
pause 1
type_command "acpctl history"
pause 0.5
$ACPCTL history
pause 3

# End
echo
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Demo Complete!                                          ║"
echo "║                                                          ║"
echo "║  Key Features Demonstrated:                              ║"
echo "║  ✅ Pre-flight questionnaire (no interruptions)          ║"
echo "║  ✅ Constitutional governance gates                      ║"
echo "║  ✅ Automatic checkpointing                              ║"
echo "║  ✅ Resume from checkpoint                               ║"
echo "║  ✅ Configurable verbosity (--quiet/--verbose)           ║"
echo "║  ✅ Complete audit trail                                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo
pause 3
