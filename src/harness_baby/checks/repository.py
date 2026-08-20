"""Repository-level metadata and agent context checks."""

from __future__ import annotations

from harness_baby.checks.base import Check
from harness_baby.models import CheckResult, ScanContext, Status


class RepositoryCheck(Check):
    id = "repository"
    category = "repository"

    def run(self, context: ScanContext) -> CheckResult:
        git_marker = context.root / ".git"
        is_git = git_marker.is_dir() or git_marker.is_file()
        license_files = sorted(
            path.name for path in context.root.iterdir() if path.name.lower().startswith("license")
        )
        evidence = {
            "git_repository": is_git,
            "license": license_files[0] if license_files else None,
        }
        status = Status.PASS if is_git else Status.FAIL
        if not is_git:
            evidence["reason"] = "No .git repository marker detected"
        return CheckResult(self.id, self.category, status, evidence)


class DocumentationCheck(Check):
    id = "documentation"
    category = "documentation"

    def run(self, context: ScanContext) -> CheckResult:
        readmes = sorted(
            path.name for path in context.root.iterdir() if path.name.lower().startswith("readme")
        )
        evidence = {"readme": readmes[0] if readmes else None}
        if readmes:
            return CheckResult(self.id, self.category, Status.PASS, evidence)
        evidence["reason"] = "No root README detected"
        return CheckResult(self.id, self.category, Status.WARN, evidence)


class AgentContextCheck(Check):
    id = "agent_context"
    category = "agent_context"

    def run(self, context: ScanContext) -> CheckResult:
        agents = context.root / "AGENTS.md"
        evidence = {
            "agents_md": agents.is_file(),
            "path": "AGENTS.md" if agents.is_file() else None,
        }
        if agents.is_file():
            return CheckResult(self.id, self.category, Status.PASS, evidence)
        evidence["reason"] = "No root AGENTS.md detected"
        return CheckResult(self.id, self.category, Status.WARN, evidence)
