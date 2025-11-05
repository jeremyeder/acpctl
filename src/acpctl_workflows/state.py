"""Shared state definitions for LangGraph workflows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage

from .scripts import ScriptResult
from .templates import SlashCommandTemplate


class SlashCommandState(TypedDict, total=False):
    """State tracked throughout a slash command workflow."""

    command: str
    arguments: str
    template: SlashCommandTemplate
    script_result: Optional[ScriptResult]
    context: Dict[str, Any]
    messages: List[BaseMessage]
    response: Any
    metadata: Dict[str, Any]

