#!/usr/bin/env python3
"""
Mock acpctl CLI for asciinema demo
Simulates the UX without implementing actual LangGraph agents
"""

import sys
import time
import argparse
from typing import Optional

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"

# Emoji/symbols
CHECK = "✅"
CROSS = "❌"
GEAR = "⚙️ "
QUESTION = "❓"
SAVE = "💾"
SPARKLES = "✨"
PLAY = "▶️ "
SKIP = "⏭️ "
PAUSE = "⏸️ "
CLOCK = "⏳"

# Global verbosity level
verbosity = "moderate"  # quiet, moderate, verbose


def print_slow(text: str, delay: float = 0.01):
    """Print text with typing effect"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def print_instant(text: str):
    """Print text instantly"""
    print(text)


def spinner(duration: float, message: str):
    """Show a spinner for duration seconds"""
    if verbosity == "quiet":
        return

    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r{BLUE}{frames[i % len(frames)]}{RESET} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")
    sys.stdout.flush()


def box(title: str, width: int = 60):
    """Print a box header"""
    print()
    print("╔" + "═" * (width - 2) + "╗")
    print(f"║ {BOLD}{title}{RESET}" + " " * (width - 4 - len(title)) + "║")
    print("╚" + "═" * (width - 2) + "╝")
    print()


def cmd_init(args):
    """Simulate acpctl init"""
    box("acpctl - Ambient Code Platform Initialization")

    time.sleep(0.5)
    print_instant(f"{GEAR}Creating .acp/ directory structure...")
    time.sleep(0.3)

    if verbosity != "quiet":
        print_instant(f"   {DIM}├─ .acp/templates/{RESET}")
        print_instant(f"   {DIM}├─ .acp/state/{RESET}")
        print_instant(f"   {DIM}└─ .acp/memory/{RESET}")

    time.sleep(0.3)
    print_instant(f"{CHECK} Directory structure created")
    print()

    time.sleep(0.5)
    print_instant(f"{GEAR}Generating constitution template...")
    time.sleep(0.4)
    print_instant(f"{CHECK} Constitution template created: {CYAN}.acp/templates/constitution.md{RESET}")
    print()

    time.sleep(0.3)
    print_instant(f"{SPARKLES} Project initialized!")
    print_instant(f"   Next: {BOLD}acpctl specify \"<feature description>\"{RESET}")
    print()


def cmd_specify(args):
    """Simulate acpctl specify with pre-flight questionnaire"""
    description = " ".join(args.description) if args.description else "Add OAuth2 authentication to REST API"

    box("acpctl - Ambient Code Platform Workflow")
    print_instant("Pre-Flight Questionnaire")
    print()

    time.sleep(0.5)
    print_instant(f"{BLUE}📋 The Specification Agent has identified 4 clarifications needed{RESET}")
    print_instant("   before generating the spec. Please answer all questions now:")
    print()
    time.sleep(0.8)

    # Question 1
    print("┌" + "─" * 58 + "┐")
    print(f"│ {BOLD}Question 1/4: Authentication{RESET}" + " " * 27 + "│")
    print("├" + "─" * 58 + "┤")
    print("│ Which OAuth2 flow should be implemented?" + " " * 17 + "│")
    print("│" + " " * 58 + "│")
    print("│  1. Authorization Code (recommended for web apps)" + " " * 8 + "│")
    print("│  2. Client Credentials (server-to-server)" + " " * 15 + "│")
    print("│  3. Resource Owner Password (legacy, not recommended)│")
    print("│  4. Device Code (for CLI/IoT devices)" + " " * 19 + "│")
    print("│" + " " * 58 + "│")
    print("│ [1-4, or 'skip' to defer]: 1" + " " * 28 + "│")
    print("└" + "─" * 58 + "┘")
    print()
    time.sleep(1.0)
    print_instant(f"{CHECK} Saved: authorization_code flow")
    print()
    time.sleep(0.5)

    # Question 2
    print("┌" + "─" * 58 + "┐")
    print(f"│ {BOLD}Question 2/4: Token Management{RESET}" + " " * 25 + "│")
    print("├" + "─" * 58 + "┤")
    print("│ Token storage mechanism?" + " " * 33 + "│")
    print("│" + " " * 58 + "│")
    print("│  1. httpOnly cookies (most secure for web)" + " " * 14 + "│")
    print("│  2. localStorage (convenient but XSS vulnerable)" + " " * 7 + "│")
    print("│  3. In-memory only (secure but no persistence)" + " " * 10 + "│")
    print("│  4. Custom secure storage implementation" + " " * 17 + "│")
    print("│" + " " * 58 + "│")
    print("│ [1-4, or 'skip' to defer]: 1" + " " * 28 + "│")
    print("└" + "─" * 58 + "┘")
    print()
    time.sleep(1.0)
    print_instant(f"{CHECK} Saved: httpOnly cookies")
    print()
    time.sleep(0.5)

    # Question 3
    print("┌" + "─" * 58 + "┐")
    print(f"│ {BOLD}Question 3/4: Token Lifecycle{RESET}" + " " * 26 + "│")
    print("├" + "─" * 58 + "┤")
    print("│ Access token expiration policy?" + " " * 26 + "│")
    print("│" + " " * 58 + "│")
    print("│  1. Short-lived (15 min access, 7 day refresh)" + " " * 10 + "│")
    print("│  2. Long-lived (24 hr access, 30 day refresh)" + " " * 11 + "│")
    print("│  3. OWASP recommended (varies by risk profile)" + " " * 11 + "│")
    print("│  4. Custom durations (will prompt for values)" + " " * 11 + "│")
    print("│" + " " * 58 + "│")
    print("│ [1-4, or 'skip' to defer]: 3" + " " * 28 + "│")
    print("└" + "─" * 58 + "┘")
    print()
    time.sleep(1.0)
    print_instant(f"{CHECK} Saved: OWASP recommended policy")
    print()
    time.sleep(0.5)

    # Question 4
    print("┌" + "─" * 58 + "┐")
    print(f"│ {BOLD}Question 4/4: Security Enhancements{RESET}" + " " * 19 + "│")
    print("├" + "─" * 58 + "┤")
    print("│ Multi-factor authentication (MFA) support?" + " " * 15 + "│")
    print("│" + " " * 58 + "│")
    print("│  1. Required for all users" + " " * 30 + "│")
    print("│  2. Optional, user-configurable" + " " * 25 + "│")
    print("│  3. Admin-enforced based on role" + " " * 24 + "│")
    print("│  4. Not in initial implementation" + " " * 23 + "│")
    print("│" + " " * 58 + "│")
    print("│ [1-4, or 'skip' to defer]: 1" + " " * 28 + "│")
    print("└" + "─" * 58 + "┘")
    print()
    time.sleep(1.0)
    print_instant(f"{CHECK} Saved: MFA required")
    print()
    time.sleep(0.5)

    box("Pre-flight complete! Starting workflow...")
    time.sleep(0.5)

    # Governance check
    print_instant(f"{GEAR}Governance Agent: Validating against constitution...")
    spinner(1.5, "Checking constitutional compliance...")
    print_instant(f"{CHECK} Constitutional check passed")
    print()
    time.sleep(0.3)

    # Specification generation
    print_instant(f"{GEAR}Specification Agent: Generating spec with your answers...")
    spinner(2.0, "Analyzing requirements and generating specification...")
    print_instant(f"{CHECK} Specification complete: {CYAN}specs/001-oauth2-auth/spec.md{RESET}")
    print()
    time.sleep(0.3)

    # Re-validation
    print_instant(f"{GEAR}Governance Agent: Re-validating spec...")
    spinner(1.0, "Validating specification against principles...")
    print_instant(f"{CHECK} Spec approved")
    print()
    time.sleep(0.3)

    # Checkpoint
    print_instant(f"{SAVE} Checkpoint saved: {BOLD}SPECIFICATION_COMPLETE{RESET}")
    print()
    time.sleep(0.3)

    print_instant(f"{SPARKLES} Specification phase complete!")
    print_instant(f"   Next: {BOLD}acpctl plan{RESET}")
    print()


def cmd_plan(args):
    """Simulate acpctl plan"""
    if verbosity == "verbose":
        cmd_plan_verbose()
    elif verbosity == "quiet":
        cmd_plan_quiet()
    else:
        cmd_plan_moderate()


def cmd_plan_moderate():
    """Default verbosity plan"""
    print()
    print_instant(f"{GEAR}Architect Agent: Analyzing specification...")
    spinner(1.5, "Analyzing specification...")
    print_instant(f"{CHECK} Analysis complete")
    print()

    time.sleep(0.3)
    print_instant(f"{GEAR}Architect Agent: Designing system architecture...")

    if verbosity == "moderate":
        time.sleep(0.5)
        print_instant(f"    {DIM}├─ Token flow design: complete{RESET}")
        time.sleep(0.5)
        print_instant(f"    {DIM}├─ Data model design: complete{RESET}")
        time.sleep(0.5)
        print_instant(f"    {DIM}└─ API contracts: in progress...{RESET}")
        spinner(1.0, "Generating API contracts...")

    print_instant(f"{CHECK} Architecture design complete")
    print()

    time.sleep(0.3)
    print_instant(f"{GEAR}Architect Agent: Generating plan document...")
    spinner(1.0, "Writing plan document...")
    print_instant(f"{CHECK} Plan generated: {CYAN}specs/001-oauth2-auth/plan.md{RESET}")
    print()

    time.sleep(0.3)
    print_instant(f"{SAVE} Checkpoint saved: {BOLD}PLANNING_COMPLETE{RESET}")
    print()

    time.sleep(0.3)
    print_instant(f"{SPARKLES} Planning phase complete!")
    print_instant(f"   Next: {BOLD}acpctl implement{RESET}")
    print()


def cmd_plan_quiet():
    """Quiet mode plan"""
    time.sleep(2.0)
    print()
    print_instant(f"{CHECK} Plan complete: {CYAN}specs/001-oauth2-auth/plan.md{RESET}")
    print_instant(f"   Next: {BOLD}acpctl implement{RESET}")
    print()


def cmd_plan_verbose():
    """Verbose mode plan"""
    print()
    print_instant(f"{GEAR}Architect Agent: Analyzing specification...")
    print_instant(f"    {DIM}📖 Reading spec from: specs/001-oauth2-auth/spec.md{RESET}")
    time.sleep(0.5)
    print_instant(f"    {DIM}🧠 Agent reasoning:{RESET}")
    print_instant(f'{DIM}       "The spec requires OAuth2 authorization code flow with{RESET}')
    print_instant(f'{DIM}        MFA support. Key architectural decisions needed:{RESET}')
    print_instant(f'{DIM}        1. Token service architecture{RESET}')
    print_instant(f'{DIM}        2. Session management approach{RESET}')
    print_instant(f'{DIM}        3. MFA provider integration point{RESET}')
    print_instant(f'{DIM}        4. Token refresh mechanism{RESET}')
    print_instant(f'{DIM}        ..."{RESET}')
    time.sleep(1.0)
    print()
    print_instant(f"    {CHECK} Identified 3 core services needed")
    print_instant(f"    {CHECK} Identified 2 external dependencies (OAuth2 provider, MFA provider)")
    print_instant(f"    {CHECK} Identified 4 data models (User, Session, Token, MFAChallenge)")
    print()

    time.sleep(0.5)
    print_instant(f"{CHECK} Analysis complete (took 2.3s)")
    print()

    time.sleep(0.5)
    print_instant(f"{GEAR}Architect Agent: Designing system architecture...")
    print_instant(f"    {DIM}🏗️  Phase 1: Token flow design{RESET}")
    time.sleep(0.3)
    print_instant(f"       {DIM}├─ Authorization endpoint: /oauth/authorize{RESET}")
    print_instant(f"       {DIM}├─ Token endpoint: /oauth/token{RESET}")
    print_instant(f"       {DIM}├─ Refresh endpoint: /oauth/refresh{RESET}")
    print_instant(f"       {DIM}└─ Revocation endpoint: /oauth/revoke{RESET}")
    time.sleep(0.5)
    print_instant(f"    {CHECK} Token flow design complete")
    print()

    time.sleep(0.5)
    print_instant(f"    {DIM}🏗️  Phase 2: Data model design{RESET}")
    print_instant(f"       {DIM}🧠 Agent reasoning:{RESET}")
    print_instant(f'{DIM}          "Need to store:{RESET}')
    print_instant(f'{DIM}           - User credentials and profile{RESET}')
    print_instant(f'{DIM}           - Active sessions with device info{RESET}')
    print_instant(f'{DIM}           - Refresh tokens with expiry{RESET}')
    print_instant(f'{DIM}           - MFA challenges and recovery codes{RESET}')
    print_instant(f'{DIM}           ..."{RESET}')
    time.sleep(0.8)
    print_instant(f"       {DIM}├─ User model: 7 fields{RESET}")
    print_instant(f"       {DIM}├─ Session model: 9 fields{RESET}")
    print_instant(f"       {DIM}├─ Token model: 6 fields{RESET}")
    print_instant(f"       {DIM}└─ MFAChallenge model: 5 fields{RESET}")
    time.sleep(0.5)
    print_instant(f"    {CHECK} Data model design complete")
    print()

    time.sleep(0.5)
    print_instant(f"    {DIM}🏗️  Phase 3: API contracts{RESET}")
    spinner(1.0, "Generating OpenAPI spec for auth endpoints...")
    print_instant(f"       {CHECK} contracts/oauth2_api.yaml created (127 lines)")
    time.sleep(0.3)
    print_instant(f"    {CHECK} API contracts complete")
    print()

    time.sleep(0.3)
    print_instant(f"{CHECK} Architecture design complete (took 8.7s)")
    print()

    time.sleep(0.5)
    print_instant(f"{GEAR}Architect Agent: Generating plan document...")
    print_instant(f"    {DIM}📝 Writing introduction and overview...{RESET}")
    time.sleep(0.3)
    print_instant(f"    {DIM}📝 Writing architecture decisions...{RESET}")
    time.sleep(0.3)
    print_instant(f"    {DIM}📝 Writing implementation phases...{RESET}")
    time.sleep(0.3)
    print_instant(f"    {DIM}📝 Writing testing strategy...{RESET}")
    time.sleep(0.3)
    print_instant(f"    {CHECK} Plan written: 4.7 KB")
    print()

    time.sleep(0.3)
    print_instant(f"{CHECK} Plan generated: {CYAN}specs/001-oauth2-auth/plan.md{RESET}")
    print()

    time.sleep(0.5)
    print_instant(f"{GEAR}Governance Agent: Re-validating plan against constitution...")
    print_instant(f"    {DIM}🔍 Checking principle: \"All auth must use industry standards\"{RESET}")
    time.sleep(0.3)
    print_instant(f"       {CHECK} Plan specifies OAuth2 RFC 6749 compliance")
    time.sleep(0.3)
    print_instant(f"    {DIM}🔍 Checking principle: \"Security by default\"{RESET}")
    time.sleep(0.3)
    print_instant(f"       {CHECK} Plan includes MFA, secure token storage, expiry policies")
    time.sleep(0.3)
    print_instant(f"    {DIM}🔍 Checking principle: \"Red Hat approved dependencies only\"{RESET}")
    time.sleep(0.3)
    print_instant(f"       {CHECK} All dependencies from approved list")
    print()

    time.sleep(0.3)
    print_instant(f"{CHECK} Governance validation passed")
    print()

    time.sleep(0.3)
    print_instant(f"{SAVE} Checkpoint saved: {BOLD}PLANNING_COMPLETE{RESET}")
    print_instant(f"    {DIM}State file: .acp/state/001-oauth2-auth.json{RESET}")
    print_instant(f"    {DIM}Checkpoint: PLANNING_COMPLETE{RESET}")
    print_instant(f"    {DIM}Timestamp: 2025-11-04T14:32:17Z{RESET}")
    print()

    time.sleep(0.3)
    print_instant(f"{SPARKLES} Planning phase complete! (total: 11.4s)")
    print_instant(f"   Next: {BOLD}acpctl implement{RESET}")
    print()


def cmd_status(args):
    """Simulate acpctl status"""
    box("Current Workflow: 001-oauth2-auth")

    print_instant(f"{BLUE}📊 Progress:{RESET} {BOLD}PLANNING_COMPLETE{RESET} (60%)")
    print()

    time.sleep(0.3)
    print_instant(f"{BOLD}Workflow Timeline:{RESET}")
    print_instant(f"  {CHECK} Constitution validation     2m 3s    COMPLETE")
    print_instant(f"  {CHECK} Specification phase         5m 12s   COMPLETE")
    print_instant(f"  {CHECK} Planning phase             11m 23s   COMPLETE")
    print_instant(f"  {PAUSE} Implementation phase       -        PENDING")
    print_instant(f"  {PAUSE} Validation phase           -        PENDING")
    print()

    time.sleep(0.3)
    print_instant(f"{BOLD}📁 Generated Artifacts:{RESET}")
    print_instant(f"  {CHECK} specs/001-oauth2-auth/spec.md         (2.1 KB)")
    print_instant(f"  {CHECK} specs/001-oauth2-auth/plan.md         (4.7 KB)")
    print_instant(f"  {CHECK} specs/001-oauth2-auth/data-model.md   (1.8 KB)")
    print_instant(f"  {CHECK} specs/001-oauth2-auth/contracts/")
    print_instant(f"     └─ oauth2_api.yaml                    (3.2 KB)")
    print()

    time.sleep(0.3)
    print_instant(f"{BOLD}🛡️  Governance Checks:{RESET} 3/3 passed")
    print()

    time.sleep(0.3)
    print_instant(f"{SAVE} {BOLD}Last checkpoint:{RESET} PLANNING_COMPLETE")
    print_instant(f"   Saved: 5 minutes ago")
    print_instant(f"   Location: .acp/state/001-oauth2-auth.json")
    print()

    print_instant(f"Next step: {BOLD}acpctl implement{RESET}")
    print()


def cmd_resume(args):
    """Simulate acpctl resume"""
    box("Resume Workflow")

    time.sleep(0.5)
    print_instant(f"Found incomplete workflow: {CYAN}001-oauth2-auth{RESET}")
    print_instant(f"Last checkpoint: {BOLD}PLANNING_COMPLETE{RESET} (5 minutes ago)")
    print()

    time.sleep(0.3)
    print_instant(f"{BOLD}Workflow progress:{RESET}")
    print_instant(f"  {CHECK} Specification phase")
    print_instant(f"  {CHECK} Planning phase")
    print_instant(f"  {PAUSE} Implementation phase (not started)")
    print()

    time.sleep(0.5)
    print_instant(f"Resume from PLANNING_COMPLETE? [Y/n]: y")
    print()

    time.sleep(0.8)
    print_instant(f"{PLAY}Resuming workflow 001-oauth2-auth...")
    print()

    time.sleep(0.5)
    print_instant(f"{SKIP} Skipping completed phases:")
    print_instant(f"    {CHECK} Constitution validation (cached)")
    print_instant(f"    {CHECK} Specification generation (cached)")
    print_instant(f"    {CHECK} Planning generation (cached)")
    print()

    time.sleep(0.5)
    print_instant(f"{GEAR}Implementation Agent: Starting implementation...")
    print()


def cmd_implement(args):
    """Simulate acpctl implement"""
    print()
    print_instant(f"{GEAR}Implementation Agent: Starting implementation...")
    spinner(1.5, "Loading plan and preparing workspace...")
    print_instant(f"{CHECK} Plan loaded: specs/001-oauth2-auth/plan.md")
    print()

    time.sleep(0.5)
    print_instant(f"{GEAR}Implementation Agent: Generating code artifacts...")

    if verbosity == "verbose":
        print_instant(f"    {DIM}🧠 Agent reasoning:{RESET}")
        print_instant(f'{DIM}       "Plan specifies 3 core services:{RESET}')
        print_instant(f'{DIM}        1. Token management service{RESET}')
        print_instant(f'{DIM}        2. Session service{RESET}')
        print_instant(f'{DIM}        3. MFA service{RESET}')
        print_instant(f'{DIM}        Will implement TDD: tests first, then implementation"{RESET}')
        print()

    time.sleep(0.5)
    print_instant(f"    {DIM}├─ Writing tests: tests/test_token_service.py{RESET}")
    spinner(1.0, "Generating test cases...")
    print_instant(f"    {CHECK} Tests written (87 lines)")

    time.sleep(0.5)
    print_instant(f"    {DIM}├─ Implementing: src/auth/token_service.py{RESET}")
    spinner(1.5, "Implementing token service...")
    print_instant(f"    {CHECK} Implementation complete (142 lines)")

    time.sleep(0.5)
    print_instant(f"    {DIM}├─ Writing tests: tests/test_session_service.py{RESET}")
    spinner(0.8, "Generating test cases...")
    print_instant(f"    {CHECK} Tests written (64 lines)")

    time.sleep(0.5)
    print_instant(f"    {DIM}└─ Implementing: src/auth/session_service.py{RESET}")
    spinner(1.2, "Implementing session service...")
    print_instant(f"    {CHECK} Implementation complete (98 lines)")
    print()

    time.sleep(0.5)
    print_instant(f"{CHECK} Code generation complete")
    print()

    time.sleep(0.3)
    print_instant(f"{SAVE} Checkpoint saved: {BOLD}IMPLEMENTATION_COMPLETE{RESET}")
    print()

    time.sleep(0.3)
    print_instant(f"{SPARKLES} Implementation phase complete!")
    print_instant(f"   Generated:")
    print_instant(f"   • src/auth/token_service.py")
    print_instant(f"   • src/auth/session_service.py")
    print_instant(f"   • tests/test_token_service.py")
    print_instant(f"   • tests/test_session_service.py")
    print()


def cmd_history(args):
    """Simulate acpctl history"""
    print()
    print_instant(f"{BOLD}Workflow History:{RESET}")
    print("┌─────┬───────────────────┬──────────────────────┬──────────────┬──────────┐")
    print("│ ID  │ Description       │ Last Checkpoint      │ Status       │ Duration │")
    print("├─────┼───────────────────┼──────────────────────┼──────────────┼──────────┤")
    print("│ 001 │ oauth2-auth       │ PLANNING_COMPLETE    │ In Progress  │ 11m 23s  │")
    print("│ 002 │ graphql-api       │ IMPLEMENTATION_DONE  │ Complete     │ 47m 12s  │")
    print("│ 003 │ rbac-system       │ SPECIFICATION_DONE   │ Failed       │ 3m 45s   │")
    print("└─────┴───────────────────┴──────────────────────┴──────────────┴──────────┘")
    print()
    print_instant(f"Use '{BOLD}acpctl resume <ID>{RESET}' to continue incomplete workflows")
    print_instant(f"Use '{BOLD}acpctl show state <ID>{RESET}' to inspect workflow state")
    print()


def main():
    global verbosity

    parser = argparse.ArgumentParser(description="acpctl - Ambient Code Platform CLI (Mock)")
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("description", nargs="*", help="Description for specify command")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Set verbosity
    if args.quiet:
        verbosity = "quiet"
    elif args.verbose:
        verbosity = "verbose"

    # Route to command
    if not args.command:
        print(f"{RED}Error: No command specified{RESET}")
        print(f"Usage: acpctl <command> [options]")
        print(f"Commands: init, specify, plan, implement, status, resume, history")
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "specify": cmd_specify,
        "plan": cmd_plan,
        "implement": cmd_implement,
        "status": cmd_status,
        "resume": cmd_resume,
        "history": cmd_history,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        print(f"{RED}Error: Unknown command '{args.command}'{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
