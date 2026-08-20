"""Built-in check registry."""

from __future__ import annotations

from harness_doctor.checks.base import Check
from harness_doctor.checks.github_actions import GitHubActionsCheck, SecurityCheck
from harness_doctor.checks.python import (
    FormattingCheck,
    LintingCheck,
    PythonTestingCheck,
    ReproducibilityCheck,
)
from harness_doctor.checks.repository import AgentContextCheck, DocumentationCheck, RepositoryCheck
from harness_doctor.checks.terraform import TerraformValidationCheck


def built_in_checks() -> tuple[Check, ...]:
    """Return checks in stable report and console order."""
    return (
        RepositoryCheck(),
        DocumentationCheck(),
        AgentContextCheck(),
        PythonTestingCheck(),
        LintingCheck(),
        FormattingCheck(),
        TerraformValidationCheck(),
        GitHubActionsCheck(),
        SecurityCheck(),
        ReproducibilityCheck(),
    )
