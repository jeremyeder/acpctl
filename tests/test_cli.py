"""CLI smoke tests for acpctl."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from acpctl.cli import app
from langchain_core.runnables import RunnableLambda


class AcpctlCliTests(unittest.TestCase):
    """Basic CLI coverage to ensure command wiring functions."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.runner = CliRunner()

    def test_specify_with_model_factory(self) -> None:
        command = [
            "specify",
            "--repo-root",
            str(self.repo_root),
            "--model-factory",
            "tests.test_cli:make_test_model",
            "--skip-scripts",
            "-j",
            "Draft",
            "the",
            "spec",
        ]

        # Set template dir to examples
        with patch.dict(os.environ, {"ACPCTL_TEMPLATE_DIR": str(self.repo_root / "examples" / "templates")}):
            result = self.runner.invoke(app, command)

        self.assertEqual(result.exit_code, 0, msg=result.output)

        payload = json.loads(result.stdout)
        self.assertGreaterEqual(payload["response"]["messages_count"], 1)

    def test_specify_with_claude_shortcut(self) -> None:
        command = [
            "specify",
            "--repo-root",
            str(self.repo_root),
            "--claude-model",
            "claude-3-opus-20240229",
            "--skip-scripts",
            "-j",
            "Draft",
            "the",
            "spec",
        ]

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key", "ACPCTL_TEMPLATE_DIR": str(self.repo_root / "examples" / "templates")}):
            with patch("acpctl.cli._build_claude_model", return_value=RunnableLambda(lambda messages: {"messages_count": len(messages)})):
                result = self.runner.invoke(app, command)

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.stdout)
        self.assertGreaterEqual(payload["response"]["messages_count"], 1)

    def test_plan_command(self) -> None:
        command = [
            "plan",
            "--repo-root",
            str(self.repo_root),
            "--model-factory",
            "tests.test_cli:make_test_model",
            "--skip-scripts",
            "-j",
            "Plan",
            "implementation",
        ]

        with patch.dict(os.environ, {"ACPCTL_TEMPLATE_DIR": str(self.repo_root / "examples" / "templates")}):
            result = self.runner.invoke(app, command)

        self.assertEqual(result.exit_code, 0, msg=result.output)

    def test_tasks_command(self) -> None:
        command = [
            "tasks",
            "--repo-root",
            str(self.repo_root),
            "--model-factory",
            "tests.test_cli:make_test_model",
            "--skip-scripts",
            "-j",
            "Generate",
            "tasks",
        ]

        with patch.dict(os.environ, {"ACPCTL_TEMPLATE_DIR": str(self.repo_root / "examples" / "templates")}):
            result = self.runner.invoke(app, command)

        self.assertEqual(result.exit_code, 0, msg=result.output)


def make_test_model() -> RunnableLambda:
    return RunnableLambda(lambda messages: {"messages_count": len(messages)})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
