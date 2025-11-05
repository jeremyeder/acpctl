"""Configuration management for acpctl workflows."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def get_template_dir(override: Optional[Path] = None) -> Path:
    """Get template directory with override support.

    Priority order:
    1. Provided override parameter
    2. ACPCTL_TEMPLATE_DIR environment variable
    3. .acpctl/templates/ in current directory or parents
    4. ~/.config/acpctl/templates/ (user config directory)
    5. Fallback to included examples

    Parameters
    ----------
    override:
        Explicit template directory path

    Returns
    -------
    Path
        Resolved template directory path
    """

    # 1. Explicit override
    if override:
        return override

    # 2. Environment variable
    if env_dir := os.getenv("ACPCTL_TEMPLATE_DIR"):
        return Path(env_dir)

    # 3. Project-local .acpctl/templates/
    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        acpctl_templates = candidate / ".acpctl" / "templates"
        if acpctl_templates.exists() and acpctl_templates.is_dir():
            return acpctl_templates

    # 4. User config directory
    try:
        from platformdirs import user_config_dir

        user_templates = Path(user_config_dir("acpctl")) / "templates"
        if user_templates.exists():
            return user_templates
    except ImportError:
        # platformdirs not available, skip this option
        pass

    # 5. Fallback to package examples
    package_dir = Path(__file__).resolve().parent.parent.parent
    examples_dir = package_dir / "examples" / "templates"
    if examples_dir.exists():
        return examples_dir

    # Last resort: templates in current repo root
    base_dir = Path(__file__).resolve().parents[2]
    return base_dir / "templates"


def get_script_dir(template_dir: Path) -> Path:
    """Get script directory relative to templates.

    Parameters
    ----------
    template_dir:
        Template directory path

    Returns
    -------
    Path
        Script directory (defaults to template_dir/../scripts)
    """

    return template_dir.parent / "scripts"
