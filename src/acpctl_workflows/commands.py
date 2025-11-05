"""Command-specific LangGraph workflow implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .workflow import SlashCommandWorkflow

MAX_FILE_CHARS = 24_000


def _read_text(path: Path, *, limit: int = MAX_FILE_CHARS) -> Optional[str]:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) > limit:
        truncated = text[:limit]
        suffix = f"\n\n… [truncated {len(text) - limit} characters]"
        return truncated + suffix
    return text


def _collect_files(base: Path, names: Iterable[str]) -> Dict[str, str]:
    collected: Dict[str, str] = {}
    for name in names:
        path = base / name
        if path.is_dir():
            collected[name] = _summarise_directory(path)
        else:
            content = _read_text(path)
            if content is not None:
                collected[name] = content
    return collected


def _summarise_directory(directory: Path, *, limit: int = 25) -> str:
    entries: List[str] = []
    if not directory.exists():
        return "<missing>"
    for item in sorted(directory.iterdir()):
        rel = item.name + ("/" if item.is_dir() else "")
        entries.append(rel)
        if len(entries) >= limit:
            break
    summary = "\n".join(entries)
    if len(list(directory.iterdir())) > limit:
        summary += "\n…"
    return summary


def _gather_command_templates(base_dir: Path) -> Dict[str, str]:
    templates_dir = base_dir / "templates" / "commands"
    mapping: Dict[str, str] = {}
    if not templates_dir.is_dir():
        return mapping
    for path in sorted(templates_dir.glob("*.md")):
        content = _read_text(path, limit=12_000)
        if content is not None:
            mapping[path.name] = content
    return mapping


class ConstitutionWorkflow(SlashCommandWorkflow):
    """Workflow for `/speckit.constitution`."""

    command_name = "constitution"

    def prepare_context(self, state):  # type: ignore[override]
        repo = self.repo_root
        constitution_path = repo / "memory" / "constitution.md"
        context: Dict[str, Any] = {
            "constitution_path": str(constitution_path),
        }

        constitution_text = _read_text(constitution_path)
        if constitution_text is not None:
            context["constitution"] = constitution_text

        templates_dir = repo / "templates"
        context["dependent_templates"] = {
            "spec": _read_text(templates_dir / "spec-template.md"),
            "plan": _read_text(templates_dir / "plan-template.md"),
            "tasks": _read_text(templates_dir / "tasks-template.md"),
        }

        context["command_templates"] = _gather_command_templates(repo)
        readme = _read_text(repo / "README.md", limit=10_000)
        if readme is not None:
            context["readme"] = readme

        docs_dir = repo / "docs"
        if docs_dir.is_dir():
            index = _read_text(docs_dir / "index.md", limit=8_000)
            if index is not None:
                context.setdefault("docs", {})["index.md"] = index

        return context


class SpecifyWorkflow(SlashCommandWorkflow):
    """Workflow for `/speckit.specify`."""

    command_name = "specify"

    def prepare_context(self, state):  # type: ignore[override]
        context: Dict[str, Any] = {}
        script = state.get("script_result")
        if script and script.data:
            context["setup"] = script.data
            spec_file = script.data.get("SPEC_FILE")
            if spec_file:
                content = _read_text(Path(spec_file))
                if content is not None:
                    context["spec_template"] = content

        constitution = _read_text(self.repo_root / "memory" / "constitution.md")
        if constitution is not None:
            context["constitution"] = constitution

        return context


class PlanWorkflow(SlashCommandWorkflow):
    """Workflow for `/speckit.plan`."""

    command_name = "plan"

    def prepare_context(self, state):  # type: ignore[override]
        context: Dict[str, Any] = {}
        script = state.get("script_result")
        if script and script.data:
            data = script.data
            context["setup"] = data
            spec_path = data.get("FEATURE_SPEC")
            if spec_path:
                spec_text = _read_text(Path(spec_path))
                if spec_text is not None:
                    context["spec"] = spec_text
            plan_path = data.get("IMPL_PLAN")
            if plan_path:
                plan_text = _read_text(Path(plan_path))
                if plan_text is not None:
                    context["plan_template"] = plan_text

        constitution = _read_text(self.repo_root / "memory" / "constitution.md")
        if constitution is not None:
            context["constitution"] = constitution

        return context


class ClarifyWorkflow(SlashCommandWorkflow):
    """Workflow for `/speckit.clarify`."""

    command_name = "clarify"

    def prepare_context(self, state):  # type: ignore[override]
        context: Dict[str, Any] = {}
        script = state.get("script_result")
        if script and script.data:
            data = script.data
            context["paths"] = data
            spec_path = data.get("FEATURE_SPEC")
            if spec_path:
                spec_text = _read_text(Path(spec_path))
                if spec_text is not None:
                    context["spec"] = spec_text
        return context


class TasksWorkflow(SlashCommandWorkflow):
    """Workflow for `/speckit.tasks`."""

    command_name = "tasks"

    def prepare_context(self, state):  # type: ignore[override]
        context: Dict[str, Any] = {}
        script = state.get("script_result")
        if script and script.data:
            data = script.data
            feature_dir = Path(data["FEATURE_DIR"])
            context["setup"] = data

            doc_names = set(data.get("AVAILABLE_DOCS", []))
            doc_names.update(["plan.md", "spec.md"])
            context["documents"] = _collect_files(feature_dir, doc_names)

        return context


class ImplementWorkflow(SlashCommandWorkflow):
    """Workflow for `/speckit.implement`."""

    command_name = "implement"

    def prepare_context(self, state):  # type: ignore[override]
        context: Dict[str, Any] = {}
        script = state.get("script_result")
        if script and script.data:
            data = script.data
            feature_dir = Path(data["FEATURE_DIR"])
            context["setup"] = data

            doc_names = set(data.get("AVAILABLE_DOCS", []))
            doc_names.update(["plan.md", "tasks.md"])
            context["documents"] = _collect_files(feature_dir, doc_names)

            checklist_dir = feature_dir / "checklists"
            if checklist_dir.is_dir():
                context["checklists"] = _collect_files(checklist_dir, [p.name for p in checklist_dir.glob("*.md")])

        return context


class AnalyzeWorkflow(SlashCommandWorkflow):
    """Workflow for `/speckit.analyze`."""

    command_name = "analyze"

    def prepare_context(self, state):  # type: ignore[override]
        context: Dict[str, Any] = {}
        script = state.get("script_result")
        if script and script.data:
            data = script.data
            feature_dir = Path(data["FEATURE_DIR"])
            context["setup"] = data

            doc_names = set(data.get("AVAILABLE_DOCS", []))
            doc_names.update(["plan.md", "spec.md", "tasks.md"])
            context["documents"] = _collect_files(feature_dir, doc_names)

        constitution = _read_text(self.repo_root / "memory" / "constitution.md")
        if constitution is not None:
            context["constitution"] = constitution

        return context


class ChecklistWorkflow(SlashCommandWorkflow):
    """Workflow for `/speckit.checklist`."""

    command_name = "checklist"

    def prepare_context(self, state):  # type: ignore[override]
        context: Dict[str, Any] = {}
        script = state.get("script_result")
        if script and script.data:
            data = script.data
            feature_dir = Path(data["FEATURE_DIR"])
            context["setup"] = data

            doc_names = set(data.get("AVAILABLE_DOCS", []))
            doc_names.update(["plan.md", "spec.md"])
            context["documents"] = _collect_files(feature_dir, doc_names)

        return context
