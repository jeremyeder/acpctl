"""Helpers for executing slash command setup scripts."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .templates import SlashCommandTemplate


@dataclass(slots=True)
class ScriptResult:
    """Container for executed script output."""

    command: str
    stdout: str
    stderr: str
    data: Optional[Dict[str, Any]] = None

    @property
    def has_data(self) -> bool:
        return self.data is not None


def detect_variant() -> str:
    """Return the default script variant for the current platform."""

    if sys.platform.startswith("win"):
        return "ps"
    return "sh"


def _render_placeholders(command: str, args: str, agent: Optional[str]) -> str:
    """Render placeholder tokens used in template scripts."""

    rendered = command
    args_value = args or ""

    # Replace quoted {ARGS} first to preserve quoting semantics
    rendered = rendered.replace('"{ARGS}"', shlex.quote(args_value))
    rendered = rendered.replace("{ARGS}", shlex.quote(args_value))

    if agent is not None:
        rendered = rendered.replace("__AGENT__", agent)

    return rendered


def _split_command(command: str) -> list[str]:
    return shlex.split(command)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Attempt to parse a JSON object from mixed stdout text."""

    stripped = text.strip()
    if not stripped:
        return None

    segments = [line.strip() for line in stripped.splitlines() if line.strip()]
    for segment in reversed(segments):
        if segment.startswith("{") or segment.startswith("["):
            try:
                parsed = json.loads(segment)
            except json.JSONDecodeError:
                continue
            else:
                if isinstance(parsed, dict):
                    return parsed
    return None


def run_setup_script(
    template: SlashCommandTemplate,
    *,
    args: str = "",
    agent: Optional[str] = None,
    variant: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> Optional[ScriptResult]:
    """Execute the setup script defined by a slash command template.

    Returns ``None`` when the template does not declare a script for the chosen variant.
    """

    cwd = cwd or Path.cwd()
    script_variant = variant or detect_variant()
    script_command = template.get_script(script_variant)
    if script_command is None:
        return None

    rendered_command = _render_placeholders(script_command, args, agent)
    command_list = _split_command(rendered_command)

    process = subprocess.run(
        command_list,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        env=dict(os.environ),
    )

    stdout = process.stdout.strip()
    stderr = process.stderr.strip()
    data: Optional[Dict[str, Any]] = None

    if process.returncode != 0:
        raise RuntimeError(
            f"Setup script failed for command '{template.name}': {rendered_command}\n"
            f"Exit code: {process.returncode}\nSTDOUT: {stdout}\nSTDERR: {stderr}"
        )

    if stdout:
        data = _extract_json(stdout)

    return ScriptResult(command=rendered_command, stdout=stdout, stderr=stderr, data=data)
