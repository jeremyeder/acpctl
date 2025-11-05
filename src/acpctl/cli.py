"""acpctl - Ambient Code Platform control CLI for spec-driven development."""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import click
import typer
import yaml
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable, RunnableLambda

from acpctl_workflows import (
    AnalyzeWorkflow,
    ChecklistWorkflow,
    ClarifyWorkflow,
    ConstitutionWorkflow,
    ImplementWorkflow,
    PlanWorkflow,
    ScriptResult,
    SlashCommandWorkflow,
    SpecifyWorkflow,
    TasksWorkflow,
)

MODEL_FACTORY_ENV = "ACPCTL_MODEL_FACTORY"

app = typer.Typer(help="Ambient Code Platform control - LangGraph workflow CLI for spec-driven development")


def _load_factory(factory_path: str) -> Callable[[], Runnable]:
    module_path, _, attribute = factory_path.partition(":")
    if not module_path or not attribute:
        raise typer.BadParameter(
            "Model factory must be in the form 'module.submodule:callable'."
        )

    module = importlib.import_module(module_path)
    factory: Callable[[], Runnable] = getattr(module, attribute)
    return factory


def _default_model() -> Runnable:
    def responder(messages):
        total_tokens = sum(len(getattr(message, "content", "")) for message in messages)
        return {
            "message": (
                "No model factory configured. Provide --model-factory module:function"
                " to connect an AI model."
            ),
            "messages_count": len(messages),
            "prompt_characters": total_tokens,
        }

    return RunnableLambda(responder)


def _build_claude_model(
    model_name: str,
    temperature: float,
    max_output_tokens: Optional[int],
) -> Runnable:
    if not 0.0 <= temperature <= 1.0:
        raise typer.BadParameter("--claude-temperature must be between 0.0 and 1.0")

    if max_output_tokens is not None and max_output_tokens <= 0:
        raise typer.BadParameter("--claude-max-output-tokens must be positive")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise typer.BadParameter("ANTHROPIC_API_KEY environment variable is required for --claude-model")

    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as err:
        raise typer.BadParameter("langchain-anthropic is required to use --claude-model") from err

    kwargs = {"model": model_name, "temperature": temperature}
    if max_output_tokens is not None:
        kwargs["max_output_tokens"] = max_output_tokens
    return ChatAnthropic(**kwargs)


def _resolve_model_selection(
    model_factory: Optional[str],
    claude_model: Optional[str],
    claude_temperature: float,
    claude_max_output_tokens: Optional[int],
) -> Tuple[Optional[str], Optional[Runnable]]:
    if model_factory and claude_model:
        raise typer.BadParameter("Use either --model-factory or --claude-model, not both.")

    prebuilt_model: Optional[Runnable] = None
    if claude_model:
        prebuilt_model = _build_claude_model(
            claude_model, claude_temperature, claude_max_output_tokens
        )

    return model_factory, prebuilt_model


def _ensure_context_storage() -> Dict[str, Any]:
    ctx = click.get_current_context()
    if ctx.obj is None:
        ctx.obj = {}
    return ctx.obj  # type: ignore[return-value]


def _initialise_context(
    model_factory: Optional[str],
    prebuilt_model: Optional[Runnable] = None,
) -> Tuple[Runnable, bool]:
    storage = _ensure_context_storage()
    factory_key = "model_factory_path"
    model_key = "model_instance"

    if prebuilt_model is not None:
        storage[factory_key] = "__prebuilt__"
        storage[model_key] = prebuilt_model
        return prebuilt_model, False

    if model_factory:
        factory_path = model_factory
    else:
        factory_path = storage.get(factory_key) or os.getenv(MODEL_FACTORY_ENV)

    if factory_path:
        if storage.get(factory_key) == factory_path and model_key in storage:
            return storage[model_key], False
        model = _load_factory(factory_path)()
        storage[factory_key] = factory_path
        storage[model_key] = model
        return model, False

    if model_key in storage:
        return storage[model_key], False

    model = _default_model()
    storage[factory_key] = None
    storage[model_key] = model
    return model, True


def _maybe_coerce_path(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    return value


def _serialise(value: Any) -> Any:
    if isinstance(value, ScriptResult):
        data = asdict(value)
        data["data"] = value.data
        return data
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, BaseMessage):
        return value.content
    if isinstance(value, dict):
        return {k: _serialise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialise(item) for item in value]
    return _maybe_coerce_path(value)


def _run_workflow(
    workflow_cls: type[SlashCommandWorkflow],
    arguments: str,
    *,
    repo_root: Path,
    model_factory: Optional[str],
    agent: Optional[str],
    skip_scripts: bool,
    extra_context: Optional[Dict[str, Any]] = None,
    prebuilt_model: Optional[Runnable] = None,
) -> Dict[str, Any]:
    model, is_default_model = _initialise_context(model_factory, prebuilt_model)
    workflow = workflow_cls(repo_root=repo_root)
    effective_skip_scripts = skip_scripts or is_default_model
    graph = workflow.compile(model, agent=agent, run_scripts=not effective_skip_scripts)
    state = workflow.initial_state(arguments=arguments, context=extra_context)
    result = graph.invoke(state)

    response = result.get("response")
    payload = {
        "response": _serialise(response),
    }

    script_result = result.get("script_result")
    if script_result is not None and not is_default_model:
        payload["script"] = _serialise(script_result)

    if is_default_model:
        meta = payload.setdefault("meta", {})
        meta["scripts_skipped"] = True
        meta["reason"] = "No model factory configured"

    return payload


def _print_output(data: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    typer.echo(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def _common_options(
    args: List[str],
    *,
    workflow_cls: type[SlashCommandWorkflow],
    repo_root: Path,
    model_factory: Optional[str],
    agent: Optional[str],
    skip_scripts: bool,
    json_output: bool,
    extra_context: Optional[Dict[str, Any]] = None,
    prebuilt_model: Optional[Runnable] = None,
) -> None:
    arguments = " ".join(args)
    result = _run_workflow(
        workflow_cls,
        arguments,
        repo_root=repo_root,
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        extra_context=extra_context,
        prebuilt_model=prebuilt_model,
    )
    _print_output(result, json_output)


def _resolve_repo_root(option_value: Optional[Path]) -> Path:
    if option_value:
        return option_value.resolve()

    start = Path.cwd()
    for candidate in [start, *start.parents]:
        if (candidate / ".specify").is_dir() or (candidate / "templates").is_dir() or (
            candidate / "pyproject.toml"
        ).is_file():
            return candidate

    return start


def _normalise_arguments(arguments: Optional[List[str]]) -> List[str]:
    if not arguments:
        return []
    return arguments


@app.command()
def specify(
    arguments: Optional[List[str]] = typer.Argument(
        None, help="Feature description passed to /speckit.specify."
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        dir_okay=True,
        file_okay=False,
        help="Repository root containing the Spec Kit project (defaults to current working directory).",
    ),
    model_factory: Optional[str] = typer.Option(
        None,
        "--model-factory",
        "-m",
        help="Python callable returning a LangChain Runnable (module:callable).",
    ),
    claude_model: Optional[str] = typer.Option(
        None,
        "--claude-model",
        help="Anthropic Claude model name (requires ANTHROPIC_API_KEY).",
    ),
    claude_temperature: float = typer.Option(
        0.0,
        "--claude-temperature",
        help="Sampling temperature for Claude responses.",
    ),
    claude_max_output_tokens: Optional[int] = typer.Option(
        None,
        "--claude-max-output-tokens",
        help="Maximum output tokens for Claude responses.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent identifier passed to setup scripts.",
    ),
    skip_scripts: bool = typer.Option(
        False,
        "--skip-scripts",
        help="Skip running shell setup scripts before invoking the workflow.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        is_flag=True,
        help="Emit JSON output instead of pretty printing.",
    ),
) -> None:
    """Run the Spec Kit specification workflow."""

    model_factory, prebuilt_model = _resolve_model_selection(
        model_factory, claude_model, claude_temperature, claude_max_output_tokens
    )

    _common_options(
        _normalise_arguments(arguments),
        workflow_cls=SpecifyWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        json_output=json_output,
        prebuilt_model=prebuilt_model,
    )


@app.command()
def plan(
    arguments: Optional[List[str]] = typer.Argument(
        None, help="Context passed to /speckit.plan."
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        dir_okay=True,
        file_okay=False,
        help="Repository root containing the Spec Kit project (defaults to current working directory).",
    ),
    model_factory: Optional[str] = typer.Option(
        None,
        "--model-factory",
        "-m",
        help="Python callable returning a LangChain Runnable (module:callable).",
    ),
    claude_model: Optional[str] = typer.Option(
        None,
        "--claude-model",
        help="Anthropic Claude model name (requires ANTHROPIC_API_KEY).",
    ),
    claude_temperature: float = typer.Option(
        0.0,
        "--claude-temperature",
        help="Sampling temperature for Claude responses.",
    ),
    claude_max_output_tokens: Optional[int] = typer.Option(
        None,
        "--claude-max-output-tokens",
        help="Maximum output tokens for Claude responses.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent identifier passed to setup scripts.",
    ),
    skip_scripts: bool = typer.Option(
        False,
        "--skip-scripts",
        help="Skip running shell setup scripts before invoking the workflow.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        is_flag=True,
        help="Emit JSON output instead of pretty printing.",
    ),
) -> None:
    """Run the implementation planning workflow."""

    model_factory, prebuilt_model = _resolve_model_selection(
        model_factory, claude_model, claude_temperature, claude_max_output_tokens
    )

    _common_options(
        _normalise_arguments(arguments),
        workflow_cls=PlanWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        json_output=json_output,
        prebuilt_model=prebuilt_model,
    )


@app.command()
def tasks(
    arguments: Optional[List[str]] = typer.Argument(
        None, help="Optional instructions appended to /speckit.tasks."
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        dir_okay=True,
        file_okay=False,
        help="Repository root containing the Spec Kit project (defaults to current working directory).",
    ),
    model_factory: Optional[str] = typer.Option(
        None,
        "--model-factory",
        "-m",
        help="Python callable returning a LangChain Runnable (module:callable).",
    ),
    claude_model: Optional[str] = typer.Option(
        None,
        "--claude-model",
        help="Anthropic Claude model name (requires ANTHROPIC_API_KEY).",
    ),
    claude_temperature: float = typer.Option(
        0.0,
        "--claude-temperature",
        help="Sampling temperature for Claude responses.",
    ),
    claude_max_output_tokens: Optional[int] = typer.Option(
        None,
        "--claude-max-output-tokens",
        help="Maximum output tokens for Claude responses.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent identifier passed to setup scripts.",
    ),
    skip_scripts: bool = typer.Option(
        False,
        "--skip-scripts",
        help="Skip running shell setup scripts before invoking the workflow.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        is_flag=True,
        help="Emit JSON output instead of pretty printing.",
    ),
) -> None:
    """Generate actionable tasks for the current feature."""

    model_factory, prebuilt_model = _resolve_model_selection(
        model_factory, claude_model, claude_temperature, claude_max_output_tokens
    )

    _common_options(
        _normalise_arguments(arguments),
        workflow_cls=TasksWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        json_output=json_output,
        prebuilt_model=prebuilt_model,
    )


@app.command()
def clarify(
    arguments: Optional[List[str]] = typer.Argument(
        None, help="Optional clarification guidance."
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        dir_okay=True,
        file_okay=False,
        help="Repository root containing the Spec Kit project (defaults to current working directory).",
    ),
    model_factory: Optional[str] = typer.Option(
        None,
        "--model-factory",
        "-m",
        help="Python callable returning a LangChain Runnable (module:callable).",
    ),
    claude_model: Optional[str] = typer.Option(
        None,
        "--claude-model",
        help="Anthropic Claude model name (requires ANTHROPIC_API_KEY).",
    ),
    claude_temperature: float = typer.Option(
        0.0,
        "--claude-temperature",
        help="Sampling temperature for Claude responses.",
    ),
    claude_max_output_tokens: Optional[int] = typer.Option(
        None,
        "--claude-max-output-tokens",
        help="Maximum output tokens for Claude responses.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent identifier passed to setup scripts.",
    ),
    skip_scripts: bool = typer.Option(
        False,
        "--skip-scripts",
        help="Skip running shell setup scripts before invoking the workflow.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        is_flag=True,
        help="Emit JSON output instead of pretty printing.",
    ),
) -> None:
    """Identify and resolve spec ambiguities."""

    model_factory, prebuilt_model = _resolve_model_selection(
        model_factory, claude_model, claude_temperature, claude_max_output_tokens
    )

    _common_options(
        _normalise_arguments(arguments),
        workflow_cls=ClarifyWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        json_output=json_output,
        prebuilt_model=prebuilt_model,
    )


@app.command()
def implement(
    arguments: Optional[List[str]] = typer.Argument(
        None, help="Optional execution notes for /speckit.implement."
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        dir_okay=True,
        file_okay=False,
        help="Repository root containing the Spec Kit project (defaults to current working directory).",
    ),
    model_factory: Optional[str] = typer.Option(
        None,
        "--model-factory",
        "-m",
        help="Python callable returning a LangChain Runnable (module:callable).",
    ),
    claude_model: Optional[str] = typer.Option(
        None,
        "--claude-model",
        help="Anthropic Claude model name (requires ANTHROPIC_API_KEY).",
    ),
    claude_temperature: float = typer.Option(
        0.0,
        "--claude-temperature",
        help="Sampling temperature for Claude responses.",
    ),
    claude_max_output_tokens: Optional[int] = typer.Option(
        None,
        "--claude-max-output-tokens",
        help="Maximum output tokens for Claude responses.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent identifier passed to setup scripts.",
    ),
    skip_scripts: bool = typer.Option(
        False,
        "--skip-scripts",
        help="Skip running shell setup scripts before invoking the workflow.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        is_flag=True,
        help="Emit JSON output instead of pretty printing.",
    ),
) -> None:
    """Execute implementation tasks using the LangGraph workflow."""

    model_factory, prebuilt_model = _resolve_model_selection(
        model_factory, claude_model, claude_temperature, claude_max_output_tokens
    )

    _common_options(
        _normalise_arguments(arguments),
        workflow_cls=ImplementWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        json_output=json_output,
        prebuilt_model=prebuilt_model,
    )


@app.command()
def analyze(
    arguments: Optional[List[str]] = typer.Argument(
        None, help="Optional instructions passed to /speckit.analyze."
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        dir_okay=True,
        file_okay=False,
        help="Repository root containing the Spec Kit project (defaults to current working directory).",
    ),
    model_factory: Optional[str] = typer.Option(
        None,
        "--model-factory",
        "-m",
        help="Python callable returning a LangChain Runnable (module:callable).",
    ),
    claude_model: Optional[str] = typer.Option(
        None,
        "--claude-model",
        help="Anthropic Claude model name (requires ANTHROPIC_API_KEY).",
    ),
    claude_temperature: float = typer.Option(
        0.0,
        "--claude-temperature",
        help="Sampling temperature for Claude responses.",
    ),
    claude_max_output_tokens: Optional[int] = typer.Option(
        None,
        "--claude-max-output-tokens",
        help="Maximum output tokens for Claude responses.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent identifier passed to setup scripts.",
    ),
    skip_scripts: bool = typer.Option(
        False,
        "--skip-scripts",
        help="Skip running shell setup scripts before invoking the workflow.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        is_flag=True,
        help="Emit JSON output instead of pretty printing.",
    ),
) -> None:
    """Run the cross-artifact analysis workflow."""

    model_factory, prebuilt_model = _resolve_model_selection(
        model_factory, claude_model, claude_temperature, claude_max_output_tokens
    )

    _common_options(
        _normalise_arguments(arguments),
        workflow_cls=AnalyzeWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        json_output=json_output,
        prebuilt_model=prebuilt_model,
    )


@app.command()
def checklist(
    arguments: Optional[List[str]] = typer.Argument(
        None, help="Checklist focus instructions."
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        dir_okay=True,
        file_okay=False,
        help="Repository root containing the Spec Kit project (defaults to current working directory).",
    ),
    model_factory: Optional[str] = typer.Option(
        None,
        "--model-factory",
        "-m",
        help="Python callable returning a LangChain Runnable (module:callable).",
    ),
    claude_model: Optional[str] = typer.Option(
        None,
        "--claude-model",
        help="Anthropic Claude model name (requires ANTHROPIC_API_KEY).",
    ),
    claude_temperature: float = typer.Option(
        0.0,
        "--claude-temperature",
        help="Sampling temperature for Claude responses.",
    ),
    claude_max_output_tokens: Optional[int] = typer.Option(
        None,
        "--claude-max-output-tokens",
        help="Maximum output tokens for Claude responses.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent identifier passed to setup scripts.",
    ),
    skip_scripts: bool = typer.Option(
        False,
        "--skip-scripts",
        help="Skip running shell setup scripts before invoking the workflow.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        is_flag=True,
        help="Emit JSON output instead of pretty printing.",
    ),
) -> None:
    """Generate requirements quality checklists."""

    model_factory, prebuilt_model = _resolve_model_selection(
        model_factory, claude_model, claude_temperature, claude_max_output_tokens
    )

    _common_options(
        _normalise_arguments(arguments),
        workflow_cls=ChecklistWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        json_output=json_output,
        prebuilt_model=prebuilt_model,
    )


@app.command()
def constitution(
    arguments: Optional[List[str]] = typer.Argument(
        None, help="Directions for updating the constitution."
    ),
    repo_root: Optional[Path] = typer.Option(
        None,
        "--repo-root",
        dir_okay=True,
        file_okay=False,
        help="Repository root containing the Spec Kit project (defaults to current working directory).",
    ),
    model_factory: Optional[str] = typer.Option(
        None,
        "--model-factory",
        "-m",
        help="Python callable returning a LangChain Runnable (module:callable).",
    ),
    claude_model: Optional[str] = typer.Option(
        None,
        "--claude-model",
        help="Anthropic Claude model name (requires ANTHROPIC_API_KEY).",
    ),
    claude_temperature: float = typer.Option(
        0.0,
        "--claude-temperature",
        help="Sampling temperature for Claude responses.",
    ),
    claude_max_output_tokens: Optional[int] = typer.Option(
        None,
        "--claude-max-output-tokens",
        help="Maximum output tokens for Claude responses.",
    ),
    agent: Optional[str] = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent identifier passed to setup scripts.",
    ),
    skip_scripts: bool = typer.Option(
        False,
        "--skip-scripts",
        help="Skip running shell setup scripts before invoking the workflow.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        is_flag=True,
        help="Emit JSON output instead of pretty printing.",
    ),
) -> None:
    """Manage the project constitution through LangGraph."""

    model_factory, prebuilt_model = _resolve_model_selection(
        model_factory, claude_model, claude_temperature, claude_max_output_tokens
    )

    _common_options(
        _normalise_arguments(arguments),
        workflow_cls=ConstitutionWorkflow,
        repo_root=_resolve_repo_root(repo_root),
        model_factory=model_factory,
        agent=agent,
        skip_scripts=skip_scripts,
        json_output=json_output,
        prebuilt_model=prebuilt_model,
    )
