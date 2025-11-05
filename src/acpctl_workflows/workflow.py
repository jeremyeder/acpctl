"""Base LangGraph workflow implementation for slash commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph

from .scripts import detect_variant, run_setup_script
from .state import SlashCommandState
from .templates import SlashCommandTemplate, load_template


class SlashCommandWorkflow:
    """Base workflow builder for Spec Kit slash commands."""

    def __init__(
        self,
        command_name: Optional[str] = None,
        *,
        repo_root: Optional[Path] = None,
        default_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        resolved_command = command_name or getattr(self, "command_name", None)
        if not resolved_command:
            raise ValueError("SlashCommandWorkflow requires a command name.")

        self.command_name = resolved_command
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.default_context = default_context or {}

    # ------------------------------------------------------------------
    # Hooks for subclasses
    # ------------------------------------------------------------------
    def prepare_context(self, state: SlashCommandState) -> Dict[str, Any]:
        """Populate workflow context before prompt construction."""

        return {}

    def build_messages(self, state: SlashCommandState) -> List[Any]:
        """Construct the message sequence for the LLM call."""

        template: SlashCommandTemplate = state["template"]
        arguments: str = state.get("arguments", "")
        script_ctx = state.get("script_result")
        context = state.get("context", {})

        system_parts: List[str] = [template.body]
        if script_ctx and script_ctx.data:
            system_parts.append("\n[setup]\n" + json.dumps(script_ctx.data, indent=2))
        if context:
            system_parts.append("\n[context]\n" + json.dumps(context, indent=2))

        system_message = SystemMessage(content="\n\n".join(system_parts))
        messages: List[Any] = [system_message]

        if arguments:
            messages.append(HumanMessage(content=arguments))

        return messages

    def postprocess(self, state: SlashCommandState, response: Any) -> Dict[str, Any]:
        """Hook allowing subclasses to update state after model invocation."""

        return {"response": response}

    # ------------------------------------------------------------------
    # Graph compilation
    # ------------------------------------------------------------------
    def compile(
        self,
        model: Runnable,
        *,
        agent: Optional[str] = None,
        run_scripts: bool = True,
        variant: Optional[str] = None,
    ):
        """Compile the workflow into a LangGraph executable."""

        graph = StateGraph(SlashCommandState)

        def load_node(state: SlashCommandState):
            # Only pass repo_root if it contains a templates directory
            # Otherwise, use template discovery (env var, .acpctl, etc.)
            template_override = None
            if self.repo_root:
                templates_dir = self.repo_root / "templates"
                if templates_dir.exists():
                    template_override = self.repo_root

            template = load_template(self.command_name, template_override)
            context = dict(self.default_context)
            context.update(state.get("context", {}))
            return {
                "command": self.command_name,
                "template": template,
                "context": context,
            }

        def script_node(state: SlashCommandState):
            if not run_scripts:
                return {}
            template: SlashCommandTemplate = state["template"]
            args = state.get("arguments", "")
            chosen_variant = variant or detect_variant()
            result = run_setup_script(
                template,
                args=args,
                agent=agent,
                variant=chosen_variant,
                cwd=self.repo_root,
            )
            return {"script_result": result} if result else {}

        def context_node(state: SlashCommandState):
            extra_context = self.prepare_context(state)
            if not extra_context:
                return {}
            merged = dict(state.get("context", {}))
            merged.update(extra_context)
            return {"context": merged}

        def message_node(state: SlashCommandState):
            messages = self.build_messages(state)
            return {"messages": messages}

        def model_node(state: SlashCommandState):
            messages = state.get("messages")
            response = model.invoke(messages)
            return self.postprocess(state, response)

        graph.add_node("load_template", load_node)
        graph.add_node("run_script", script_node)
        graph.add_node("prepare_context", context_node)
        graph.add_node("build_messages", message_node)
        graph.add_node("call_model", model_node)

        graph.set_entry_point("load_template")
        graph.add_edge("load_template", "run_script")
        graph.add_edge("run_script", "prepare_context")
        graph.add_edge("prepare_context", "build_messages")
        graph.add_edge("build_messages", "call_model")
        graph.add_edge("call_model", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def initial_state(
        self,
        *,
        arguments: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SlashCommandState:
        """Create a base state dictionary for workflow invocation."""

        state: SlashCommandState = {
            "command": self.command_name,
            "arguments": arguments,
            "context": dict(self.default_context),
        }
        if metadata:
            state["metadata"] = metadata
        if context:
            state_context = dict(state.get("context", {}))
            state_context.update(context)
            state["context"] = state_context
        return state
