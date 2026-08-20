"""Python testing, linting, formatting, and reproducibility checks."""

from __future__ import annotations

from typing import Any

from harness_baby.checks.base import Check
from harness_baby.checks.helpers import (
    config_has_section,
    load_toml,
    nested_mapping,
    project_dependency_names,
    read_text,
    requirement_names,
)
from harness_baby.models import CheckResult, ScanContext, Status


def _python_metadata(context: ScanContext) -> dict[str, Any]:
    pyproject_path = context.root / "pyproject.toml"
    pyproject, parse_error = load_toml(pyproject_path)
    dependencies = project_dependency_names(pyproject)
    requirements = context.root / "requirements.txt"
    if requirements.is_file():
        dependencies.update(requirement_names(requirements))
    return {
        "pyproject": pyproject,
        "pyproject_error": parse_error,
        "dependencies": dependencies,
    }


def _tool_table(metadata: dict[str, Any], name: str) -> bool:
    tools = nested_mapping(metadata["pyproject"], "tool")
    return name in tools and isinstance(tools[name], dict)


class PythonTestingCheck(Check):
    id = "testing"
    category = "testing"

    def run(self, context: ScanContext) -> CheckResult:
        if "python" not in context.detected_stacks:
            return CheckResult(
                self.id,
                self.category,
                Status.SKIP,
                {"reason": "Python stack not detected"},
            )

        metadata = _python_metadata(context)
        test_files = sorted(
            context.relative(path)
            for path in context.paths_with_suffix(".py")
            if path.name.startswith("test_") or path.name.endswith("_test.py")
        )
        texts = [read_text(context.root / filename) for filename in test_files]
        pytest_detected = (
            "pytest" in metadata["dependencies"]
            or _tool_table(metadata, "pytest")
            or (context.root / "pytest.ini").is_file()
            or any("import pytest" in text for text in texts)
        )
        unittest_detected = any(
            "import unittest" in text or "from unittest" in text for text in texts
        )
        root = context.root
        pyproject_text = read_text(root / "pyproject.toml")
        coverage_configs = [
            name
            for name, detected in (
                ("pyproject.toml", "[tool.coverage." in pyproject_text),
                (".coveragerc", (root / ".coveragerc").is_file()),
                ("setup.cfg", config_has_section(root / "setup.cfg", "coverage")),
                ("tox.ini", config_has_section(root / "tox.ini", "coverage")),
            )
            if detected
        ]
        pytest_options = nested_mapping(metadata["pyproject"], "tool", "pytest", "ini_options")
        addopts = pytest_options.get("addopts", "")
        if "--cov" in str(addopts):
            coverage_configs.append("pytest --cov")
        frameworks = [
            name
            for name, detected in (("pytest", pytest_detected), ("unittest", unittest_detected))
            if detected
        ]
        evidence: dict[str, Any] = {
            "frameworks": frameworks,
            "test_files": test_files,
            "coverage_config": coverage_configs,
            "pyproject_parse_error": metadata["pyproject_error"],
        }
        if frameworks or test_files:
            return CheckResult(self.id, self.category, Status.PASS, evidence)
        evidence["reason"] = "No supported Python test framework or test files detected"
        return CheckResult(self.id, self.category, Status.FAIL, evidence)


class LintingCheck(Check):
    id = "linting"
    category = "linting"

    def run(self, context: ScanContext) -> CheckResult:
        applicable: list[str] = []
        configured: list[str] = []
        evidence: dict[str, Any] = {}

        if "python" in context.detected_stacks:
            applicable.append("python")
            metadata = _python_metadata(context)
            root = context.root
            ruff = (
                "ruff" in metadata["dependencies"]
                or _tool_table(metadata, "ruff")
                or (root / "ruff.toml").is_file()
                or (root / ".ruff.toml").is_file()
            )
            flake8 = (
                "flake8" in metadata["dependencies"]
                or (root / ".flake8").is_file()
                or config_has_section(root / "setup.cfg", "flake8")
                or config_has_section(root / "tox.ini", "flake8")
            )
            mypy = (
                "mypy" in metadata["dependencies"]
                or _tool_table(metadata, "mypy")
                or (root / "mypy.ini").is_file()
                or (root / ".mypy.ini").is_file()
                or config_has_section(root / "setup.cfg", "mypy")
            )
            tools = [
                name
                for name, found in (("ruff", ruff), ("flake8", flake8), ("mypy", mypy))
                if found
            ]
            evidence["python_tools"] = tools
            if tools:
                configured.append("python")

        if "terraform" in context.detected_stacks:
            applicable.append("terraform")
            configs = sorted(
                context.relative(path) for path in context.paths_named(".tflint.hcl", "tflint.hcl")
            )
            evidence["tflint_config"] = configs
            if configs:
                configured.append("terraform")

        evidence["applicable_stacks"] = applicable
        if not applicable:
            evidence["reason"] = "No supported source stack detected"
            return CheckResult(self.id, self.category, Status.SKIP, evidence)
        if len(configured) == len(applicable):
            return CheckResult(self.id, self.category, Status.PASS, evidence)
        if configured:
            evidence["reason"] = "Lint configuration is missing for one or more detected stacks"
            return CheckResult(self.id, self.category, Status.WARN, evidence)
        evidence["reason"] = "No supported lint configuration detected"
        return CheckResult(self.id, self.category, Status.FAIL, evidence)


class FormattingCheck(Check):
    id = "formatting"
    category = "formatting"

    def run(self, context: ScanContext) -> CheckResult:
        applicable: list[str] = []
        configured: list[str] = []
        evidence: dict[str, Any] = {}
        if "python" in context.detected_stacks:
            applicable.append("python")
            metadata = _python_metadata(context)
            black = "black" in metadata["dependencies"] or _tool_table(metadata, "black")
            ruff = nested_mapping(metadata["pyproject"], "tool", "ruff")
            ruff_format = "format" in ruff and isinstance(ruff["format"], dict)
            tools = [
                name for name, found in (("black", black), ("ruff-format", ruff_format)) if found
            ]
            evidence["python_formatters"] = tools
            if tools:
                configured.append("python")
        if "terraform" in context.detected_stacks:
            applicable.append("terraform")
            configured.append("terraform")
            evidence["terraform_fmt_applicable"] = True

        evidence["applicable_stacks"] = applicable
        if not applicable:
            evidence["reason"] = "No supported source stack detected"
            return CheckResult(self.id, self.category, Status.SKIP, evidence)
        if len(configured) == len(applicable):
            return CheckResult(self.id, self.category, Status.PASS, evidence)
        if configured:
            evidence["reason"] = (
                "Formatter configuration is missing for one or more detected stacks"
            )
            return CheckResult(self.id, self.category, Status.WARN, evidence)
        evidence["reason"] = "No supported formatter configuration detected"
        return CheckResult(self.id, self.category, Status.FAIL, evidence)


class ReproducibilityCheck(Check):
    id = "reproducibility"
    category = "reproducibility"

    def run(self, context: ScanContext) -> CheckResult:
        applicable: list[str] = []
        reproducible: list[str] = []
        evidence: dict[str, Any] = {}
        if "python" in context.detected_stacks:
            applicable.append("python")
            lock_names = ("uv.lock", "poetry.lock", "Pipfile.lock", "pdm.lock")
            locks = [name for name in lock_names if (context.root / name).is_file()]
            requirements = context.root / "requirements.txt"
            pinned_requirements = False
            if requirements.is_file():
                entries = [
                    line.strip()
                    for line in read_text(requirements).splitlines()
                    if line.strip() and not line.lstrip().startswith(("#", "-"))
                ]
                pinned_requirements = bool(entries) and all("==" in line for line in entries)
            evidence["python_lockfiles"] = locks
            evidence["requirements_fully_pinned"] = pinned_requirements
            if locks or pinned_requirements:
                reproducible.append("python")
        if "terraform" in context.detected_stacks:
            applicable.append("terraform")
            locks = sorted(
                context.relative(path) for path in context.paths_named(".terraform.lock.hcl")
            )
            evidence["terraform_lockfiles"] = locks
            if locks:
                reproducible.append("terraform")

        evidence["applicable_stacks"] = applicable
        if not applicable:
            evidence["reason"] = "No supported dependency-bearing stack detected"
            return CheckResult(self.id, self.category, Status.SKIP, evidence)
        if len(reproducible) == len(applicable):
            return CheckResult(self.id, self.category, Status.PASS, evidence)
        evidence["reason"] = (
            "One or more detected stacks lack a lockfile or fully pinned requirements"
        )
        status = Status.WARN if reproducible else Status.FAIL
        return CheckResult(self.id, self.category, status, evidence)
