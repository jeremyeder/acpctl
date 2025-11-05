"""Utilities for loading Spec Kit slash command templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .config import get_template_dir


@dataclass(slots=True)
class SlashCommandTemplate:
    """Represents a slash command template and its metadata."""

    name: str
    path: Path
    description: str
    body: str
    scripts: Dict[str, str] = field(default_factory=dict)
    agent_scripts: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_script(self, variant: str) -> Optional[str]:
        """Return the command script for the given variant (e.g. ``sh`` or ``ps``)."""

        return self.scripts.get(variant)

    def get_agent_script(self, variant: str) -> Optional[str]:
        """Return the agent-specific script command for the given variant."""

        return self.agent_scripts.get(variant)


def _split_front_matter(content: str) -> tuple[Optional[str], str]:
    """Split a markdown file into optional front matter and body."""

    if not content.startswith("---\n"):
        return None, content

    end_index = content.find("\n---\n", 4)
    if end_index == -1:
        raise ValueError("Malformed front matter: closing delimiter not found.")

    front_matter = content[4:end_index]
    body = content[end_index + 5 :]
    return front_matter, body


def load_template(command_name: str, root: Path | None = None) -> SlashCommandTemplate:
    """Load a slash command template by name.

    Parameters
    ----------
    command_name:
        Name of the slash command (e.g. ``"specify"``).
    root:
        Optional repository root or template directory override.
        If provided, templates are loaded from root/templates/commands/.
        Otherwise, uses get_template_dir() to discover templates.
    """

    if root is not None:
        # Legacy behavior: root points to repo root containing templates/commands/
        template_base = root / "templates"
    else:
        # New behavior: discover template directory
        template_base = get_template_dir()

    template_path = template_base / "commands" / f"{command_name}.md"
    if not template_path.is_file():
        raise FileNotFoundError(f"Unknown slash command template: {template_path}")

    text = template_path.read_text(encoding="utf-8")
    front_matter_text, body = _split_front_matter(text)

    metadata: Dict[str, Any]
    if front_matter_text is None:
        metadata = {}
    else:
        metadata = yaml.safe_load(front_matter_text) or {}

    description = metadata.get("description", "")
    scripts = metadata.get("scripts", {}) or {}
    agent_scripts = metadata.get("agent_scripts", {}) or {}

    return SlashCommandTemplate(
        name=command_name,
        path=template_path,
        description=description,
        body=body.strip(),
        scripts=scripts,
        agent_scripts=agent_scripts,
        metadata={k: v for k, v in metadata.items() if k not in {"description", "scripts", "agent_scripts"}},
    )

