"""Static GitHub Actions CI and secret checks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from harness_doctor.checks.base import Check
from harness_doctor.checks.helpers import read_text
from harness_doctor.models import CheckResult, ScanContext, Status

TEST_PATTERN = re.compile(r"\b(pytest|python\s+-m\s+unittest|unittest)\b", re.IGNORECASE)
LINT_PATTERN = re.compile(r"\b(ruff|flake8|pylint|mypy|tflint)\b", re.IGNORECASE)
TF_VALIDATE_PATTERN = re.compile(r"\bterraform\s+validate\b", re.IGNORECASE)
ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|access[_-]?key)\b\s*[:=]\s*['\"]?([^\s'\"#]+)"
)
TOKEN_PATTERNS = {
    "github_token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def _workflow_paths(context: ScanContext) -> list[Path]:
    workflow_root = context.root / ".github" / "workflows"
    return sorted(
        (
            path
            for path in context.files
            if path.parent == workflow_root and path.suffix.lower() in {".yml", ".yaml"}
        ),
        key=lambda path: path.as_posix(),
    )


def _parse_errors(paths: list[Path], context: ScanContext) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for path in paths:
        try:
            parsed = yaml.safe_load(read_text(path))
            if parsed is not None and not isinstance(parsed, dict):
                errors.append(
                    {"file": context.relative(path), "error": "Workflow root is not a mapping"}
                )
        except yaml.YAMLError as error:
            errors.append({"file": context.relative(path), "error": type(error).__name__})
    return errors


def _secret_findings(paths: list[Path], context: ScanContext) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            if "${{" in line and ("secrets." in line or "github.token" in line):
                continue
            assignment = ASSIGNMENT_PATTERN.search(line)
            if assignment:
                value = assignment.group(2)
                if value not in {"", "null", "none", "~", "|", ">"} and not value.startswith("$"):
                    findings.append(
                        {
                            "file": context.relative(path),
                            "line": line_number,
                            "kind": "sensitive_assignment",
                        }
                    )
                    continue
            for kind, pattern in TOKEN_PATTERNS.items():
                if pattern.search(line):
                    findings.append(
                        {"file": context.relative(path), "line": line_number, "kind": kind}
                    )
                    break
    return findings


class GitHubActionsCheck(Check):
    id = "ci"
    category = "ci"

    def run(self, context: ScanContext) -> CheckResult:
        paths = _workflow_paths(context)
        workflows = [context.relative(path) for path in paths]
        combined = "\n".join(read_text(path) for path in paths)
        evidence: dict[str, Any] = {
            "github_actions": bool(paths),
            "workflows": workflows,
            "test_step": bool(TEST_PATTERN.search(combined)),
            "lint_step": bool(LINT_PATTERN.search(combined)),
            "terraform_validate_step": bool(TF_VALIDATE_PATTERN.search(combined)),
            "parse_errors": _parse_errors(paths, context),
        }
        if not paths:
            evidence["reason"] = "No GitHub Actions workflow detected"
            return CheckResult(self.id, self.category, Status.WARN, evidence)
        if evidence["parse_errors"]:
            evidence["reason"] = "One or more workflow files could not be parsed"
            return CheckResult(self.id, self.category, Status.FAIL, evidence)

        required_steps = [evidence["test_step"], evidence["lint_step"]]
        if "terraform" in context.detected_stacks:
            required_steps.append(evidence["terraform_validate_step"])
        if all(required_steps):
            return CheckResult(self.id, self.category, Status.PASS, evidence)
        evidence["reason"] = (
            "Workflow exists but one or more relevant test, lint, or validate steps are missing"
        )
        return CheckResult(self.id, self.category, Status.WARN, evidence)


class SecurityCheck(Check):
    id = "security"
    category = "security"

    def run(self, context: ScanContext) -> CheckResult:
        paths = _workflow_paths(context)
        if not paths:
            return CheckResult(
                self.id,
                self.category,
                Status.SKIP,
                {"reason": "No GitHub Actions workflow detected"},
            )
        findings = _secret_findings(paths, context)
        evidence: dict[str, Any] = {
            "files_scanned": [context.relative(path) for path in paths],
            "potential_hardcoded_secrets": findings,
            "secret_values_included": False,
        }
        if findings:
            evidence["reason"] = (
                "Potential hardcoded secret assignments detected; values were redacted"
            )
            return CheckResult(self.id, self.category, Status.FAIL, evidence)
        return CheckResult(self.id, self.category, Status.PASS, evidence)
